<#
.SYNOPSIS
  Tenant Cloud Local Bootstrap - Start Tenant Plane services locally

.DESCRIPTION
  Bootstraps and manages the Tenant Cloud plane stack (tenant services + dependencies)
  on a local laptop for testing tenant-side ingestion/adapters/evidence/telemetry flows.

.PARAMETER Mode
  Operation mode: "setup", "start", "stop", "status", "verify"

.PARAMETER AutoInstallPrereqs
  If set, attempts to install missing prerequisites via winget

.PARAMETER StartDockerDeps
  If set, starts Tenant Postgres + Redis via docker compose

.PARAMETER ApplyDbSchemaPack
  If set, runs schema pack apply + schema equivalence verify if scripts exist

.PARAMETER RunUnitTests
  If set, runs tenant-plane unit tests; FAIL if any fail

.PARAMETER SetupOllama
  If set, ensures Ollama is installed

.PARAMETER PullSmallModels
  If set, pulls tinyllama, qwen2.5-coder:14b

.PARAMETER PullBigModels
  If set, pulls qwen2.5-coder:32b

.PARAMETER ZuRoot
  Optional override for ZU_ROOT; otherwise uses .env or defaults to {repo}\.zu

.EXAMPLE
  .\tenant_cloud_bootstrap_local.ps1 -Mode setup -StartDockerDeps

.EXAMPLE
  .\tenant_cloud_bootstrap_local.ps1 -Mode start
#>

[CmdletBinding()]
param(
    [ValidateSet("setup","start","stop","status","verify")]
    [string]$Mode = "setup",
    [switch]$AutoInstallPrereqs,
    [switch]$StartDockerDeps,
    [switch]$ApplyDbSchemaPack,
    [switch]$RunUnitTests,
    [switch]$SetupOllama,
    [switch]$PullSmallModels,
    [switch]$PullBigModels,
    [string]$ZuRoot
)

# Strict error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Track state
$script:Failures = @()
$script:Warnings = @()
$script:ServiceProcesses = @{}
$script:ServicePorts = @{}

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
    param([string]$RepoRoot, [string]$ZuRoot, [hashtable]$AdditionalVars)
    
    $envFile = Join-Path $RepoRoot ".env"
    $lines = @()
    
    if (Test-Path $envFile) {
        $existing = Get-Content $envFile
        $existingKeys = @{}
        foreach ($line in $existing) {
            if ($line -match '^([^=]+)\s*=') {
                $key = $matches[1].Trim()
                $existingKeys[$key] = $true
                $lines += $line
            } else {
                $lines += $line
            }
        }
        
        # Add missing vars
        if (-not $existingKeys.ContainsKey("ZU_ROOT")) {
            $lines += "ZU_ROOT=$ZuRoot"
        }
        foreach ($key in $AdditionalVars.Keys) {
            if (-not $existingKeys.ContainsKey($key)) {
                $lines += "$key=$($AdditionalVars[$key])"
            }
        }
        
        Set-Content -Path $envFile -Value ($lines -join "`n")
    } else {
        # Create new .env file
        $newLines = @("ZU_ROOT=$ZuRoot")
        foreach ($key in $AdditionalVars.Keys) {
            $newLines += "$key=$($AdditionalVars[$key])"
        }
        Set-Content -Path $envFile -Value ($newLines -join "`n")
    }
    Write-Success "Updated .env file"
}

# Discover tenant services
function Discover-TenantServices {
    param([string]$RepoRoot)
    
    $services = @{}
    
    # Integration Adapters (main tenant service)
    $integrationAdaptersPath = Join-Path $RepoRoot "src\cloud_services\client-services\integration-adapters"
    $integrationAdaptersMain = Join-Path $integrationAdaptersPath "main.py"
    if (Test-Path $integrationAdaptersMain) {
        $services["integration-adapters"] = @{
            Name = "integration-adapters"
            Path = $integrationAdaptersPath
            Port = 8010
            HealthPath = "/health"
            MainPy = $integrationAdaptersMain
        }
    }
    
    return $services
}

# ============================================================================
# Main execution
# ============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Tenant Cloud Local Bootstrap" -ForegroundColor Cyan
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

# Discover services
$DiscoveredServices = Discover-TenantServices -RepoRoot $RepoRoot
Write-Info "Discovered $($DiscoveredServices.Count) tenant service(s)"

# ============================================================================
# Prerequisite checks
# ============================================================================

if ($Mode -in @("setup", "start", "verify")) {
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
    
    # Docker (only if StartDockerDeps)
    if ($StartDockerDeps) {
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
                    Write-Error-Custom "Docker is required for -StartDockerDeps. Install from: https://www.docker.com/products/docker-desktop/ or use -AutoInstallPrereqs"
                }
            } else {
                Write-Error-Custom "Docker is required for -StartDockerDeps. Install from: https://www.docker.com/products/docker-desktop/ or use -AutoInstallPrereqs"
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
}

# ============================================================================
# Setup mode: Environment + folder structure
# ============================================================================

if ($Mode -eq "setup") {
    Write-Host "`n--- Setup Mode ---" -ForegroundColor Yellow
    
    # Update .env with tenant DB URLs
    $dbVars = @{
        ZEROUI_TENANT_DB_URL = "postgresql://zeroui:zeroui_dev_only@localhost:5451/zeroui_tenant"
        REDIS_URL = "redis://localhost:6381"
        INTEGRATION_ADAPTERS_DATABASE_URL = "postgresql://zeroui:zeroui_dev_only@localhost:5451/zeroui_tenant"
    }
    Update-EnvFile -RepoRoot $RepoRoot -ZuRoot $ZuRootResolved -AdditionalVars $dbVars
    
    # Create folder structure if needed
    $folderScript = Join-Path $RepoRoot "storage-scripts\tools\create-folder-structure-development.ps1"
    if (Test-Path $folderScript) {
        Write-Info "Creating folder structure..."
        try {
            & $folderScript -ZuRoot $ZuRootResolved
            if ($LASTEXITCODE -ne 0) {
                Write-Warning-Custom "Folder structure creation returned exit code $LASTEXITCODE"
            } else {
                Write-Success "Folder structure created"
            }
        } catch {
            Write-Warning-Custom "Folder structure creation failed: $_"
        }
    } else {
        # Create minimal tenant folders
        Write-Info "Creating minimal tenant folder structure..."
        $tenantBase = Join-Path $ZuRootResolved "tenant"
        $tenantDirs = @(
            (Join-Path $tenantBase "evidence"),
            (Join-Path $tenantBase "telemetry"),
            (Join-Path $tenantBase "adapters"),
            (Join-Path $tenantBase "reporting"),
            (Join-Path $tenantBase "queue")
        )
        foreach ($dir in $tenantDirs) {
            if (-not (Test-Path $dir)) {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
                Write-Success "Created: $dir"
            }
        }
    }
    
    # Create Python venv if missing
    $venvPath = Join-Path $RepoRoot "venv"
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
    }
    
    # Install Python dependencies
    $pythonExe = Join-Path $venvPath "Scripts\python.exe"
    if (Test-Path $pythonExe) {
        Write-Info "Installing Python dependencies..."
        try {
            & $pythonExe -m pip install --upgrade pip --quiet
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Failed to upgrade pip"
                exit 1
            }
            
            $requirementsFile = Join-Path $RepoRoot "requirements.txt"
            if (Test-Path $requirementsFile) {
                & $pythonExe -m pip install -r $requirementsFile --quiet
                if ($LASTEXITCODE -ne 0) {
                    Write-Error-Custom "Failed to install Python dependencies"
                    exit 1
                }
                Write-Success "Python dependencies installed"
            }
            
            & $pythonExe -m pip install -e . --quiet
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Failed to install package in editable mode"
                exit 1
            }
        } catch {
            Write-Error-Custom "Failed to install Python dependencies: $_"
            exit 1
        }
    }
}

# ============================================================================
# Docker dependencies
# ============================================================================

if ($StartDockerDeps) {
    Write-Host "`n--- Starting Docker Dependencies ---" -ForegroundColor Yellow
    
    $composeFile = Join-Path $RepoRoot "infra\local\docker-compose.tenant_cloud.local.yml"
    $envFile = Join-Path $RepoRoot "infra\local\tenant_cloud.local.env"
    
    if (-not (Test-Path $composeFile)) {
        Write-Error-Custom "Docker compose file not found: $composeFile"
        exit 1
    }
    
    if ($Mode -eq "start" -or $Mode -eq "setup") {
        Write-Info "Starting Tenant Postgres and Redis containers..."
        try {
            Push-Location $RepoRoot
            if (Test-Path $envFile) {
                & docker compose -f $composeFile --env-file $envFile up -d
            } else {
                & docker compose -f $composeFile up -d
            }
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Failed to start Docker containers (exit code: $LASTEXITCODE)"
                Pop-Location
                exit 1
            }
            Write-Success "Docker containers started"
            Pop-Location
        } catch {
            Pop-Location
            Write-Error-Custom "Failed to start Docker containers: $_"
            exit 1
        }
        
        # Wait for health
        Write-Info "Waiting for containers to be healthy..."
        $maxWait = 60
        $waited = 0
        $allHealthy = $false
        while ($waited -lt $maxWait) {
            $tenantPg = & docker ps --filter "name=zeroui-tenant-pg" --format "{{.Status}}" 2>&1
            $redis = & docker ps --filter "name=zeroui-redis-tenant" --format "{{.Status}}" 2>&1
            
            if ($tenantPg -match "healthy" -and $redis -match "healthy") {
                $allHealthy = $true
                break
            }
            Start-Sleep -Seconds 2
            $waited += 2
        }
        
        if ($allHealthy) {
            Write-Success "All containers are healthy"
        } else {
            Write-Warning-Custom "Some containers may not be healthy yet. Check with: docker ps"
        }
    } elseif ($Mode -eq "stop") {
        Write-Info "Stopping Docker containers..."
        try {
            Push-Location $RepoRoot
            & docker compose -f $composeFile down
            if ($LASTEXITCODE -ne 0) {
                Write-Warning-Custom "Docker compose down returned exit code $LASTEXITCODE"
            } else {
                Write-Success "Docker containers stopped"
            }
            Pop-Location
        } catch {
            Pop-Location
            Write-Warning-Custom "Failed to stop Docker containers: $_"
        }
    }
}

# ============================================================================
# Apply DB schema pack
# ============================================================================

if ($ApplyDbSchemaPack) {
    Write-Host "`n--- Applying DB Schema Pack ---" -ForegroundColor Yellow
    
    $schemaPackScript = Join-Path $RepoRoot "scripts\db\apply_schema_pack.ps1"
    if (Test-Path $schemaPackScript) {
        Write-Info "Running schema pack apply script..."
        try {
            & $schemaPackScript
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Schema pack apply failed (exit code: $LASTEXITCODE)"
                exit 1
            }
            Write-Success "Schema pack applied"
        } catch {
            Write-Error-Custom "Schema pack apply failed: $_"
            exit 1
        }
    } else {
        Write-Warning-Custom "Schema pack script not found: $schemaPackScript. Skipping by design."
    }
    
    $verifyScript = Join-Path $RepoRoot "scripts\db\verify_schema_equivalence.ps1"
    if (Test-Path $verifyScript) {
        Write-Info "Verifying schema equivalence..."
        try {
            & $verifyScript
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Schema equivalence verification failed (exit code: $LASTEXITCODE)"
                exit 1
            }
            Write-Success "Schema equivalence verified"
        } catch {
            Write-Error-Custom "Schema equivalence verification failed: $_"
            exit 1
        }
    } else {
        Write-Warning-Custom "Schema equivalence script not found: $verifyScript. Skipping by design."
    }
}

# ============================================================================
# Start/Stop/Status services
# ============================================================================

$logDir = Join-Path $env:USERPROFILE ".zeroai\tenant\logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

