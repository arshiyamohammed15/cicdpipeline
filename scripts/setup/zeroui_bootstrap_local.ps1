<#
.SYNOPSIS
  ZeroUI Local Bootstrap Script - One-command setup for fresh workstation

.DESCRIPTION
  Ensures prerequisites, creates folder structure, installs dependencies,
  and runs unit tests. Idempotent and safe to run multiple times.

.PARAMETER Mode
  Operation mode: "setup" (default) or "verify" (check-only)

.PARAMETER AutoInstallPrereqs
  If set, attempts to install missing prerequisites via winget

.PARAMETER SetupDockerPlanePostgres
  If set, starts 3 Postgres containers (tenant/zeroui/shared) on ports 5433/5434/5435

.PARAMETER SetupOllama
  If set, ensures Ollama is installed

.PARAMETER PullSmallModels
  If set, pulls tinyllama, qwen2.5-coder:14b, and llama3:instruct

.PARAMETER PullBigModels
  If set, pulls qwen2.5-coder:32b

.PARAMETER RunTests
  If set, runs unit tests (default ON in setup mode, OFF in verify mode)

.PARAMETER ZuRoot
  Optional override for ZU_ROOT; otherwise uses .env or defaults to {repo}\.zu

.EXAMPLE
  .\zeroui_bootstrap_local.ps1 -Mode setup -RunTests

.EXAMPLE
  .\zeroui_bootstrap_local.ps1 -Mode setup -AutoInstallPrereqs -SetupDockerPlanePostgres -SetupOllama -PullSmallModels -RunTests

.EXAMPLE
  .\zeroui_bootstrap_local.ps1 -Mode verify
#>

[CmdletBinding()]
param(
    [ValidateSet("setup","verify")]
    [string]$Mode = "setup",
    [switch]$AutoInstallPrereqs,
    [switch]$SetupDockerPlanePostgres,
    [switch]$SetupOllama,
    [switch]$PullSmallModels,
    [switch]$PullBigModels,
    [switch]$RunTests,
    [string]$ZuRoot
)

# Strict error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Track failures
$script:Failures = @()
$script:Warnings = @()

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
    $script:Warnings += $Message
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
    $script:Failures += $Message
}

function Test-Command {
    param([string]$Command, [string]$TestArg = "--version")
    try {
        $null = & $Command $TestArg 2>&1
        return $true
    } catch {
        return $false
    }
}

function Test-CommandWithVersion {
    param([string]$Command, [string]$MinVersion, [string]$TestArg = "--version")
    try {
        $output = & $Command $TestArg 2>&1 | Select-Object -First 1
        if ($output -match $MinVersion) {
            return $true
        }
        # Try version comparison if output is parseable
        if ($output -match '(\d+)\.(\d+)') {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            $requiredParts = $MinVersion -split '\.'
            $requiredMajor = [int]$requiredParts[0]
            $requiredMinor = if ($requiredParts.Length -gt 1) { [int]$requiredParts[1] } else { 0 }
            return ($major -gt $requiredMajor) -or (($major -eq $requiredMajor) -and ($minor -ge $requiredMinor))
        }
        return $false
    } catch {
        return $false
    }
}

function Install-ViaWinget {
    param([string]$PackageId, [string]$PackageName)
    if (-not (Test-Command "winget")) {
        Write-Error-Custom "winget not available. Cannot auto-install $PackageName"
        return $false
    }
    Write-Info "Installing $PackageName via winget..."
    try {
        & winget install -e --id $PackageId --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$PackageName installed successfully"
            return $true
        } else {
            Write-Error-Custom "winget install failed for $PackageName (exit code: $LASTEXITCODE)"
            return $false
        }
    } catch {
        Write-Error-Custom "Failed to install $PackageName via winget: $($_.Exception.Message)"
        return $false
    }
}

function Get-RepoRoot {
    # Try git rev-parse first
    try {
        $root = & git rev-parse --show-toplevel 2>&1
        if ($LASTEXITCODE -eq 0 -and (Test-Path $root)) {
            return $root
        }
    } catch {
        # Fall through to path walking
    }
    
    # Walk up from script location
    $scriptPath = $PSScriptRoot
    $current = $scriptPath
    while ($current) {
        $pyproject = Join-Path $current "pyproject.toml"
        $packageJson = Join-Path $current "package.json"
        if ((Test-Path $pyproject) -and (Test-Path $packageJson)) {
            return $current
        }
        $parent = Split-Path $current -Parent
        if ($parent -eq $current) {
            break
        }
        $current = $parent
    }
    
    throw "Could not determine repo root. Run from repo directory or ensure pyproject.toml and package.json exist."
}

