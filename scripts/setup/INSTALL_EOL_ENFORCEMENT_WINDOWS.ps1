# Windows PowerShell Installation Script for EOL Enforcement
# Run this script to set up EOL validation on Windows

Write-Host "=" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "EOL Enforcement Setup for Windows" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Git
Write-Host "Checking Git installation..." -ForegroundColor Yellow
try {
    $gitVersion = git --version 2>&1
    Write-Host "  Found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Git not found. Please install Git." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Installation Options:" -ForegroundColor Cyan
Write-Host "  1. Minimal (Validation script only - manual validation)"
Write-Host "  2. Git Hook (Automatic validation on commit)"
Write-Host "  3. Pre-commit Framework (Full automated setup)"
Write-Host ""

$choice = Read-Host "Select option (1-3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Minimal setup complete." -ForegroundColor Green
        Write-Host "Usage: python scripts\ci\validate_eol.py" -ForegroundColor Yellow
        Write-Host "       python scripts\ci\validate_eol.py --fix" -ForegroundColor Yellow
    }

    "2" {
        Write-Host ""
        Write-Host "Installing Git hook..." -ForegroundColor Yellow

        $hookPath = ".git\hooks\pre-commit"
        $hookSource = "scripts\git-hooks\pre-commit-eol"

        if (Test-Path $hookSource) {
            Copy-Item $hookSource $hookPath -Force
            Write-Host "  Git hook installed: $hookPath" -ForegroundColor Green
            Write-Host ""
            Write-Host "Test: Create a file with wrong EOL and try to commit" -ForegroundColor Yellow
        } else {
            Write-Host "  ERROR: Hook source not found: $hookSource" -ForegroundColor Red
        }
    }

    "3" {
        Write-Host ""
        Write-Host "Installing pre-commit framework..." -ForegroundColor Yellow

        try {
            python -m pip install pre-commit
            Write-Host "  Pre-commit installed" -ForegroundColor Green

            python -m pre_commit install
            Write-Host "  Hooks installed" -ForegroundColor Green

            Write-Host ""
            Write-Host "Testing hooks..." -ForegroundColor Yellow
            python -m pre_commit run --all-files

            Write-Host ""
            Write-Host "Setup complete!" -ForegroundColor Green
        } catch {
            Write-Host "  ERROR: Failed to install pre-commit" -ForegroundColor Red
            Write-Host "  Try: python -m pip install pre-commit" -ForegroundColor Yellow
        }
    }

    default {
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan
