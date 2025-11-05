<#
.SYNOPSIS
  Test Script for delete-folder-structure.ps1 (Main Delete Script)

.DESCRIPTION
  Tests the main delete-folder-structure.ps1 script that deletes all environments.

.PARAMETER TestRoot
  Root directory for test execution. Default: "D:\ZeroUI-Test-Main-Delete"

.EXAMPLE
  .\test-delete-main.ps1
#>

[CmdletBinding()]
param(
    [string]$TestRoot = "D:\ZeroUI-Test-Main-Delete"
)

$ErrorActionPreference = "Stop"

$parentDir = Split-Path $PSScriptRoot -Parent
$scriptRoot = Join-Path $parentDir "tools"
if(-not (Test-Path $scriptRoot)) {
    Write-Error "Script root not found: $scriptRoot"
    exit 1
}
$scriptRoot = (Resolve-Path $scriptRoot).Path
$deleteScript = Join-Path $scriptRoot "delete-folder-structure.ps1"

Write-Host "`nTesting delete-folder-structure.ps1 (Main Delete Script)" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

if(Test-Path $TestRoot) {
    Remove-Item -Path $TestRoot -Recurse -Force -ErrorAction SilentlyContinue
}

# Create all environments first
Write-Host "[SETUP] Creating all environments..." -ForegroundColor Yellow

$createScripts = @(
    "create-folder-structure-development.ps1",
    "create-folder-structure-integration.ps1",
    "create-folder-structure-staging.ps1",
    "create-folder-structure-production.ps1"
)

foreach($createScript in $createScripts) {
    $scriptPath = Join-Path $scriptRoot $createScript
    if(Test-Path $scriptPath) {
        & $scriptPath -ZuRoot $TestRoot
    }
}

Write-Host "[TEST 1] Delete all environments with Force" -ForegroundColor Yellow
& $deleteScript -ZuRoot $TestRoot -Force
if($LASTEXITCODE -eq 0) {
    $devExists = Test-Path (Join-Path $TestRoot "development")
    $intExists = Test-Path (Join-Path $TestRoot "integration")
    $stagingExists = Test-Path (Join-Path $TestRoot "staging")
    $prodExists = Test-Path (Join-Path $TestRoot "production")
    
    if(-not $devExists -and -not $intExists -and -not $stagingExists -and -not $prodExists) {
        Write-Host "[PASS] All environments deleted successfully" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Some environments still exist" -ForegroundColor Red
    }
} else {
    Write-Host "[FAIL] Delete script execution failed" -ForegroundColor Red
}

# Test 2: WhatIf mode
Write-Host "`n[SETUP] Recreating all environments..." -ForegroundColor Yellow
foreach($createScript in $createScripts) {
    $scriptPath = Join-Path $scriptRoot $createScript
    if(Test-Path $scriptPath) {
        & $scriptPath -ZuRoot $TestRoot
    }
}

Write-Host "[TEST 2] WhatIf mode (should not delete)" -ForegroundColor Yellow
& $deleteScript -ZuRoot $TestRoot -WhatIf
if($LASTEXITCODE -eq 0) {
    $devExists = Test-Path (Join-Path $TestRoot "development")
    $intExists = Test-Path (Join-Path $TestRoot "integration")
    
    if($devExists -and $intExists) {
        Write-Host "[PASS] WhatIf mode preserved all environments" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] WhatIf mode deleted environments" -ForegroundColor Red
    }
}

# Test 3: With Environment parameter
Write-Host "`n[TEST 3] Delete with Environment parameter" -ForegroundColor Yellow
& $deleteScript -ZuRoot $TestRoot -Environment "development" -Force
if($LASTEXITCODE -eq 0) {
    $devExists = Test-Path (Join-Path $TestRoot "development")
    $intExists = Test-Path (Join-Path $TestRoot "integration")
    
    # Should delete all environments, but IDE only from development
    Write-Host "[INFO] Check if all environments were deleted (IDE only from development)" -ForegroundColor Cyan
}

# Cleanup
if(Test-Path $TestRoot) {
    Remove-Item -Path $TestRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "`nTest completed." -ForegroundColor Cyan

