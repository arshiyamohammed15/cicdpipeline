<#
.SYNOPSIS
  Test Script for delete-folder-structure-integration.ps1

.DESCRIPTION
  Tests the delete-folder-structure-integration.ps1 script.

.PARAMETER TestRoot
  Root directory for test execution. Default: "D:\ZeroUI-Test-Int-Delete"

.EXAMPLE
  .\test-delete-integration.ps1
#>

[CmdletBinding()]
param(
    [string]$TestRoot = "D:\ZeroUI-Test-Int-Delete"
)

$ErrorActionPreference = "Stop"

$parentDir = Split-Path $PSScriptRoot -Parent
$scriptRoot = Join-Path $parentDir "tools"
if(-not (Test-Path $scriptRoot)) {
    Write-Error "Script root not found: $scriptRoot"
    exit 1
}
$scriptRoot = (Resolve-Path $scriptRoot).Path
$createScript = Join-Path $scriptRoot "create-folder-structure-integration.ps1"
$deleteScript = Join-Path $scriptRoot "delete-folder-structure-integration.ps1"

Write-Host "`nTesting delete-folder-structure-integration.ps1" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

if(Test-Path $TestRoot) {
    Remove-Item -Path $TestRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "[TEST] Create then delete integration environment" -ForegroundColor Yellow
& $createScript -ZuRoot $TestRoot
if($LASTEXITCODE -eq 0) {
    & $deleteScript -ZuRoot $TestRoot -Force
    if($LASTEXITCODE -eq 0) {
        $stillExists = Test-Path (Join-Path $TestRoot "integration")
        if(-not $stillExists) {
            Write-Host "[PASS] Integration environment deleted successfully" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] Environment still exists" -ForegroundColor Red
        }
    }
}

if(Test-Path $TestRoot) {
    Remove-Item -Path $TestRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "`nTest completed." -ForegroundColor Cyan