function Get-ZuRoot {
    param([string]$RepoRoot, [string]$Override)
    
    if ($Override) {
        return $Override
    }
    
    # Check .env file
    $envFile = Join-Path $RepoRoot ".env"
    if (Test-Path $envFile) {
        $content = Get-Content $envFile -Raw
        if ($content -match 'ZU_ROOT\s*=\s*(.+)') {
            $envValue = $matches[1].Trim()
            # Remove quotes if present
            $envValue = $envValue -replace '^["'']|["'']$', ''
            if ($envValue) {
                return $envValue
            }
        }
    }
    
    # Default to {repo}\.zu
    return Join-Path $RepoRoot ".zu"
}

function Update-EnvFile {
    param([string]$RepoRoot, [string]$ZuRoot)
    
    $envFile = Join-Path $RepoRoot ".env"
    $zuRootLine = "ZU_ROOT=$ZuRoot"
    
    if (Test-Path $envFile) {
        $content = Get-Content $envFile -Raw
        if ($content -match 'ZU_ROOT\s*=') {
            # Replace existing ZU_ROOT line
            $content = $content -replace 'ZU_ROOT\s*=.*', $zuRootLine
            Set-Content -Path $envFile -Value $content -NoNewline
        } else {
            # Append ZU_ROOT line
            Add-Content -Path $envFile -Value "`n$zuRootLine"
        }
    } else {
        # Create new .env file
        Set-Content -Path $envFile -Value $zuRootLine
    }
    Write-Success "Updated .env file with ZU_ROOT=$ZuRoot"
}

# ============================================================================
# Main execution
# ============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ZeroUI Local Bootstrap" -ForegroundColor Cyan
Write-Host "Mode: $Mode" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get repo root
try {
    $RepoRoot = Get-RepoRoot
    Write-Success "Repo root: $RepoRoot"
} catch {
    Write-Error-Custom $_.Exception.Message
    exit 1
}

# Resolve ZU_ROOT
$ZuRootResolved = Get-ZuRoot -RepoRoot $RepoRoot -Override $ZuRoot
Write-Info "ZU_ROOT: $ZuRootResolved"

# Update .env if needed
Update-EnvFile -RepoRoot $RepoRoot -ZuRoot $ZuRootResolved

# ============================================================================
# Prerequisite checks
# ============================================================================

Write-Host "`n--- Checking Prerequisites ---" -ForegroundColor Yellow

# Git
Write-Info "Checking Git..."
if (Test-Command "git") {
    $gitVersion = & git --version
    Write-Success "Git: $gitVersion"
} else {
    if ($AutoInstallPrereqs) {
        if (-not (Install-ViaWinget "Git.Git" "Git")) {
            Write-Error-Custom "Git is required. Install from: https://git-scm.com/download/win"
        }
    } else {
        Write-Error-Custom "Git is required. Install from: https://git-scm.com/download/win or use -AutoInstallPrereqs"
    }
}

# Python 3.11
Write-Info "Checking Python 3.11..."
$pythonFound = $false
if (Test-Command "py") {
    try {
        $pyOutput = & py -3.11 -V 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python: $pyOutput"
            $pythonFound = $true
        }
    } catch {
        # Try python command
    }
}
if (-not $pythonFound) {
    if (Test-Command "python") {
        $pyVersion = & python --version 2>&1
        if ($pyVersion -match "3\.(1[1-9]|[2-9]\d)") {
            Write-Success "Python: $pyVersion"
            $pythonFound = $true
        }
    }
}
if (-not $pythonFound) {
    if ($AutoInstallPrereqs) {
        if (-not (Install-ViaWinget "Python.Python.3.11" "Python 3.11")) {
            Write-Error-Custom "Python 3.11+ is required. Install from: https://www.python.org/downloads/ or use -AutoInstallPrereqs"
        }
    } else {
        Write-Error-Custom "Python 3.11+ is required. Install from: https://www.python.org/downloads/ or use -AutoInstallPrereqs"
    }
}

