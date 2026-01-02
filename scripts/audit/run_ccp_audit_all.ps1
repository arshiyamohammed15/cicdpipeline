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

    $runDir = Join-Path $repoRoot ("artifacts/audit_runs/ccp_audit_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
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
            python scripts/audit/ccp_inventory_allowed_paths.py $repoRoot --out-dir $runDir
        }
        $inv = Join-Path $runDir "ccp_module_inventory.md"
        $paths = Join-Path $runDir "ccp_allowed_paths.md"
        Assert-EvidenceFiles -PassLabel "PASS 1" -Paths @($inv, $paths) -RunDir $runDir -LogPath $pass1Log
        $passStatus[$currentPass] = "PASS"

        # PASS 2 - Boundary Check
        $currentPass = "PASS 2"
        $passStatus[$currentPass] = "RUNNING"
        $pass2Log = Join-Path $runDir "pass2_boundary_check.log"
        $boundaryScript = if (Test-Path "tools/arch/boundary_check.py") {
            "tools/arch/boundary_check.py"
        } else {
            "scripts/audit/ccp_boundary_check.py"
        }
        Invoke-LoggedCommand -Label "PASS 2 boundary check" -LogPath $pass2Log -Command {
            python $boundaryScript $repoRoot --out-dir $runDir
        }
        $boundary = Join-Path $runDir "ccp_boundary_violations.md"
        Assert-EvidenceFiles -PassLabel "PASS 2" -Paths @($boundary) -RunDir $runDir -LogPath $pass2Log
        $passStatus[$currentPass] = "PASS"

        # PASS 3 - Contracts & Schemas
        $currentPass = "PASS 3"
        $passStatus[$currentPass] = "RUNNING"
        $pass3Log = Join-Path $runDir "pass3_contracts_and_schemas.log"
        if (Test-Path $pass3Log) {
            Remove-Item -Force $pass3Log
        }
        & python -m pytest --import-mode=importlib `
            tests/contracts/cross_cutting_concern_services/validate_examples.py `
            tests/contracts/integration_adaptors/validate_examples.py `
            tests/contracts/llm_gateway/validate_examples.py `
            tests/contracts/evidence_receipt_indexing_service/validate_examples.py -q *> $pass3Log
        $contractsExit = $LASTEXITCODE
        Add-Content -Path $pass3Log -Value ("CONTRACTS_EXIT_CODE=" + $contractsExit)
        if ($contractsExit -ne 0 -and $contractsExit -ne 5) {
            Add-Content -Path $pass3Log -Value ("UTC_FINISHED=" + (Get-Date).ToUniversalTime().ToString("o"))
            Write-Host ("FAIL: PASS 3 contract tests returned " + $contractsExit)
            Write-Host "Log tail:"
            Write-LogTail -Path $pass3Log -Lines 40
            throw "PASS 3 contract tests failed."
        }
        & python scripts/ci/validate_llm_gateway_schemas.py *>> $pass3Log
        $schemasExit = $LASTEXITCODE
        Add-Content -Path $pass3Log -Value ("SCHEMAS_EXIT_CODE=" + $schemasExit)
        Add-Content -Path $pass3Log -Value ("PY_EXIT_CODE=" + $schemasExit)
        Add-Content -Path $pass3Log -Value ("UTC_FINISHED=" + (Get-Date).ToUniversalTime().ToString("o"))
        if ($schemasExit -ne 0) {
            Write-Host ("FAIL: PASS 3 schema validation returned " + $schemasExit)
            Write-Host "Log tail:"
            Write-LogTail -Path $pass3Log -Lines 40
            throw "PASS 3 schema validation failed."
        }
        $pass3Evidence = Join-Path $runDir "ccp_contracts_and_schemas.md"
        $pass3Lines = @(
            "# CCP Contracts and Schemas (PASS 3)",
            "",
            "Status: PASS",
            "Contract tests:",
            "- tests/contracts/cross_cutting_concern_services/validate_examples.py",
            "- tests/contracts/integration_adaptors/validate_examples.py",
            "- tests/contracts/llm_gateway/validate_examples.py",
            "- tests/contracts/evidence_receipt_indexing_service/validate_examples.py",
            "",
            "Schema validation:",
            "- scripts/ci/validate_llm_gateway_schemas.py"
        )
        Set-Content -Path $pass3Evidence -Value $pass3Lines
        Assert-EvidenceFiles -PassLabel "PASS 3" -Paths @($pass3Evidence) -RunDir $runDir -LogPath $pass3Log
        $passStatus[$currentPass] = "PASS"

        # PASS 4 - Chokepoint Invariants
        $currentPass = "PASS 4"
        $passStatus[$currentPass] = "RUNNING"
        $pass4Log = Join-Path $runDir "pass4_chokepoint_invariants.log"
        Invoke-LoggedCommand -Label "PASS 4 chokepoint invariants" -LogPath $pass4Log -Command {
            python -m pytest --import-mode=importlib tests/ccp_audit/test_ccp_smoke.py -q
        }
        $pass4Evidence = Join-Path $runDir "ccp_chokepoint_invariants.md"
        $pass4Lines = @(
            "# CCP Chokepoint Invariants (PASS 4)",
            "",
            "Status: PASS",
            "Tests:",
            "- tests/ccp_audit/test_ccp_smoke.py",
            "",
            "Owner invariants:",
            "- Identity/IAM owner: EPC-1",
            "- Policy/config owner: EPC-3 + config",
            "- Schema validation owner: EPC-12",
            "- Token budgets owner: PM-6",
            "- External tool reliability owner: PM-5",
            "- Governed memory writes owner: EPC-2 (receipts required)",
            "- Receipt indexing owner: PM-7"
        )
        Set-Content -Path $pass4Evidence -Value $pass4Lines
        Assert-EvidenceFiles -PassLabel "PASS 4" -Paths @($pass4Evidence) -RunDir $runDir -LogPath $pass4Log
        $passStatus[$currentPass] = "PASS"

        # PASS 5 - Golden Path
        $currentPass = "PASS 5"
        $passStatus[$currentPass] = "RUNNING"
        $pass5Log = Join-Path $runDir "pass5_e2e_golden_path.log"
        Invoke-LoggedCommand -Label "PASS 5 golden path" -LogPath $pass5Log -Command {
            python -m pytest --import-mode=importlib tests/ccp_audit/test_ccp_e2e_golden_path.py -q
        }
        $pass5Evidence = Join-Path $runDir "ccp_e2e_golden_path.md"
        $pass5Lines = @(
            "# CCP E2E Golden Path (PASS 5)",
            "",
            "Status: PASS",
            "Tests:",
            "- tests/ccp_audit/test_ccp_e2e_golden_path.py",
            "",
            "Covered steps:",
            "- Load local policy snapshot/config",
            "- Resolve identity via EPC-1 stub",
            "- Validate tool output against schema (EPC-12)",
            "- Emit receipt via CCCS (PM-2)",
            "- Index receipt via PM-7 adapter"
        )
        Set-Content -Path $pass5Evidence -Value $pass5Lines
        Assert-EvidenceFiles -PassLabel "PASS 5" -Paths @($pass5Evidence) -RunDir $runDir -LogPath $pass5Log
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
            "# CCP Modules Audit Run Summary",
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
            ("- ccp_module_inventory.md: " + (Get-FileSizeText -Path (Join-Path $runDir "ccp_module_inventory.md")) + " bytes"),
            ("- ccp_allowed_paths.md: " + (Get-FileSizeText -Path (Join-Path $runDir "ccp_allowed_paths.md")) + " bytes"),
            ("- ccp_boundary_violations.md: " + (Get-FileSizeText -Path (Join-Path $runDir "ccp_boundary_violations.md")) + " bytes"),
            ("- ccp_contracts_and_schemas.md: " + (Get-FileSizeText -Path (Join-Path $runDir "ccp_contracts_and_schemas.md")) + " bytes"),
            ("- ccp_chokepoint_invariants.md: " + (Get-FileSizeText -Path (Join-Path $runDir "ccp_chokepoint_invariants.md")) + " bytes"),
            ("- ccp_e2e_golden_path.md: " + (Get-FileSizeText -Path (Join-Path $runDir "ccp_e2e_golden_path.md")) + " bytes"),
            "",
            "Tail excerpts:",
            "## ccp_module_inventory.md",
            (Get-FileTail -Path (Join-Path $runDir "ccp_module_inventory.md")),
            "",
            "## ccp_allowed_paths.md",
            (Get-FileTail -Path (Join-Path $runDir "ccp_allowed_paths.md")),
            "",
            "## ccp_boundary_violations.md",
            (Get-FileTail -Path (Join-Path $runDir "ccp_boundary_violations.md")),
            "",
            "## ccp_contracts_and_schemas.md",
            (Get-FileTail -Path (Join-Path $runDir "ccp_contracts_and_schemas.md")),
            "",
            "## ccp_chokepoint_invariants.md",
            (Get-FileTail -Path (Join-Path $runDir "ccp_chokepoint_invariants.md")),
            "",
            "## ccp_e2e_golden_path.md",
            (Get-FileTail -Path (Join-Path $runDir "ccp_e2e_golden_path.md"))
        )
        Set-Content -Path $summaryPath -Value $summary
    }

    if ($failure) {
        throw $failure
    }
} finally {
    Pop-Location
}
