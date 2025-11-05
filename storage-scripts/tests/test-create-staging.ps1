<#
.SYNOPSIS
  Test Script for create-folder-structure-staging.ps1

.DESCRIPTION
  Tests the create-folder-structure-staging.ps1 script.

.PARAMETER TestRoot
  Root directory for test execution. Default: "D:\ZeroUI-Test-Staging"

.EXAMPLE
  .\test-create-staging.ps1
#>

[CmdletBinding()]
param(
    [string]$TestRoot = "D:\ZeroUI-Test-Staging",
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
$scriptPath = Join-Path $scriptRoot "create-folder-structure-staging.ps1"

Write-Host "`nTesting create-folder-structure-staging.ps1" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

if(Test-Path $TestRoot) {
    Remove-Item -Path $TestRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "[TEST] Create staging environment" -ForegroundColor Yellow
& $scriptPath -ZuRoot $TestRoot
if($LASTEXITCODE -eq 0) {
    $tenantExists = Test-Path (Join-Path $TestRoot "staging\tenant")
    $productExists = Test-Path (Join-Path $TestRoot "staging\product")
    $sharedExists = Test-Path (Join-Path $TestRoot "staging\shared")
    $ideExists = Test-Path (Join-Path $TestRoot "staging\ide")
    
    if($tenantExists -and $productExists -and $sharedExists -and -not $ideExists) {
        Write-Host "[PASS] Staging environment created correctly (no IDE plane)" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Structure incorrect" -ForegroundColor Red
    }
} else {
    Write-Host "[FAIL] Script execution failed" -ForegroundColor Red
}

if(-not $SkipCleanup -and (Test-Path $TestRoot)) {
    Remove-Item -Path $TestRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "`nTest completed." -ForegroundColor Cyan

