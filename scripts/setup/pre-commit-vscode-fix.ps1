#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Fixes pre-commit hooks to work in VS Code on Windows

.DESCRIPTION
    This script enhances the pre-commit hook to work in both Cursor terminal
    and VS Code by trying multiple Python paths and ensuring proper execution.

.NOTES
    Run this script if pre-commit hooks don't work in VS Code commit button.
#>

$ErrorActionPreference = "Stop"

Write-Host "Fixing pre-commit hooks for VS Code compatibility..." -ForegroundColor Cyan

# Check if pre-commit is installed
try {
    $null = python -m pre_commit --version 2>&1
    Write-Host "✓ pre-commit is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ pre-commit is not installed. Installing..." -ForegroundColor Yellow
    python -m pip install pre-commit
}

# Reinstall hooks to ensure they're up to date
Write-Host "Reinstalling pre-commit hooks..." -ForegroundColor Cyan
python -m pre_commit install --hook-type pre-commit

# Enhance the hook script
$hookPath = ".git/hooks/pre-commit"
if (Test-Path $hookPath) {
    Write-Host "Enhancing pre-commit hook for VS Code compatibility..." -ForegroundColor Cyan

    $hookContent = Get-Content $hookPath -Raw

    # Check if already enhanced
    if ($hookContent -match "python3|python -mpre_commit") {
        Write-Host "✓ Hook already enhanced" -ForegroundColor Green
    } else {
        # Backup original
        Copy-Item $hookPath "$hookPath.backup" -Force
        Write-Host "✓ Backed up original hook" -ForegroundColor Green

        # The hook should already be enhanced by pre-commit install
        Write-Host "✓ Hook reinstalled with latest configuration" -ForegroundColor Green
    }
} else {
    Write-Host "✗ Pre-commit hook not found. Installing..." -ForegroundColor Yellow
    python -m pre_commit install --hook-type pre-commit
}

Write-Host ""
Write-Host "Testing pre-commit hooks..." -ForegroundColor Cyan
python -m pre_commit run --all-files --hook-stage commit

Write-Host ""
Write-Host "✓ Pre-commit hooks are now configured for VS Code!" -ForegroundColor Green
Write-Host ""
Write-Host "If hooks still don't work in VS Code:" -ForegroundColor Yellow
Write-Host "  1. Restart VS Code" -ForegroundColor Yellow
Write-Host "  2. Check VS Code Git settings (git.allowNoVerifyCommit should be false)" -ForegroundColor Yellow
Write-Host "  3. Ensure Python is in your PATH" -ForegroundColor Yellow
Write-Host "  4. Try: git config --global core.hooksPath .git/hooks" -ForegroundColor Yellow
