[CmdletBinding()]
param(
    [string]$TestRoot = "D:\ZeroUI-Test-Minimal"
)

$ErrorActionPreference = "Stop"

$parentDir = Split-Path $PSScriptRoot -Parent
$scriptRoot = Join-Path $parentDir "tools"
if(-not (Test-Path $scriptRoot)) {
    Write-Error "Script root not found: $scriptRoot"
    exit 1
}
$scriptRoot = (Resolve-Path $scriptRoot).Path

Write-Host "Script root: $scriptRoot" -ForegroundColor Green
Write-Host "Test root: $TestRoot" -ForegroundColor Green

