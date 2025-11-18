<#
.SYNOPSIS
  Test Script for delete-folder-structure-development.ps1

.DESCRIPTION
  Tests the delete-folder-structure-development.ps1 script.

.PARAMETER TestRoot
  Root directory for test execution. Default: "D:\ZeroUI-Test-Dev-Delete"

.EXAMPLE
  .\test-delete-development.ps1
#>

[CmdletBinding()]
param(
    [string]$TestRoot = "D:\ZeroUI-Test-Dev-Delete"
)

$ErrorActionPreference = "Stop"

$parentDir = Split-Path $PSScriptRoot -Parent
$scriptRoot = Join-Path $parentDir "tools"
if(-not (Test-Path $scriptRoot)) {
    Write-Error "Script root not found: $scriptRoot"
    exit 1
}
$scriptRoot = (Resolve-Path $scriptRoot).Path
$createScript = Join-Path $scriptRoot "create-folder-structure-development.ps1"
$deleteScript = Join-Path $scriptRoot "delete-folder-structure-development.ps1"

Write-Host "`nTesting delete-folder-structure-development.ps1" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

# Cleanup
if(Test-Path $TestRoot) {
    Remove-Item -Path $TestRoot -Recurse -Force -ErrorAction SilentlyContinue
}

# Test 1: Create then delete
Write-Host "[TEST 1] Create then delete with Force" -ForegroundColor Yellow
$testPath = Join-Path $TestRoot "test1"
New-Item -ItemType Directory -Path (Split-Path $testPath -Parent) -Force | Out-Null

& $createScript -ZuRoot $testPath
if($LASTEXITCODE -eq 0) {
    & $deleteScript -ZuRoot $testPath -Force
    if($LASTEXITCODE -eq 0) {
        $stillExists = Test-Path (Join-Path $testPath "development")
        if(-not $stillExists) {
            Write-Host "[PASS] Environment deleted successfully" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] Environment still exists" -ForegroundColor Red
        }
    } else {
        Write-Host "[FAIL] Delete script execution failed" -ForegroundColor Red
    }
} else {
    Write-Host "[FAIL] Create script execution failed" -ForegroundColor Red
}

# Test 2: WhatIf mode
Write-Host "`n[TEST 2] WhatIf mode (should not delete)" -ForegroundColor Yellow
$testPath2 = Join-Path $TestRoot "test2"
& $createScript -ZuRoot $testPath2
if($LASTEXITCODE -eq 0) {
    & $deleteScript -ZuRoot $testPath2 -WhatIf
    if($LASTEXITCODE -eq 0) {
        $stillExists = Test-Path (Join-Path $testPath2 "development")
        if($stillExists) {
            Write-Host "[PASS] WhatIf mode preserved structure" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] WhatIf mode deleted structure" -ForegroundColor Red
        }
    }
}

# Cleanup
if(Test-Path $TestRoot) {
    Remove-Item -Path $TestRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "`nTest completed." -ForegroundColor Cyan
