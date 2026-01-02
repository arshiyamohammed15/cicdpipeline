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

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
Push-Location $repoRoot
try {
    $env:USE_REAL_SERVICES = "false"

    $runDir = Join-Path $repoRoot ("artifacts/audit_runs/pm_audit_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
    New-Item -ItemType Directory -Force $runDir | Out-Null
    Write-Host ("RUN_DIR=" + $runDir)

    # PASS 1/2
    $pass1Log = Join-Path $runDir "pass1_2_inventory_allowed_paths.log"
    & python scripts/audit/pm_inventory_allowed_paths.py --out-dir $runDir *> $pass1Log
    $exitCode = $LASTEXITCODE
    Add-Content -Path $pass1Log -Value ("PY_EXIT_CODE=" + $exitCode)
    Add-Content -Path $pass1Log -Value ("UTC_FINISHED=" + (Get-Date).ToUniversalTime().ToString("o"))
    if ($exitCode -ne 0) {
        Write-Host ("FAIL: PASS 1/2 returned " + $exitCode)
        Write-Host "Log tail:"
        Write-LogTail -Path $pass1Log -Lines 40
        throw "PASS 1/2 failed with non-zero exit code."
    }

    $inv = Join-Path $runDir "pm_module_inventory.md"
    $paths = Join-Path $runDir "pm_allowed_paths.md"
    $missing = @()
    if (-not (Test-Path $inv)) {
        $missing += "pm_module_inventory.md missing"
    } elseif ((Get-Item $inv).Length -le 0) {
        $missing += "pm_module_inventory.md empty"
    }
    if (-not (Test-Path $paths)) {
        $missing += "pm_allowed_paths.md missing"
    } elseif ((Get-Item $paths).Length -le 0) {
        $missing += "pm_allowed_paths.md empty"
    }
    if ($missing.Count -gt 0) {
        Write-Host "FAIL: PASS 1/2 evidence files missing or empty."
        Write-Host "RUN_DIR listing:"
        Get-ChildItem -Path $runDir | Select-Object Name, Length
        Write-Host "Log tail:"
        Write-LogTail -Path $pass1Log -Lines 40
        throw ("PASS 1/2 evidence validation failed: " + ($missing -join "; "))
    }

    Write-Host ("LOG=" + $pass1Log)
    Write-Host ("LOG_BYTES=" + (Get-Item $pass1Log).Length)
    Write-Host ("FOUND=pm_module_inventory.md BYTES=" + (Get-Item $inv).Length)
    Write-Host ("FOUND=pm_allowed_paths.md BYTES=" + (Get-Item $paths).Length)

    # PASS 3
    $pass3ContractsLog = Join-Path $runDir "pass3_contracts.log"
    Invoke-LoggedCommand -Label "PASS 3 contracts" -LogPath $pass3ContractsLog -Command {
        python -m pytest --import-mode=importlib `
            tests/contracts/mmm_engine/validate_examples.py `
            tests/contracts/cross_cutting_concern_services/validate_examples.py `
            tests/contracts/signal_ingestion_and_normalization/validate_examples.py `
            tests/contracts/detection_engine_core/validate_examples.py `
            tests/contracts/integration_adaptors/validate_examples.py `
            tests/contracts/llm_gateway/validate_examples.py `
            tests/contracts/evidence_receipt_indexing_service/validate_examples.py -q
    }

    $pass3SchemaLog = Join-Path $runDir "pass3_llm_gateway_schema_validation.log"
    Invoke-LoggedCommand -Label "PASS 3 schema validation" -LogPath $pass3SchemaLog -Command {
        python scripts/ci/validate_llm_gateway_schemas.py
    }

    # PASS 4
    $pass4Log = Join-Path $runDir "pass4_smoke.log"
    Invoke-LoggedCommand -Label "PASS 4 smoke" -LogPath $pass4Log -Command {
        python -m pytest --import-mode=importlib tests/pm_audit/test_pm_smoke.py -q
    }

    # PASS 5
    $pass5Log = Join-Path $runDir "pass5_e2e_golden_path.log"
    Invoke-LoggedCommand -Label "PASS 5 golden path" -LogPath $pass5Log -Command {
        python -m pytest --import-mode=importlib tests/pm_audit/test_pm_e2e_golden_path.py -q
    }

    $summaryPath = Join-Path $runDir "RUN_SUMMARY.md"
    $summary = @(
        "# PM Audit Run Summary",
        "",
        "RUN_DIR: $runDir",
        "USE_REAL_SERVICES=false",
        "",
        "PASS 1/2: PASS",
        "PASS 3 (contracts): PASS",
        "PASS 3 (schemas): PASS",
        "PASS 4: PASS",
        "PASS 5: PASS",
        "",
        "Evidence files:",
        "- pm_module_inventory.md",
        "- pm_allowed_paths.md",
        "- pass1_2_inventory_allowed_paths.log",
        "- pass3_contracts.log",
        "- pass3_llm_gateway_schema_validation.log",
        "- pass4_smoke.log",
        "- pass5_e2e_golden_path.log",
        "- RUN_SUMMARY.md"
    )
    Set-Content -Path $summaryPath -Value $summary
} finally {
    Pop-Location
}
