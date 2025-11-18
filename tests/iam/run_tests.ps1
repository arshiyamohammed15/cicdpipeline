# IAM Module Test Execution Script for PowerShell
# Execute all IAM test suites

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IAM Module (M21) Test Execution" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

# Test 1: Unit Tests
Write-Host "Running Unit Tests (test_iam_service.py)..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow
python tests/test_iam_service.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Unit tests failed with exit code: $LASTEXITCODE" -ForegroundColor Red
} else {
    Write-Host "Unit tests completed successfully" -ForegroundColor Green
}
Write-Host ""

# Test 2: Integration Tests
Write-Host "Running Integration Tests (test_iam_routes.py)..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow
python tests/test_iam_routes.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Integration tests failed with exit code: $LASTEXITCODE" -ForegroundColor Red
} else {
    Write-Host "Integration tests completed successfully" -ForegroundColor Green
}
Write-Host ""

# Test 3: Performance Tests
Write-Host "Running Performance Tests (test_iam_performance.py)..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow
python tests/test_iam_performance.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Performance tests failed with exit code: $LASTEXITCODE" -ForegroundColor Red
} else {
    Write-Host "Performance tests completed successfully" -ForegroundColor Green
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Execution Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
