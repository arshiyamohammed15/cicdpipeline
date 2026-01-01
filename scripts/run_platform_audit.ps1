param()

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvActivate = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"

if (Test-Path -Path $venvActivate) {
    Write-Host "Activating virtual environment: $venvActivate"
    . $venvActivate
} else {
    Write-Host "No .venv found. Continuing with system Python."
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "FAIL: python not found on PATH."
    exit 1
}

$smokeResults = Join-Path $repoRoot "platform_smoke_results.txt"
Write-Host "Running platform smoke tests..."
python -m pytest -q tests/platform_smoke/ 2>&1 | Tee-Object -FilePath $smokeResults
$smokeExit = $LASTEXITCODE
if ($smokeExit -ne 0) {
    Write-Host "FAIL: platform smoke tests failed (exit $smokeExit)."
}

$boundaryScript = Join-Path $repoRoot "scripts\boundary_check.py"
$boundaryExit = 0
if (Test-Path -Path $boundaryScript) {
    Write-Host "Running boundary check..."
    python $boundaryScript --staged --unstaged
    $boundaryExit = $LASTEXITCODE
    if ($boundaryExit -ne 0) {
        Write-Host "FAIL: boundary_check.py failed (exit $boundaryExit)."
    }
} else {
    Write-Host "SKIP: scripts/boundary_check.py not found."
}

if ($smokeExit -eq 0 -and $boundaryExit -eq 0) {
    Write-Host "PASS: platform audit checks completed successfully."
    exit 0
}

Write-Host "FAIL: platform audit checks did not pass."
exit 1
