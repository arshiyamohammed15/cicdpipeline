Param(
    [int]$Workers = 4
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot
$env:TEST_RANDOM_SEED = "42"

$testFailures = @()
$exitCode = 0

function Invoke-Step {
    param(
        [string]$Name,
        [ScriptBlock]$Action,
        [switch]$ContinueOnError
    )

    Write-Host "==> $Name" -ForegroundColor Cyan
    try {
        & $Action
        if ($LASTEXITCODE -ne 0 -and -not $ContinueOnError) {
            throw "Step failed with exit code $LASTEXITCODE"
        }
        Write-Host "<== $Name (Success)`n" -ForegroundColor Green
    } catch {
        Write-Host "<== $Name (Failed: $_)`n" -ForegroundColor Red
        $script:testFailures += $Name
        if (-not $ContinueOnError) {
            $script:exitCode = 1
        }
    }
}

function With-Location {
    param(
        [string]$Path,
        [ScriptBlock]$Action
    )

    Push-Location $Path
    try {
        & $Action
    } finally {
        Pop-Location
    }
}

function Resolve-PythonExe {
    $venvPy = Join-Path $repoRoot 'venv\Scripts\python.exe'
    if (Test-Path $venvPy) {
        return $venvPy
    }
    return 'python'
}

# Phase 1: Clear all caches
Invoke-Step "Clear all test caches" {
    & (Resolve-PythonExe) tools/test_registry/clear_cache.py
}

# Phase 2: Build prerequisites
Invoke-Step "Install root JS deps" {
    npm ci
}

Invoke-Step "Build TypeScript" {
    npm run build:typescript
}

# Phase 3: Run all test types

# 3.1 Python Tests
# Note: --cache-clear and -p no:cacheprovider are already in pyproject.toml
Invoke-Step "Run Python unit tests" -ContinueOnError {
    & (Resolve-PythonExe) -m pytest -n $Workers -o maxfail=0 -m unit tests/
}

Invoke-Step "Run Python integration tests" -ContinueOnError {
    & (Resolve-PythonExe) -m pytest -n $Workers -o maxfail=0 -m integration tests/
}

Invoke-Step "Run Python E2E tests" -ContinueOnError {
    & (Resolve-PythonExe) -m pytest -n $Workers -o maxfail=0 tests/ -k "e2e"
}

Invoke-Step "Run Python security tests" -ContinueOnError {
    & (Resolve-PythonExe) -m pytest -n $Workers -o maxfail=0 -m security tests/
}

Invoke-Step "Run Python performance tests" -ContinueOnError {
    & (Resolve-PythonExe) -m pytest -n $Workers -o maxfail=0 -m performance tests/
}

Invoke-Step "Run Python resilience tests" -ContinueOnError {
    & (Resolve-PythonExe) -m pytest -n $Workers -o maxfail=0 tests/ -k "resilience"
}

Invoke-Step "Run Python database tests" -ContinueOnError {
    # Database tests are typically integration tests, but run separately to ensure isolation
    & (Resolve-PythonExe) -m pytest -n $Workers -o maxfail=0 tests/ -k "database or db"
}

Invoke-Step "Run Python zeroui_observability tests" -ContinueOnError {
    & (Resolve-PythonExe) -m pytest -n $Workers -o maxfail=0 src/shared_libs/zeroui_observability
}

Invoke-Step "Run Python marker-only tests (constitution, llm, dgp, alerting, budgeting, deployment)" -ContinueOnError {
    & (Resolve-PythonExe) -m pytest -n $Workers -o maxfail=0 tests/ -m "constitution or llm_gateway_unit or llm_gateway_integration or dgp_regression or dgp_security or dgp_performance or dgp_compliance or alerting_regression or alerting_security or alerting_performance or alerting_integration or budgeting_regression or budgeting_security or budgeting_performance or deployment_regression or deployment_security or deployment_integration"
}

# 3.2 TypeScript/Jest Tests (all: storage, edge-agent, e2e, platform, infra_config, vscode-extension __tests__)
Invoke-Step "Run TypeScript/Jest tests" -ContinueOnError {
    npx jest --config jest.config.js --maxWorkers=$Workers --no-cache
}

# 3.3 VS Code Extension Tests
Invoke-Step "Install VS Code extension deps" {
    With-Location (Join-Path $repoRoot 'src\vscode-extension') {
        npm ci
    }
}

Invoke-Step "Compile VS Code extension" {
    With-Location (Join-Path $repoRoot 'src\vscode-extension') {
        npm run compile
    }
}

Invoke-Step "Run VS Code extension tests" -ContinueOnError {
    With-Location (Join-Path $repoRoot 'src\vscode-extension') {
        npm test
    }
}

# Phase 4: Summary
Write-Host "`n=== Test Execution Summary ===" -ForegroundColor Cyan
if ($testFailures.Count -eq 0) {
    Write-Host "All test suites passed!" -ForegroundColor Green
    $exitCode = 0
} else {
    Write-Host "The following test suites failed:" -ForegroundColor Red
    foreach ($failure in $testFailures) {
        Write-Host "  - $failure" -ForegroundColor Red
    }
    $exitCode = 1
}

exit $exitCode