# Node.js LTS
Write-Info "Checking Node.js LTS..."
if (Test-Command "node") {
    $nodeVersion = & node -v
    if ($nodeVersion -match 'v(\d+)') {
        $major = [int]$matches[1]
        if ($major -ge 18) {
            Write-Success "Node.js: $nodeVersion"
        } else {
            if ($AutoInstallPrereqs) {
                if (-not (Install-ViaWinget "OpenJS.NodeJS.LTS" "Node.js LTS")) {
                    Write-Error-Custom "Node.js 18+ (LTS) is required. Install from: https://nodejs.org/ or use -AutoInstallPrereqs"
                }
            } else {
                Write-Error-Custom "Node.js 18+ (LTS) is required. Install from: https://nodejs.org/ or use -AutoInstallPrereqs"
            }
        }
    }
} else {
    if ($AutoInstallPrereqs) {
        if (-not (Install-ViaWinget "OpenJS.NodeJS.LTS" "Node.js LTS")) {
            Write-Error-Custom "Node.js 18+ (LTS) is required. Install from: https://nodejs.org/ or use -AutoInstallPrereqs"
        }
    } else {
        Write-Error-Custom "Node.js 18+ (LTS) is required. Install from: https://nodejs.org/ or use -AutoInstallPrereqs"
    }
}

# npm
Write-Info "Checking npm..."
if (Test-Command "npm") {
    $npmVersion = & npm -v
    Write-Success "npm: $npmVersion"
} else {
    Write-Error-Custom "npm is required (usually comes with Node.js)"
}

# Docker (only if SetupDockerPlanePostgres)
if ($SetupDockerPlanePostgres) {
    Write-Info "Checking Docker..."
    if (Test-Command "docker") {
        $dockerVersion = & docker --version
        Write-Success "Docker: $dockerVersion"
        
        Write-Info "Checking Docker Compose..."
        if (Test-Command "docker" "compose version") {
            $composeVersion = & docker compose version
            Write-Success "Docker Compose: $composeVersion"
        } else {
            if ($AutoInstallPrereqs) {
                Write-Warning-Custom "Docker Compose not found. Ensure Docker Desktop includes compose."
            } else {
                Write-Error-Custom "Docker Compose is required. Install Docker Desktop from: https://www.docker.com/products/docker-desktop/ or use -AutoInstallPrereqs"
            }
        }
    } else {
        if ($AutoInstallPrereqs) {
            if (-not (Install-ViaWinget "Docker.DockerDesktop" "Docker Desktop")) {
                Write-Error-Custom "Docker is required for -SetupDockerPlanePostgres. Install from: https://www.docker.com/products/docker-desktop/ or use -AutoInstallPrereqs"
            }
        } else {
            Write-Error-Custom "Docker is required for -SetupDockerPlanePostgres. Install from: https://www.docker.com/products/docker-desktop/ or use -AutoInstallPrereqs"
        }
    }
}

# Ollama (only if SetupOllama)
if ($SetupOllama) {
    Write-Info "Checking Ollama..."
    if (Test-Command "ollama") {
        $ollamaVersion = & ollama --version
        Write-Success "Ollama: $ollamaVersion"
    } else {
        if ($AutoInstallPrereqs) {
            if (-not (Install-ViaWinget "Ollama.Ollama" "Ollama")) {
                Write-Error-Custom "Ollama is required for -SetupOllama. Install from: https://ollama.ai/ or use -AutoInstallPrereqs"
            }
        } else {
            Write-Error-Custom "Ollama is required for -SetupOllama. Install from: https://ollama.ai/ or use -AutoInstallPrereqs"
        }
    }
}

