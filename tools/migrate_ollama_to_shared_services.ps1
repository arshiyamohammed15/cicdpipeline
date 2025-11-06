# Migrate Ollama and TinyLlama to Shared Services Plane
# Per folder-business-rules.md section 4.4: llm/(guardrails|routing|tools|ollama|tinyllama)/

param(
    [string]$ZuRoot = $env:ZU_ROOT,
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

# Determine ZU_ROOT
if (-not $ZuRoot) {
    $ZuRoot = (Get-Location).Path
    Write-Host "ZU_ROOT not set, using current directory: $ZuRoot" -ForegroundColor Yellow
}

$targetOllama = Join-Path $ZuRoot "shared\llm\ollama"
$targetTinyllama = Join-Path $ZuRoot "shared\llm\tinyllama"

Write-Host "=== Ollama and TinyLlama Migration to Shared Services Plane ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Source Locations:" -ForegroundColor Yellow
Write-Host "  Ollama Executable: C:\Users\pc\AppData\Local\Programs\Ollama\"
Write-Host "  Models (OLLAMA_MODELS): $env:OLLAMA_MODELS"
Write-Host "  Models (Default): C:\Users\pc\.ollama"
Write-Host ""
Write-Host "Target Locations (per folder-business-rules.md):" -ForegroundColor Green
Write-Host "  Ollama: $targetOllama"
Write-Host "  TinyLlama: $targetTinyllama"
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE - No changes will be made" -ForegroundColor Magenta
    Write-Host ""
}

# Step 1: Create target directories
Write-Host "Step 1: Creating target directories..." -ForegroundColor Cyan
if (-not $DryRun) {
    New-Item -ItemType Directory -Path $targetOllama -Force | Out-Null
    New-Item -ItemType Directory -Path $targetTinyllama -Force | Out-Null
    Write-Host "  Created: $targetOllama" -ForegroundColor Green
    Write-Host "  Created: $targetTinyllama" -ForegroundColor Green
} else {
    Write-Host "  Would create: $targetOllama" -ForegroundColor Gray
    Write-Host "  Would create: $targetTinyllama" -ForegroundColor Gray
}

# Step 2: Copy Ollama executable and files
Write-Host ""
Write-Host "Step 2: Copying Ollama installation..." -ForegroundColor Cyan
$ollamaSource = "C:\Users\pc\AppData\Local\Programs\Ollama"
if (Test-Path $ollamaSource) {
    if (-not $DryRun) {
        # Create bin subdirectory for executables
        $targetOllamaBin = Join-Path $targetOllama "bin"
        New-Item -ItemType Directory -Path $targetOllamaBin -Force | Out-Null
        
        # Copy ollama.exe
        if (Test-Path (Join-Path $ollamaSource "ollama.exe")) {
            Copy-Item (Join-Path $ollamaSource "ollama.exe") -Destination $targetOllamaBin -Force
            Write-Host "  Copied ollama.exe to $targetOllamaBin" -ForegroundColor Green
        }
        
        # Copy other files if they exist
        Get-ChildItem $ollamaSource -File | ForEach-Object {
            Copy-Item $_.FullName -Destination $targetOllamaBin -Force
            Write-Host "  Copied $($_.Name) to $targetOllamaBin" -ForegroundColor Green
        }
    } else {
        Write-Host "  Would copy Ollama files from $ollamaSource to $targetOllama\bin" -ForegroundColor Gray
    }
} else {
    Write-Host "  Ollama source not found at $ollamaSource" -ForegroundColor Yellow
}

# Step 3: Move/Copy TinyLlama model files
Write-Host ""
Write-Host "Step 3: Moving TinyLlama model files..." -ForegroundColor Cyan
$modelSources = @()
if ($env:OLLAMA_MODELS -and (Test-Path $env:OLLAMA_MODELS)) {
    $modelSources += $env:OLLAMA_MODELS
}
if (Test-Path "C:\Users\pc\.ollama") {
    $modelSources += "C:\Users\pc\.ollama"
}

