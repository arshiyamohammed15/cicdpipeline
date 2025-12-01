#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Downloads and installs k6 for Windows

.DESCRIPTION
    Downloads the k6 Windows binary (v0.48.0) and places it in tools/k6/
    for local performance testing. This script is required for Windows developers
    who need to run k6 performance tests locally.

.NOTES
    The k6 binary is not stored in git. This script downloads it on-demand.
    CI environments install k6 via package managers (apt-get, etc.)
#>

$ErrorActionPreference = "Stop"

$K6_VERSION = "v0.48.0"
$K6_DIR = "tools/k6"
$K6_ZIP_DIR = "$K6_DIR/k6-$K6_VERSION-windows-amd64"
$K6_EXE = "$K6_ZIP_DIR/k6.exe"
$K6_ZIP = "$K6_DIR/k6-$K6_VERSION-windows-amd64.zip"
$K6_URL = "https://github.com/grafana/k6/releases/download/$K6_VERSION/k6-$K6_VERSION-windows-amd64.zip"

Write-Host "Installing k6 for Windows..." -ForegroundColor Cyan
Write-Host "Version: $K6_VERSION" -ForegroundColor Cyan
Write-Host ""

# Check if k6 already exists
if (Test-Path $K6_EXE) {
    Write-Host "✓ k6 already installed at $K6_EXE" -ForegroundColor Green
    
    # Verify it's executable
    try {
        $version = & $K6_EXE version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ k6 is working correctly" -ForegroundColor Green
            Write-Host $version
            exit 0
        }
    } catch {
        Write-Host "⚠ k6 exists but may be corrupted. Re-downloading..." -ForegroundColor Yellow
    }
}

# Create tools/k6 directory if it doesn't exist
if (-not (Test-Path $K6_DIR)) {
    New-Item -ItemType Directory -Path $K6_DIR -Force | Out-Null
    Write-Host "✓ Created directory: $K6_DIR" -ForegroundColor Green
}

# Download k6
Write-Host "Downloading k6 from $K6_URL..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $K6_URL -OutFile $K6_ZIP -UseBasicParsing
    Write-Host "✓ Download complete" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to download k6: $_" -ForegroundColor Red
    exit 1
}

# Extract k6
Write-Host "Extracting k6..." -ForegroundColor Cyan
try {
    Expand-Archive -Path $K6_ZIP -DestinationPath $K6_DIR -Force
    Write-Host "✓ Extraction complete" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to extract k6: $_" -ForegroundColor Red
    exit 1
}

# Clean up zip file
if (Test-Path $K6_ZIP) {
    Remove-Item $K6_ZIP -Force
    Write-Host "✓ Cleaned up zip file" -ForegroundColor Green
}

# Verify installation
if (Test-Path $K6_EXE) {
    Write-Host ""
    Write-Host "✓ k6 installed successfully at $K6_EXE" -ForegroundColor Green
    
    # Test k6
    try {
        $version = & $K6_EXE version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "k6 version information:" -ForegroundColor Cyan
            Write-Host $version
            Write-Host ""
            Write-Host "✓ k6 is ready to use!" -ForegroundColor Green
            Write-Host ""
            Write-Host "You can now run:" -ForegroundColor Cyan
            Write-Host "  npm run test:llm-gateway:performance:windows" -ForegroundColor Yellow
        } else {
            Write-Host "⚠ k6 installed but version check failed" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠ k6 installed but could not verify version: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ k6 installation failed: $K6_EXE not found" -ForegroundColor Red
    exit 1
}