if ($Mode -eq "start" -or ($Mode -eq "setup" -and $StartDockerDeps)) {
    Write-Host "`n--- Starting Tenant Cloud Services ---" -ForegroundColor Yellow
    
    $venvPath = Join-Path $RepoRoot "venv"
    $pythonExe = Join-Path $venvPath "Scripts\python.exe"
    $uvicornExe = Join-Path $venvPath "Scripts\uvicorn.exe"
    
    if (-not (Test-Path $pythonExe)) {
        Write-Error-Custom "Python venv not found. Run with -Mode setup first."
        exit 1
    }
    
    # Start services
    foreach ($svcName in $DiscoveredServices.Keys) {
        $svc = $DiscoveredServices[$svcName]
        Write-Info "Starting $($svc.Name) on port $($svc.Port)..."
        
        # Check if port is already in use
        $portInUse = Get-NetTCPConnection -LocalPort $svc.Port -ErrorAction SilentlyContinue
        if ($portInUse) {
            Write-Warning-Custom "Port $($svc.Port) is already in use. Skipping $($svc.Name)."
            continue
        }
        
        try {
            Push-Location $svc.Path
            $logFile = Join-Path $logDir "$($svc.Name).log"
            
            # Start uvicorn process
            $process = Start-Process -FilePath $uvicornExe -ArgumentList "main:app", "--host", "0.0.0.0", "--port", $svc.Port.ToString() -PassThru -NoNewWindow -RedirectStandardOutput $logFile -RedirectStandardError $logFile
            
            if ($process) {
                $script:ServiceProcesses[$svc.Name] = $process
                $script:ServicePorts[$svc.Name] = $svc.Port
                Write-Success "$($svc.Name) started (PID: $($process.Id), Port: $($svc.Port))"
                
                # Wait for health check
                Start-Sleep -Seconds 2
                try {
                    $healthUrl = "http://localhost:$($svc.Port)$($svc.HealthPath)"
                    $response = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 5 -ErrorAction SilentlyContinue
                    if ($response.StatusCode -eq 200) {
                        Write-Success "$($svc.Name) health check passed"
                    }
                } catch {
                    Write-Warning-Custom "$($svc.Name) health check not yet available (may need more time)"
                }
            } else {
                Write-Error-Custom "Failed to start $($svc.Name)"
            }
            Pop-Location
        } catch {
            Pop-Location
            Write-Error-Custom "Failed to start $($svc.Name): $_"
        }
    }
    
    Write-Info "Service logs: $logDir"
    
} elseif ($Mode -eq "stop") {
    Write-Host "`n--- Stopping Tenant Cloud Services ---" -ForegroundColor Yellow
    
    # Load saved PIDs if available
    $pidFile = Join-Path $logDir "service_pids.txt"
    if (Test-Path $pidFile) {
        $pids = Get-Content $pidFile | ForEach-Object { [int]$_ }
        foreach ($pid in $pids) {
            try {
                $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($proc) {
                    Stop-Process -Id $pid -Force
                    Write-Success "Stopped process $pid"
                }
            } catch {
                Write-Warning-Custom "Could not stop process $pid: $_"
            }
        }
        Remove-Item $pidFile -ErrorAction SilentlyContinue
    }
    
    # Also try to kill by port
    foreach ($svcName in $DiscoveredServices.Keys) {
        $svc = $DiscoveredServices[$svcName]
        $conn = Get-NetTCPConnection -LocalPort $svc.Port -ErrorAction SilentlyContinue
        if ($conn) {
            $pid = $conn.OwningProcess
            try {
                Stop-Process -Id $pid -Force
                Write-Success "Stopped service on port $($svc.Port) (PID: $pid)"
            } catch {
                Write-Warning-Custom "Could not stop service on port $($svc.Port)"
            }
        }
    }
    
} elseif ($Mode -eq "status") {
    Write-Host "`n--- Service Status ---" -ForegroundColor Yellow
    
    Write-Info "Docker containers:"
    & docker ps --filter "name=zeroui-tenant" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Info "`nTenant services:"
    foreach ($svcName in $DiscoveredServices.Keys) {
        $svc = $DiscoveredServices[$svcName]
        $conn = Get-NetTCPConnection -LocalPort $svc.Port -ErrorAction SilentlyContinue
        if ($conn) {
            try {
                $healthUrl = "http://localhost:$($svc.Port)$($svc.HealthPath)"
                $response = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 2 -ErrorAction SilentlyContinue
                Write-Success "$($svc.Name): RUNNING (port $($svc.Port), health: OK)"
            } catch {
                Write-Warning-Custom "$($svc.Name): RUNNING (port $($svc.Port), health: FAILED)"
            }
        } else {
            Write-Host "$($svc.Name): STOPPED" -ForegroundColor Gray
        }
    }
}

# ============================================================================
# Unit tests
# ============================================================================