foreach ($source in $modelSources) {
    Write-Host "  Checking: $source" -ForegroundColor Gray
    $tinyllamaFiles = Get-ChildItem $source -Recurse -Filter "*tinyllama*" -ErrorAction SilentlyContinue
    if ($tinyllamaFiles) {
        foreach ($file in $tinyllamaFiles) {
            if (-not $DryRun) {
                $relativePath = $file.FullName.Substring($source.Length).TrimStart('\')
                $targetPath = Join-Path $targetTinyllama $relativePath
                $targetDir = Split-Path $targetPath -Parent
                if (-not (Test-Path $targetDir)) {
                    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
                }
                Copy-Item $file.FullName -Destination $targetPath -Force
                Write-Host "    Copied: $($file.Name) to $targetTinyllama" -ForegroundColor Green
            } else {
                Write-Host "    Would copy: $($file.Name) to $targetTinyllama" -ForegroundColor Gray
            }
        }
    }
}

# Step 4: Update environment variable
Write-Host ""
Write-Host "Step 4: Updating OLLAMA_MODELS environment variable..." -ForegroundColor Cyan
if (-not $DryRun) {
    [System.Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $targetTinyllama, [System.EnvironmentVariableTarget]::User)
    $env:OLLAMA_MODELS = $targetTinyllama
    Write-Host "  Updated OLLAMA_MODELS to: $targetTinyllama" -ForegroundColor Green
    Write-Host "  Note: You may need to restart your terminal for the change to take effect" -ForegroundColor Yellow
} else {
    Write-Host "  Would set OLLAMA_MODELS to: $targetTinyllama" -ForegroundColor Gray
}

# Step 5: Update configuration files
Write-Host ""
Write-Host "Step 5: Updating configuration files..." -ForegroundColor Cyan
$ollamaConfig = Join-Path $targetOllama "config.json"
$tinyllamaConfig = Join-Path $targetTinyllama "config.json"

if (-not $DryRun) {
    # Update Ollama config if it exists
    if (Test-Path $ollamaConfig) {
        $config = Get-Content $ollamaConfig | ConvertFrom-Json
        $config.storage_path = $targetOllama
        $config | ConvertTo-Json -Depth 10 | Set-Content $ollamaConfig
        Write-Host "  Updated: $ollamaConfig" -ForegroundColor Green
    }
    
    # Update TinyLlama config if it exists
    if (Test-Path $tinyllamaConfig) {
        $config = Get-Content $tinyllamaConfig | ConvertFrom-Json
        $config.storage_path = $targetTinyllama
        $config | ConvertTo-Json -Depth 10 | Set-Content $tinyllamaConfig
        Write-Host "  Updated: $tinyllamaConfig" -ForegroundColor Green
    }
} else {
    Write-Host "  Would update configuration files" -ForegroundColor Gray
}

# Step 6: Create uninstall script for old locations
Write-Host ""
Write-Host "Step 6: Creating uninstall script..." -ForegroundColor Cyan
$uninstallScript = Join-Path $targetOllama "uninstall_old_installation.ps1"
if (-not $DryRun) {
    $uninstallContent = @"
# Uninstall script for old Ollama installation
# Run this after verifying the new installation works

Write-Host "Removing old Ollama installation..." -ForegroundColor Yellow

# Remove old Ollama executable location (if portable)
`$oldOllama = "C:\Users\pc\AppData\Local\Programs\Ollama"
if (Test-Path `$oldOllama) {
    Write-Host "Removing: `$oldOllama" -ForegroundColor Yellow
    Remove-Item `$oldOllama -Recurse -Force -ErrorAction SilentlyContinue
}

# Remove old models location (if moved)
`$oldModels = "$env:OLLAMA_MODELS"
if (`$oldModels -and `$oldModels -ne "$targetTinyllama" -and (Test-Path `$oldModels)) {
    Write-Host "Removing: `$oldModels" -ForegroundColor Yellow
    Remove-Item `$oldModels -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Uninstall complete. Old installation removed." -ForegroundColor Green
"@
    Set-Content -Path $uninstallScript -Value $uninstallContent
    Write-Host "  Created: $uninstallScript" -ForegroundColor Green
    Write-Host "  Note: Review and run this script after verifying the new installation works" -ForegroundColor Yellow
} else {
    Write-Host "  Would create uninstall script" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Migration Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "New Installation Locations:" -ForegroundColor Cyan
Write-Host "  Ollama: $targetOllama"
Write-Host "  TinyLlama: $targetTinyllama"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Restart your terminal to load the new OLLAMA_MODELS environment variable"
Write-Host "  2. Test the installation: ollama list"
Write-Host "  3. If everything works, run: $uninstallScript"
Write-Host ""

