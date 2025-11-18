<#
.SYNOPSIS
  Test Script for create-folder-structure-development.ps1

.DESCRIPTION
  Tests the create-folder-structure-development.ps1 script.
  Verifies that all required folders are created correctly.

.PARAMETER TestRoot
  Root directory for test execution. Default: "D:\ZeroUI-Test-Dev"

.PARAMETER SkipCleanup
  If specified, does not clean up test directories after execution.

.EXAMPLE
  .\test-create-development.ps1
  .\test-create-development.ps1 -TestRoot "E:\Test-Dev"
#>

[CmdletBinding()]
param(
    [string]$TestRoot = "D:\ZeroUI-Test-Dev",
    [switch]$SkipCleanup
)

$ErrorActionPreference = "Stop"

$parentDir = Split-Path $PSScriptRoot -Parent
$scriptRoot = Join-Path $parentDir "tools"
if(-not (Test-Path $scriptRoot)) {
    Write-Error "Script root not found: $scriptRoot"
    exit 1
}
$scriptRoot = (Resolve-Path $scriptRoot).Path
$scriptPath = Join-Path $scriptRoot "create-folder-structure-development.ps1"

Write-Host "`nTesting create-folder-structure-development.ps1" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

# Cleanup
if(Test-Path $TestRoot) {
    Remove-Item -Path $TestRoot -Recurse -Force -ErrorAction SilentlyContinue
}

# Test 1: Basic creation
Write-Host "[TEST 1] Basic creation with default parameters" -ForegroundColor Yellow
$testPath = Join-Path $TestRoot "test1"
New-Item -ItemType Directory -Path (Split-Path $testPath -Parent) -Force | Out-Null

& $scriptPath -ZuRoot $testPath
if($LASTEXITCODE -eq 0) {
    $ideExists = Test-Path (Join-Path $testPath "development\ide")
    $tenantExists = Test-Path (Join-Path $testPath "development\tenant")
    $productExists = Test-Path (Join-Path $testPath "development\product")
    $sharedExists = Test-Path (Join-Path $testPath "development\shared")

    if($ideExists -and $tenantExists -and $productExists -and $sharedExists) {
        Write-Host "[PASS] All folders created successfully" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Missing folders" -ForegroundColor Red
    }
} else {
    Write-Host "[FAIL] Script execution failed" -ForegroundColor Red
}

# Test 2: With parameters
Write-Host "`n[TEST 2] Creation with Drive and ProductName parameters" -ForegroundColor Yellow
$testPath2 = Join-Path $TestRoot "test2"
& $scriptPath -Drive "D" -ProductName "TestProduct" -ZuRoot $testPath2
if($LASTEXITCODE -eq 0) {
    Write-Host "[PASS] Script accepts parameters" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Script failed with parameters" -ForegroundColor Red
}

# Test 3: With CompatAliases
Write-Host "`n[TEST 3] Creation with CompatAliases switch" -ForegroundColor Yellow
$testPath3 = Join-Path $TestRoot "test3"
& $scriptPath -ZuRoot $testPath3 -CompatAliases
if($LASTEXITCODE -eq 0) {
    $metaSchemaExists = Test-Path (Join-Path $testPath3 "development\tenant\meta\schema")
    if($metaSchemaExists) {
        Write-Host "[PASS] CompatAliases folder created" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] CompatAliases folder not created" -ForegroundColor Red
    }
} else {
    Write-Host "[FAIL] Script execution failed" -ForegroundColor Red
}

# Cleanup
if(-not $SkipCleanup -and (Test-Path $TestRoot)) {
    Remove-Item -Path $TestRoot -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "`nTest directories cleaned up." -ForegroundColor Green
}

Write-Host "`nTest completed." -ForegroundColor Cyan
