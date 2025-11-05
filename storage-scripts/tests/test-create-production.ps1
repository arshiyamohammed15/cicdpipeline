<#
.SYNOPSIS
  Test Script for create-folder-structure-production.ps1

.DESCRIPTION
  Tests the create-folder-structure-production.ps1 script.

.PARAMETER TestRoot
  Root directory for test execution. Default: "D:\ZeroUI-Test-Production"

.EXAMPLE
  .\test-create-production.ps1
#>

[CmdletBinding()]
param(
    [string]$TestRoot = "D:\ZeroUI-Test-Production",
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
$scriptPath = Join-Path $scriptRoot "create-folder-structure-production.ps1"

Write-Host "`nTesting create-folder-structure-production.ps1" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

if(Test-Path $TestRoot) {
    Remove-Item -Path $TestRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "[TEST] Create production environment" -ForegroundColor Yellow
& $scriptPath -ZuRoot $TestRoot
if($LASTEXITCODE -eq 0) {
    $tenantExists = Test-Path (Join-Path $TestRoot "production\tenant")
    $productExists = Test-Path (Join-Path $TestRoot "production\product")
    $sharedExists = Test-Path (Join-Path $TestRoot "production\shared")
    $ideExists = Test-Path (Join-Path $TestRoot "production\ide")
    
    if($tenantExists -and $productExists -and $sharedExists -and -not $ideExists) {
        Write-Host "[PASS] Production environment created correctly (no IDE plane)" -ForegroundColor Green
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

