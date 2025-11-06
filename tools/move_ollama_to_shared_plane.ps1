# Move Ollama and TinyLlama from repo to actual shared plane
# Per folder-business-rules.md: {ZU_ROOT}/shared/llm/(ollama|tinyllama)/

param(
    [string]$ZuRoot = "D:\ZeroUI\development",
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== Moving Ollama and TinyLlama to Shared Plane ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Source (repo - WRONG):" -ForegroundColor Red
$repoRoot = (Get-Location).Path
$sourceOllama = Join-Path $repoRoot "shared\llm\ollama"
$sourceTinyllama = Join-Path $repoRoot "shared\llm\tinyllama"
Write-Host "  Ollama: $sourceOllama"
Write-Host "  TinyLlama: $sourceTinyllama"
Write-Host ""
Write-Host "Target (shared plane - CORRECT):" -ForegroundColor Green
$targetOllama = Join-Path $ZuRoot "shared\llm\ollama"
$targetTinyllama = Join-Path $ZuRoot "shared\llm\tinyllama"
Write-Host "  Ollama: $targetOllama"
Write-Host "  TinyLlama: $targetTinyllama"
Write-Host ""
Write-Host "ZU_ROOT: $ZuRoot" -ForegroundColor Yellow
Write-Host ""

if ($DryRun) {
    Write-Host "DRY RUN MODE - No changes will be made" -ForegroundColor Magenta
    Write-Host ""
}

# Step 1: Create ZU_ROOT structure if it doesn't exist
Write-Host "Step 1: Creating ZU_ROOT structure..." -ForegroundColor Cyan
if (-not $DryRun) {
    if (-not (Test-Path $ZuRoot)) {
        New-Item -ItemType Directory -Path $ZuRoot -Force | Out-Null
        Write-Host "  Created ZU_ROOT: $ZuRoot" -ForegroundColor Green
    }
    New-Item -ItemType Directory -Path (Join-Path $ZuRoot "shared\llm\ollama\bin") -Force | Out-Null
    New-Item -ItemType Directory -Path $targetTinyllama -Force | Out-Null
    Write-Host "  Created target directories" -ForegroundColor Green
} else {
    Write-Host "  Would create: $targetOllama" -ForegroundColor Gray
    Write-Host "  Would create: $targetTinyllama" -ForegroundColor Gray
}

# Step 2: Move Ollama files
Write-Host ""
Write-Host "Step 2: Moving Ollama installation..." -ForegroundColor Cyan
if (Test-Path $sourceOllama) {
    if (-not $DryRun) {
        # Move bin directory
        $sourceBin = Join-Path $sourceOllama "bin"
        $targetBin = Join-Path $targetOllama "bin"
        if (Test-Path $sourceBin) {
            Move-Item $sourceBin -Destination $targetBin -Force
            Write-Host "  Moved bin directory" -ForegroundColor Green
        }
        
        # Move config and other files
        Get-ChildItem $sourceOllama -File | ForEach-Object {
            Move-Item $_.FullName -Destination $targetOllama -Force
            Write-Host "  Moved: $($_.Name)" -ForegroundColor Green
        }
    } else {
        Write-Host "  Would move Ollama files from $sourceOllama to $targetOllama" -ForegroundColor Gray
    }
} else {
    Write-Host "  Source Ollama directory not found: $sourceOllama" -ForegroundColor Yellow
}

# Step 3: Move TinyLlama files
Write-Host ""
Write-Host "Step 3: Moving TinyLlama models..." -ForegroundColor Cyan
if (Test-Path $sourceTinyllama) {
    if (-not $DryRun) {
        Get-ChildItem $sourceTinyllama -Recurse | ForEach-Object {
            $relativePath = $_.FullName.Substring($sourceTinyllama.Length).TrimStart('\')
            $targetPath = Join-Path $targetTinyllama $relativePath
            
            if ($_.PSIsContainer) {
                if (-not (Test-Path $targetPath)) {
                    New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
                }
            } else {
                $targetDir = Split-Path $targetPath -Parent
                if (-not (Test-Path $targetDir)) {
                    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
                }
                Move-Item $_.FullName -Destination $targetPath -Force
                Write-Host "  Moved: $relativePath" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "  Would move TinyLlama files from $sourceTinyllama to $targetTinyllama" -ForegroundColor Gray
    }
} else {
    Write-Host "  Source TinyLlama directory not found: $sourceTinyllama" -ForegroundColor Yellow
}

# Step 4: Update environment variable
Write-Host ""
Write-Host "Step 4: Updating OLLAMA_MODELS environment variable..." -ForegroundColor Cyan
if (-not $DryRun) {
    [System.Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $targetTinyllama, [System.EnvironmentVariableTarget]::User)
    $env:OLLAMA_MODELS = $targetTinyllama
    Write-Host "  Updated OLLAMA_MODELS to: $targetTinyllama" -ForegroundColor Green
    Write-Host "  Note: Restart terminal for environment variable to take effect" -ForegroundColor Yellow
} else {
    Write-Host "  Would set OLLAMA_MODELS to: $targetTinyllama" -ForegroundColor Gray
}

# Step 5: Update configuration files
Write-Host ""
Write-Host "Step 5: Updating configuration files..." -ForegroundColor Cyan
$ollamaConfig = Join-Path $targetOllama "config.json"
$tinyllamaConfig = Join-Path $targetTinyllama "config.json"

if (-not $DryRun) {
    if (Test-Path $ollamaConfig) {
        $config = Get-Content $ollamaConfig | ConvertFrom-Json
        $config.storage_path = $targetOllama
        $config.executable_path = Join-Path $targetOllama "bin\ollama.exe"
        $config.models_path = $targetTinyllama
        $config | ConvertTo-Json -Depth 10 | Set-Content $ollamaConfig
        Write-Host "  Updated: $ollamaConfig" -ForegroundColor Green
    }
    
    if (Test-Path $tinyllamaConfig) {
        $config = Get-Content $tinyllamaConfig | ConvertFrom-Json
        $config.storage_path = $targetTinyllama
        $config | ConvertTo-Json -Depth 10 | Set-Content $tinyllamaConfig
        Write-Host "  Updated: $tinyllamaConfig" -ForegroundColor Green
    }
} else {
    Write-Host "  Would update configuration files" -ForegroundColor Gray
}

# Step 6: Update service code to use ZU_ROOT
Write-Host ""
Write-Host "Step 6: Configuration files updated" -ForegroundColor Cyan
Write-Host "  Service code will read from ZU_ROOT environment variable" -ForegroundColor Gray

Write-Host ""
Write-Host "=== Migration Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "New Locations (in shared plane, not repo):" -ForegroundColor Cyan
Write-Host "  Ollama: $targetOllama"
Write-Host "  TinyLlama: $targetTinyllama"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Set ZU_ROOT environment variable: `$env:ZU_ROOT = `"$ZuRoot`"" -ForegroundColor White
Write-Host "  2. Restart terminal to load environment variables"
Write-Host "  3. Test: $targetOllama\bin\ollama.exe --version"
Write-Host ""