# Fail if critical prerequisites missing
if ($script:Failures.Count -gt 0) {
    Write-Host "`n--- Prerequisites Check Failed ---" -ForegroundColor Red
    $script:Failures | ForEach-Object { Write-Host "  ✗ $_" -ForegroundColor Red }
    Write-Host "`nPlease install missing prerequisites and run again." -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# Folder structure creation
# ============================================================================

if ($Mode -eq "setup") {
    Write-Host "`n--- Creating Folder Structure ---" -ForegroundColor Yellow
    
    $folderScript = Join-Path $RepoRoot "storage-scripts\tools\create-folder-structure-development.ps1"
    if (-not (Test-Path $folderScript)) {
        Write-Error-Custom "Folder structure script not found: $folderScript"
        exit 1
    }
    
    Write-Info "Running folder structure creator..."
    try {
        & $folderScript -ZuRoot $ZuRootResolved
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Folder structure creation failed (exit code: $LASTEXITCODE)"
        } else {
            Write-Success "Folder structure created"
        }
    } catch {
        Write-Error-Custom "Folder structure creation failed: $_"
    }
    
    # Verify key directories exist (what the script actually creates)
    Write-Info "Verifying folder structure..."
    $requiredDirs = @(
        (Join-Path $ZuRootResolved "development\ide"),
        (Join-Path $ZuRootResolved "development\tenant"),
        (Join-Path $ZuRootResolved "development\product"),
        (Join-Path $ZuRootResolved "development\shared")
    )
    
    $allExist = $true
    foreach ($dir in $requiredDirs) {
        if (Test-Path $dir) {
            Write-Success "Directory exists: $dir"
        } else {
            Write-Error-Custom "Directory missing: $dir"
            $allExist = $false
        }
    }
    
    if (-not $allExist) {
        Write-Error-Custom "Folder structure verification failed"
        exit 1
    }
} else {
    # Verify mode: just check folders exist
    Write-Host "`n--- Verifying Folder Structure ---" -ForegroundColor Yellow
    $requiredDirs = @(
        (Join-Path $ZuRootResolved "development\ide"),
        (Join-Path $ZuRootResolved "development\tenant"),
        (Join-Path $ZuRootResolved "development\product"),
        (Join-Path $ZuRootResolved "development\shared")
    )
    
    $allExist = $true
    foreach ($dir in $requiredDirs) {
        if (Test-Path $dir) {
            Write-Success "Directory exists: $dir"
        } else {
            Write-Error-Custom "Directory missing: $dir"
            $allExist = $false
        }
    }
    
    if (-not $allExist) {
        Write-Error-Custom "Folder structure verification failed"
        exit 1
    }
}

# ============================================================================
# Python environment setup
# ============================================================================

if ($Mode -eq "setup") {
    Write-Host "`n--- Setting Up Python Environment ---" -ForegroundColor Yellow
    
    $venvPath = Join-Path $RepoRoot "venv"
    
    # Create venv if missing
    if (-not (Test-Path $venvPath)) {
        Write-Info "Creating Python virtual environment..."
        try {
            if (Test-Command "py") {
                & py -3.11 -m venv $venvPath
            } else {
                & python -m venv $venvPath
            }
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Failed to create virtual environment (exit code: $LASTEXITCODE)"
                exit 1
            }
            Write-Success "Virtual environment created"
        } catch {
            Write-Error-Custom "Failed to create virtual environment: $_"
            exit 1
        }
    } else {
        Write-Success "Virtual environment already exists"
    }
    
    $pythonExe = Join-Path $venvPath "Scripts\python.exe"
    
    if (-not (Test-Path $pythonExe)) {
        Write-Error-Custom "Python executable not found in venv: $pythonExe"
        exit 1
    }
    
    # Upgrade pip
    Write-Info "Upgrading pip..."
    try {
        & $pythonExe -m pip install --upgrade pip --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Failed to upgrade pip (exit code: $LASTEXITCODE)"
            exit 1
        }
        Write-Success "pip upgraded"
    } catch {
        Write-Error-Custom "Failed to upgrade pip: $_"
        exit 1
    }
    
    # Install dependencies
    Write-Info "Installing Python dependencies from requirements.txt..."
    $requirementsFile = Join-Path $RepoRoot "requirements.txt"
    if (-not (Test-Path $requirementsFile)) {
        Write-Error-Custom "requirements.txt not found: $requirementsFile"
        exit 1
    }
    
    try {
        & $pythonExe -m pip install -r $requirementsFile --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Failed to install Python dependencies (exit code: $LASTEXITCODE)"
            exit 1
        }
        Write-Success "Python dependencies installed"
    } catch {
        Write-Error-Custom "Failed to install Python dependencies: $_"
        exit 1
    }
    
    # Install package in editable mode
    Write-Info "Installing package in editable mode..."
    try {
        Push-Location $RepoRoot
        & $pythonExe -m pip install -e . --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Failed to install package in editable mode (exit code: $LASTEXITCODE)"
            Pop-Location
            exit 1
        }
        Write-Success "Package installed in editable mode"
        Pop-Location
    } catch {
        Pop-Location
        Write-Error-Custom "Failed to install package in editable mode: $_"
        exit 1
    }
}