if ($RunUnitTests) {
    Write-Host "`n--- Running Tenant Unit Tests ---" -ForegroundColor Yellow
    
    $venvPath = Join-Path $RepoRoot "venv"
    $pythonExe = Join-Path $venvPath "Scripts\python.exe"
    
    if (Test-Path $pythonExe) {
        Write-Info "Running tenant-plane unit tests..."
        try {
            Push-Location $RepoRoot
            # Run tests for integration-adapters (tenant service)
            $testPath = "tests\cloud_services\client_services\integration_adapters"
            if (Test-Path $testPath) {
                & $pythonExe -m pytest -q $testPath -v
            } else {
                # Fallback: try alternative path
                $testPath = "src\cloud_services\client-services\integration-adapters\tests"
                if (Test-Path $testPath) {
                    & $pythonExe -m pytest -q $testPath -v
                } else {
                    Write-Warning-Custom "Tenant test directory not found. Skipping tests."
                    Pop-Location
                    exit 0
                }
            }
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Custom "Tenant unit tests failed (exit code: $LASTEXITCODE)"
                Pop-Location
                exit 1
            }
            Write-Success "ALL TENANT TESTS PASSED"
            Pop-Location
        } catch {
            Pop-Location
            Write-Error-Custom "Tenant unit tests failed: $_"
            exit 1
        }
    } else {
        Write-Error-Custom "Python venv not found. Run with -Mode setup first."
        exit 1
    }
}

# ============================================================================
# Ollama setup
# ============================================================================

if ($SetupOllama) {
    Write-Host "`n--- Setting Up Ollama Models ---" -ForegroundColor Yellow
    
    if (-not (Test-Command "ollama")) {
        Write-Error-Custom "Ollama not found. Install it first or use -AutoInstallPrereqs"
        exit 1
    }
    
    if ($PullSmallModels) {
        Write-Warning-Custom "Pulling small models - this can take a long time"
        $smallModels = @("tinyllama:latest", "qwen2.5-coder:14b")
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
    
    if ($PullSmallModels -or $PullBigModels) {
        Write-Info "Installed Ollama models:"
        & ollama list
    }
}

# ============================================================================
# Summary
# ============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Bootstrap Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nRepository: $RepoRoot" -ForegroundColor White
Write-Host "ZU_ROOT: $ZuRootResolved" -ForegroundColor White

if ($StartDockerDeps) {
    Write-Host "`nDocker Services:" -ForegroundColor Cyan
    & docker ps --filter "name=zeroui-tenant" --format "  {{.Names}}: {{.Status}}" 2>&1 | ForEach-Object { Write-Host $_ -ForegroundColor White }
    
    Write-Host "`nDatabase URLs:" -ForegroundColor Cyan
    Write-Host "  Tenant: postgresql://zeroui:zeroui_dev_only@localhost:5451/zeroui_tenant" -ForegroundColor White
    Write-Host "  Redis:  redis://localhost:6381" -ForegroundColor White
}

if ($Mode -eq "start" -or ($Mode -eq "setup" -and $StartDockerDeps)) {
    Write-Host "`nTenant Services:" -ForegroundColor Cyan
    foreach ($svcName in $DiscoveredServices.Keys) {
        $svc = $DiscoveredServices[$svcName]
        $conn = Get-NetTCPConnection -LocalPort $svc.Port -ErrorAction SilentlyContinue
        if ($conn) {
            Write-Host "  $($svc.Name): http://localhost:$($svc.Port)$($svc.HealthPath)" -ForegroundColor White
        }
    }
}

if ($RunUnitTests) {
    Write-Host "`nUnit Tests: Executed - ALL TENANT TESTS PASSED" -ForegroundColor Green
} elseif ($Mode -eq "setup") {
    Write-Host "`nUnit Tests: Not executed (use -RunUnitTests to run)" -ForegroundColor Gray
}

if ($script:Warnings.Count -gt 0) {
    Write-Host "`nWarnings:" -ForegroundColor Yellow
    $script:Warnings | ForEach-Object { Write-Host "  ⚠ $_" -ForegroundColor Yellow }
}

if ($script:Failures.Count -eq 0) {
    Write-Host "`n✓ Bootstrap completed successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n✗ Bootstrap completed with errors:" -ForegroundColor Red
    $script:Failures | ForEach-Object { Write-Host "  ✗ $_" -ForegroundColor Red }
    exit 1
}

