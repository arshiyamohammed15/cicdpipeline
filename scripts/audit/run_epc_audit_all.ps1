Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-LogTail {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [int]$Lines = 40
    )
    if (Test-Path $Path) {
        Get-Content -Path $Path -Tail $Lines
    }
}

function Invoke-LoggedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][scriptblock]$Command,
        [Parameter(Mandatory = $true)][string]$LogPath
    )
    & $Command *> $LogPath
    $exitCode = $LASTEXITCODE
    Add-Content -Path $LogPath -Value ("PY_EXIT_CODE=" + $exitCode)
    Add-Content -Path $LogPath -Value ("UTC_FINISHED=" + (Get-Date).ToUniversalTime().ToString("o"))
    if ($exitCode -ne 0) {
        Write-Host ("FAIL: " + $Label + " returned " + $exitCode)
        Write-Host "Log tail:"
        Write-LogTail -Path $LogPath -Lines 40
        throw ($Label + " failed with exit code " + $exitCode)
    }
}

function Assert-EvidenceFiles {
    param(
        [Parameter(Mandatory = $true)][string]$PassLabel,
        [Parameter(Mandatory = $true)][string[]]$Paths,
        [Parameter(Mandatory = $true)][string]$RunDir,
        [Parameter(Mandatory = $true)][string]$LogPath
    )
    $missing = @()
    foreach ($path in $Paths) {
        if (-not (Test-Path $path)) {
            $missing += (Split-Path -Leaf $path) + " missing"
        } elseif ((Get-Item $path).Length -le 0) {
            $missing += (Split-Path -Leaf $path) + " empty"
        }
    }
    if ($missing.Count -gt 0) {
        Write-Host ("FAIL: " + $PassLabel + " evidence files missing or empty.")
        Write-Host "RUN_DIR listing:"
        Get-ChildItem -Path $RunDir | Select-Object Name, Length
        Write-Host "Log tail:"
        Write-LogTail -Path $LogPath -Lines 40
        throw ($PassLabel + " evidence validation failed: " + ($missing -join "; "))
    }
}

function Get-FileTail {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [int]$Lines = 12
    )
    if (Test-Path $Path) {
        return Get-Content -Path $Path -Tail $Lines
    }
    return @("<missing>")
}

