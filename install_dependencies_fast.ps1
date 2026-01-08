# Fast dependency installation using pip resolver optimizations
# This avoids the hang by using pip's resolver more efficiently

$ErrorActionPreference = "Stop"
if ($PSScriptRoot) {
    $repoRoot = $PSScriptRoot
} else {
    $repoRoot = Get-Location
}
Set-Location $repoRoot

Write-Host "Installing dependencies with optimized resolver..." -ForegroundColor Cyan
Write-Host ""

# Method: Install with resolver optimizations
# Use --no-build-isolation and --prefer-binary to speed up
# Install in two passes: first without deps, then resolve deps

Write-Host "[Pass 1] Installing packages without dependency resolution..." -ForegroundColor Yellow
python -m pip install --no-deps -r requirements.txt

Write-Host ""
Write-Host "[Pass 2] Resolving and installing dependencies..." -ForegroundColor Yellow
# Now install with dependency resolution, but pip will use already-installed packages
python -m pip install -r requirements.txt --upgrade

Write-Host ""
Write-Host "✓ Installation complete!" -ForegroundColor Green
python -m pip check