# ============================================================================
# Node.js dependencies
# ============================================================================

if ($Mode -eq "setup") {
    Write-Host "`n--- Setting Up Node.js Dependencies ---" -ForegroundColor Yellow
    
    # Root package.json
    Write-Info "Installing root Node.js dependencies..."
    try {
        Push-Location $RepoRoot
        if (Test-Path "package-lock.json") {
            & npm ci --silent
        } else {
            & npm install --silent
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Failed to install root Node.js dependencies (exit code: $LASTEXITCODE)"
            Pop-Location
            exit 1
        }
        Write-Success "Root Node.js dependencies installed"
        Pop-Location
    } catch {
        Pop-Location
        Write-Error-Custom "Failed to install root Node.js dependencies: $_"
        exit 1
    }
    
    # VS Code extension
    Write-Info "Installing VS Code extension dependencies..."
    $vscodePath = Join-Path $RepoRoot "src\vscode-extension"
    if (Test-Path $vscodePath) {
        try {
            Push-Location $vscodePath
            if (Test-Path "package-lock.json") {
                & npm ci --silent
            } else {
                & npm install --silent
            }
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Failed to install VS Code extension dependencies (exit code: $LASTEXITCODE)"
                Pop-Location
                exit 1
            }
            Write-Success "VS Code extension dependencies installed"
            Pop-Location
        } catch {
            Pop-Location
            Write-Error-Custom "Failed to install VS Code extension dependencies: $_"
            exit 1
        }
    } else {
        Write-Warning-Custom "VS Code extension directory not found: $vscodePath"
    }
    
    # Edge agent
    Write-Info "Installing edge agent dependencies..."
    $edgeAgentPath = Join-Path $RepoRoot "src\edge-agent"
    if (Test-Path $edgeAgentPath) {
        try {
            Push-Location $edgeAgentPath
            if (Test-Path "package-lock.json") {
                & npm ci --silent
            } else {
                & npm install --silent
            }
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Failed to install edge agent dependencies (exit code: $LASTEXITCODE)"
                Pop-Location
                exit 1
            }
            Write-Success "Edge agent dependencies installed"
            Pop-Location
        } catch {
            Pop-Location
            Write-Error-Custom "Failed to install edge agent dependencies: $_"
            exit 1
        }
    } else {
        Write-Warning-Custom "Edge agent directory not found: $edgeAgentPath"
    }
}

# ============================================================================
# Docker Postgres planes
# ============================================================================

if ($Mode -eq "setup" -and $SetupDockerPlanePostgres) {
    Write-Host "`n--- Setting Up Docker Postgres Planes ---" -ForegroundColor Yellow
    
    $composeFile = Join-Path $RepoRoot "infra\local\docker-compose.planes-postgres.yml"
    if (-not (Test-Path $composeFile)) {
        Write-Error-Custom "Docker compose file not found: $composeFile"
        exit 1
    }
    
    Write-Info "Starting Postgres containers..."
    try {
        Push-Location $RepoRoot
        & docker compose -f $composeFile up -d
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Failed to start Postgres containers (exit code: $LASTEXITCODE)"
            Pop-Location
            exit 1
        }
        Write-Success "Postgres containers started"
        Pop-Location
    } catch {
        Pop-Location
        Write-Error-Custom "Failed to start Postgres containers: $_"
        exit 1
    }
    
    Write-Info "Connection strings:"
    Write-Host "  Tenant:   postgresql://zeroui:zeroui_dev_only@localhost:5433/zeroui" -ForegroundColor Cyan
    Write-Host "  Zeroui:   postgresql://zeroui:zeroui_dev_only@localhost:5434/zeroui" -ForegroundColor Cyan
    Write-Host "  Shared:   postgresql://zeroui:zeroui_dev_only@localhost:5435/zeroui" -ForegroundColor Cyan
}

# ============================================================================
# Ollama model pulls
# ============================================================================