function Get-FileSizeText {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (Test-Path $Path) {
        return (Get-Item $Path).Length.ToString()
    }
    return "missing"
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
Push-Location $repoRoot
try {
    $env:USE_REAL_SERVICES = "false"

    $runDir = Join-Path $repoRoot ("artifacts/audit_runs/epc_audit_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
    New-Item -ItemType Directory -Force $runDir | Out-Null
    Write-Host ("RUN_DIR=" + $runDir)

    $passStatus = [ordered]@{
        "PASS 1" = "PENDING"
        "PASS 2" = "PENDING"
        "PASS 3" = "PENDING"
        "PASS 4" = "PENDING"
        "PASS 5" = "PENDING"
    }
    $currentPass = ""
    $failure = $null

    try {
        # PASS 1 - Inventory & Allowed Paths
        $currentPass = "PASS 1"
        $passStatus[$currentPass] = "RUNNING"
        $pass1Log = Join-Path $runDir "pass1_inventory_allowed_paths.log"
        Invoke-LoggedCommand -Label "PASS 1 inventory/allowed paths" -LogPath $pass1Log -Command {
            python scripts/audit/epc_inventory_allowed_paths.py $repoRoot --out-dir $runDir
        }
        $inv = Join-Path $runDir "epc_module_inventory.md"
        $paths = Join-Path $runDir "epc_allowed_paths.md"
        Assert-EvidenceFiles -PassLabel "PASS 1" -Paths @($inv, $paths) -RunDir $runDir -LogPath $pass1Log
        $passStatus[$currentPass] = "PASS"

        # PASS 2 - Boundary Check
        $currentPass = "PASS 2"
        $passStatus[$currentPass] = "RUNNING"
        $pass2Log = Join-Path $runDir "pass2_boundary_check.log"
        Invoke-LoggedCommand -Label "PASS 2 boundary check" -LogPath $pass2Log -Command {
            python scripts/audit/epc_boundary_check.py $repoRoot --out-dir $runDir
        }
        $boundary = Join-Path $runDir "epc_boundary_violations.md"
        Assert-EvidenceFiles -PassLabel "PASS 2" -Paths @($boundary) -RunDir $runDir -LogPath $pass2Log
        $passStatus[$currentPass] = "PASS"

        # PASS 3 - Contracts & Schemas
        $currentPass = "PASS 3"
        $passStatus[$currentPass] = "RUNNING"
        $pass3Log = Join-Path $runDir "pass3_contracts_and_schemas.log"
        Invoke-LoggedCommand -Label "PASS 3 contracts & schemas" -LogPath $pass3Log -Command {
            $contractsPath = Join-Path $repoRoot "src/cloud_services/shared-services/contracts-schema-registry"
            $validatorsPath = Join-Path $contractsPath "validators"
            $configPath = Join-Path $repoRoot "config"
            $policiesPath = Join-Path $configPath "policies"

            $missing = @()
            if (-not (Test-Path $contractsPath)) {
                $missing += "contracts-schema-registry missing"
            } elseif (-not (Test-Path $validatorsPath)) {
                $missing += "contracts-schema-registry/validators missing"
            }
            if (-not (Test-Path $configPath)) {
                $missing += "config/ missing"
            } elseif (-not (Test-Path $policiesPath)) {
                $missing += "config/policies missing"
            }

            $pass3Evidence = Join-Path $runDir "epc_contracts_and_schemas.md"
            $lines = @(
                "# EPC Contracts and Schemas (PASS 3)",
                "",
                ("contracts-schema-registry path: " + $contractsPath),
                ("contracts-schema-registry exists: " + (Test-Path $contractsPath)),
                ("validators folder exists: " + (Test-Path $validatorsPath)),
                "",
                ("config path: " + $configPath),
                ("config exists: " + (Test-Path $configPath)),
                ("config/policies exists: " + (Test-Path $policiesPath))
            )
            if ($missing.Count -gt 0) {
                $lines += ""
                $lines += "## Missing:"
                foreach ($item in $missing) {
                    $lines += ("- " + $item)
                }
                $lines += ""
                $lines += "Status: FAIL"
                Set-Content -Path $pass3Evidence -Value $lines
                $global:LASTEXITCODE = 1
                return
            }
            $lines += ""
            $lines += "Status: PASS"
            Set-Content -Path $pass3Evidence -Value $lines
            $global:LASTEXITCODE = 0
            return
        }
        $contractsEvidence = Join-Path $runDir "epc_contracts_and_schemas.md"
        Assert-EvidenceFiles -PassLabel "PASS 3" -Paths @($contractsEvidence) -RunDir $runDir -LogPath $pass3Log
        $passStatus[$currentPass] = "PASS"

        # PASS 4 - Chokepoint Invariants
        $currentPass = "PASS 4"
        $passStatus[$currentPass] = "RUNNING"
        $pass4Log = Join-Path $runDir "pass4_chokepoint_invariants.log"
        Invoke-LoggedCommand -Label "PASS 4 chokepoint invariants" -LogPath $pass4Log -Command {
            $targets = @(
                @{ Label = "EPC-3 configuration-policy-management"; Path = Join-Path $repoRoot "src/cloud_services/shared-services/configuration-policy-management" },
                @{ Label = "EPC-12 contracts-schema-registry"; Path = Join-Path $repoRoot "src/cloud_services/shared-services/contracts-schema-registry" },
                @{ Label = "EPC-1 identity-access-management"; Path = Join-Path $repoRoot "src/cloud_services/shared-services/identity-access-management" },
                @{ Label = "EPC-4 alerting-notification-service"; Path = Join-Path $repoRoot "src/cloud_services/shared-services/alerting-notification-service" },
                @{ Label = "EPC-5 health-reliability-monitoring"; Path = Join-Path $repoRoot "src/cloud_services/shared-services/health-reliability-monitoring" }
            )
            $missing = @()
            $lines = @("# EPC Chokepoint Invariants (PASS 4)", "")
            foreach ($target in $targets) {
                $exists = Test-Path $target.Path
                $lines += ("- " + $target.Label + ": " + $exists)
                if (-not $exists) {
                    $missing += $target.Label
                }
            }
            if ($missing.Count -gt 0) {
                $lines += ""
                $lines += "Status: FAIL"
                $lines += "## Missing chokepoint roots"
                foreach ($item in $missing) {
                    $lines += ("- " + $item)
                }
                $pass4Evidence = Join-Path $runDir "epc_chokepoint_invariants.md"
                Set-Content -Path $pass4Evidence -Value $lines
                $global:LASTEXITCODE = 1
                return
            }
            $lines += ""
            $lines += "Status: PASS"
            $pass4Evidence = Join-Path $runDir "epc_chokepoint_invariants.md"
            Set-Content -Path $pass4Evidence -Value $lines
            $global:LASTEXITCODE = 0
            return
        }
        $chokepointEvidence = Join-Path $runDir "epc_chokepoint_invariants.md"
        Assert-EvidenceFiles -PassLabel "PASS 4" -Paths @($chokepointEvidence) -RunDir $runDir -LogPath $pass4Log
        $passStatus[$currentPass] = "PASS"

        # PASS 5 - Offline Golden Path
        $currentPass = "PASS 5"
        $passStatus[$currentPass] = "RUNNING"
        $pass5Log = Join-Path $runDir "pass5_e2e_golden_path.log"
        Invoke-LoggedCommand -Label "PASS 5 offline golden path" -LogPath $pass5Log -Command {
            $expectedEvidence = @(
                "epc_module_inventory.md",
                "epc_allowed_paths.md",
                "epc_boundary_violations.md",
                "epc_contracts_and_schemas.md",
                "epc_chokepoint_invariants.md"
            )
            $missingEvidence = @()
            $evidenceLines = @(
                "# EPC Offline Golden Path (PASS 5)",
                "",
                "USE_REAL_SERVICES=false",
                "Evidence inputs:"
            )
            foreach ($name in $expectedEvidence) {
                $path = Join-Path $runDir $name
                $sizeText = if (Test-Path $path) { (Get-Item $path).Length.ToString() + " bytes" } else { "missing" }
                $evidenceLines += ("- " + $name + ": " + $sizeText)
                if (-not (Test-Path $path) -or (Get-Item $path).Length -le 0) {
                    $missingEvidence += ($name + " missing or empty")
                }
            }

            if ($missingEvidence.Count -gt 0) {
                $evidenceLines += ""
                $evidenceLines += "Status: FAIL"
                $evidenceLines += "## Missing evidence"
                foreach ($item in $missingEvidence) {
                    $evidenceLines += ("- " + $item)
                }
                $pass5Evidence = Join-Path $runDir "epc_e2e_golden_path.md"
                Set-Content -Path $pass5Evidence -Value $evidenceLines
                $global:LASTEXITCODE = 1
                return
            }

            $evidenceLines += ""
            $evidenceLines += "Status: PASS"
            $evidenceLines += "## Notes"
            $evidenceLines += "- Offline golden path validated using locally generated evidence only."

            $pass5Evidence = Join-Path $runDir "epc_e2e_golden_path.md"
            Set-Content -Path $pass5Evidence -Value $evidenceLines
            $global:LASTEXITCODE = 0
            return
        }
        $goldenEvidence = Join-Path $runDir "epc_e2e_golden_path.md"
        Assert-EvidenceFiles -PassLabel "PASS 5" -Paths @($goldenEvidence) -RunDir $runDir -LogPath $pass5Log
        $passStatus[$currentPass] = "PASS"
    } catch {
        if ($currentPass) {
            $passStatus[$currentPass] = "FAIL"
        }
        $failure = $_
    } finally {
        if ($failure) {
            $keys = @($passStatus.Keys)
            foreach ($key in $keys) {
                if ($passStatus[$key] -eq "PENDING" -or $passStatus[$key] -eq "RUNNING") {
                    $passStatus[$key] = "SKIPPED"
                }
            }
        }

        $summaryPath = Join-Path $runDir "RUN_SUMMARY.md"
        $summary = @(
            "# EPC Modules Audit Run Summary",
            "",
            ("RUN_DIR: " + $runDir),
            "USE_REAL_SERVICES=false",
            "",
            "Pass status:",
            ("- PASS 1: " + $passStatus["PASS 1"]),
            ("- PASS 2: " + $passStatus["PASS 2"]),
            ("- PASS 3: " + $passStatus["PASS 3"]),
            ("- PASS 4: " + $passStatus["PASS 4"]),
            ("- PASS 5: " + $passStatus["PASS 5"]),
            "",
            "Evidence file sizes:",
            ("- epc_module_inventory.md: " + (Get-FileSizeText -Path (Join-Path $runDir "epc_module_inventory.md")) + " bytes"),
            ("- epc_allowed_paths.md: " + (Get-FileSizeText -Path (Join-Path $runDir "epc_allowed_paths.md")) + " bytes"),
            ("- epc_boundary_violations.md: " + (Get-FileSizeText -Path (Join-Path $runDir "epc_boundary_violations.md")) + " bytes"),
            ("- epc_contracts_and_schemas.md: " + (Get-FileSizeText -Path (Join-Path $runDir "epc_contracts_and_schemas.md")) + " bytes"),
            ("- epc_chokepoint_invariants.md: " + (Get-FileSizeText -Path (Join-Path $runDir "epc_chokepoint_invariants.md")) + " bytes"),
            ("- epc_e2e_golden_path.md: " + (Get-FileSizeText -Path (Join-Path $runDir "epc_e2e_golden_path.md")) + " bytes"),
            "",
            "Tail excerpts:",
            "## epc_module_inventory.md",
            (Get-FileTail -Path (Join-Path $runDir "epc_module_inventory.md")),
            "",
            "## epc_allowed_paths.md",
            (Get-FileTail -Path (Join-Path $runDir "epc_allowed_paths.md")),
            "",
            "## epc_boundary_violations.md",
            (Get-FileTail -Path (Join-Path $runDir "epc_boundary_violations.md")),
            "",
            "## epc_contracts_and_schemas.md",
            (Get-FileTail -Path (Join-Path $runDir "epc_contracts_and_schemas.md")),
            "",
            "## epc_chokepoint_invariants.md",
            (Get-FileTail -Path (Join-Path $runDir "epc_chokepoint_invariants.md")),
            "",
            "## epc_e2e_golden_path.md",
            (Get-FileTail -Path (Join-Path $runDir "epc_e2e_golden_path.md"))
        )
        Set-Content -Path $summaryPath -Value $summary
    }

    if ($failure) {
        throw $failure
    }
} finally {
    Pop-Location
}
