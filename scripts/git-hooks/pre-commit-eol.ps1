# Pre-commit hook for EOL validation (PowerShell version)
# Copy to .git/hooks/pre-commit

$ErrorActionPreference = "Stop"

# Get project root
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# Add to Python path
$env:PYTHONPATH = "$projectRoot;$env:PYTHONPATH"

# Run validation
python "$projectRoot\scripts\ci\validate_eol.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nEOL validation failed. Commit blocked." -ForegroundColor Red
    Write-Host "To fix: python scripts\ci\validate_eol.py --fix" -ForegroundColor Yellow
    exit 1
}

Write-Host "EOL validation passed" -ForegroundColor Green
exit 0