if ($Mode -eq "setup" -and $SetupOllama) {
    Write-Host "`n--- Setting Up Ollama Models ---" -ForegroundColor Yellow
    
    if (-not (Test-Command "ollama")) {
        Write-Error-Custom "Ollama not found. Install it first or use -AutoInstallPrereqs"
        exit 1
    }
    
    if ($PullSmallModels) {
        Write-Warning-Custom "Pulling small models - this can take a long time"
        $smallModels = @("tinyllama:latest", "qwen2.5-coder:14b", "llama3:instruct")
        foreach ($model in $smallModels) {
            Write-Info "Pulling $model..."
            try {
                & ollama pull $model
                if ($LASTEXITCODE -ne 0) {
                    Write-Error-Custom "Failed to pull $model (exit code: $LASTEXITCODE)"
                } else {
                    Write-Success "Pulled $model"
                }
            } catch {
                $errorMsg = $_.Exception.Message
                Write-Error-Custom "Failed to pull ${model}: $errorMsg"
            }
        }
    }
    
    if ($PullBigModels) {
        Write-Warning-Custom "Pulling big models - this can take a very long time"
        Write-Info "Pulling qwen2.5-coder:32b..."
        try {
            & ollama pull qwen2.5-coder:32b
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Failed to pull qwen2.5-coder:32b (exit code: $LASTEXITCODE)"
            } else {
                Write-Success "Pulled qwen2.5-coder:32b"
            }
        } catch {
            Write-Error-Custom "Failed to pull qwen2.5-coder:32b: $_"
        }
    }
}

# ============================================================================
# Unit tests
# ============================================================================

$shouldRunTests = $false
if ($Mode -eq "setup") {
    # Default ON in setup mode unless explicitly disabled
    $shouldRunTests = -not $PSBoundParameters.ContainsKey('RunTests') -or $RunTests
} else {
    # Default OFF in verify mode unless explicitly enabled
    $shouldRunTests = $RunTests
}

if ($shouldRunTests) {
    Write-Host "`n--- Running Unit Tests ---" -ForegroundColor Yellow
    
    # Python tests
    Write-Info "Running Python tests..."
    $pythonExe = Join-Path $RepoRoot "venv\Scripts\python.exe"
    if (Test-Path $pythonExe) {
        try {
            Push-Location $RepoRoot
            & $pythonExe -m pytest -q
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Python tests failed (exit code: $LASTEXITCODE)"
                Pop-Location
                exit 1
            }
            Write-Success "Python tests passed"
            Pop-Location
        } catch {
            Pop-Location
            Write-Error-Custom "Python tests failed: $_"
            exit 1
        }
    } else {
        Write-Error-Custom "Python executable not found: $pythonExe"
        exit 1
    }
    
    # TypeScript tests (root)
    Write-Info "Running TypeScript tests..."
    try {
        Push-Location $RepoRoot
        & npm run build:typescript
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "TypeScript build failed (exit code: $LASTEXITCODE)"
            Pop-Location
            exit 1
        }
        
        & npm run test:typescript
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "TypeScript tests failed (exit code: $LASTEXITCODE)"
            Pop-Location
            exit 1
        }
        Write-Success "TypeScript tests passed"
        Pop-Location
    } catch {
        Pop-Location
        Write-Error-Custom "TypeScript tests failed: $_"
        exit 1
    }
}

# ============================================================================
# Summary
# ============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Bootstrap Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($script:Failures.Count -eq 0) {
    Write-Host "`n✓ Bootstrap completed successfully!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Activate Python venv: .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  2. Review docs/architecture/dev/bootstrap_one_command.md for details" -ForegroundColor White
    Write-Host "  3. Start developing!" -ForegroundColor White
    
    if ($SetupDockerPlanePostgres) {
        Write-Host "`nPostgres containers are running on:" -ForegroundColor Cyan
        Write-Host "  - Tenant: localhost:5433" -ForegroundColor White
        Write-Host "  - Zeroui: localhost:5434" -ForegroundColor White
        Write-Host "  - Shared: localhost:5435" -ForegroundColor White
    }
    
    if ($script:Warnings.Count -gt 0) {
        Write-Host "`nWarnings:" -ForegroundColor Yellow
        $script:Warnings | ForEach-Object { Write-Host "  ⚠ $_" -ForegroundColor Yellow }
    }
    
    exit 0
} else {
    Write-Host "`n✗ Bootstrap completed with errors:" -ForegroundColor Red
    $script:Failures | ForEach-Object { Write-Host "  ✗ $_" -ForegroundColor Red }
    Write-Host "`nPlease fix the errors above and run again." -ForegroundColor Yellow
    exit 1
}

