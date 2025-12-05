# Update test manifest script for Windows CI/CD and local use

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Set-Location $ProjectRoot

Write-Host "Updating test manifest..."
python tools/test_registry/generate_manifest.py --update

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to update test manifest"
    exit 1
}

Write-Host "Test manifest updated successfully"

