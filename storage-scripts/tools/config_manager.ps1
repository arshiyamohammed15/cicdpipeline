<#
.SYNOPSIS
  ZeroUI Environment Configuration Manager

.DESCRIPTION
  Manages environment configurations for ZeroUI storage architecture.
  Supports multiple environments and deployment types (on-prem, cloud).

.PARAMETER Action
  Action to perform: 'list', 'validate', 'generate', 'show'

.PARAMETER Env
  Environment name (development, integration, staging, production)

.PARAMETER DeploymentType
  Deployment type (local, onprem, cloud)

.PARAMETER ConfigFile
  Path to configuration file

.PARAMETER ZuRoot
  Base path for ZU_ROOT generation (used with generate action)

.EXAMPLE
  .\config_manager.ps1 -Action list
  .\config_manager.ps1 -Action validate -Env integration -DeploymentType cloud
  .\config_manager.ps1 -Action generate -Env staging -DeploymentType onprem -ZuRoot "\\server\ZeroUI"
  .\config_manager.ps1 -Action show -Env production

#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('list', 'validate', 'generate', 'show')]
    [string]$Action,
    
    [string]$Env,
    [string]$DeploymentType,
    [string]$ConfigFile,
    [string]$ZuRoot
)

function Show-EnvironmentList {
    param([object]$Config)
    
    Write-Host "Available Environments:" -ForegroundColor Cyan
    foreach($envName in $Config.environments.PSObject.Properties.Name) {
        $env = $Config.environments.$envName
        Write-Host "  $envName" -ForegroundColor Yellow
        Write-Host "    Description: $($env.description)"
        $deployTypes = $env.deployment_types.PSObject.Properties.Name -join ', '
        Write-Host "    Deployment Types: $deployTypes"
    }
}

function Validate-EnvironmentConfig {
    param(
        [string]$Env,
        [string]$DeploymentType,
        [object]$Config
    )
    
    $errors = @()
    
    if(-not $Config.environments.$Env) {
        $errors += "Environment '$Env' not found"
    } else {
        if(-not $Config.environments.$Env.deployment_types.$DeploymentType) {
            $errors += "Deployment type '$DeploymentType' not found for environment '$Env'"
        } else {
            $deployConfig = $Config.environments.$Env.deployment_types.$DeploymentType
            $backend = $deployConfig.backend
            
            if(-not $Config.storage_backends.$backend) {
                $errors += "Backend '$backend' referenced but not defined in storage_backends"
            }
        }
    }
    
    if($errors) {
        Write-Host "Validation Errors:" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        return $false
    }
    
    Write-Host "Configuration valid" -ForegroundColor Green
    return $true
}

function Generate-ZuRoot {
    param(
        [string]$Env,
        [string]$DeploymentType,
        [object]$Config,
        [string]$ZuRoot
    )
    
    $envConfig = $Config.environments.$Env.deployment_types.$DeploymentType
    $pattern = $envConfig.zu_root_pattern
    
    # Replace placeholders
    if($pattern -match '\{base_path\}') {
        if(-not $ZuRoot) {
            Write-Host "Error: -ZuRoot required when using base_path pattern" -ForegroundColor Red
            return $null
        }
        $zuRootGenerated = $pattern -replace '\{base_path\}', $ZuRoot
        # Normalize path separators for Windows
        if($zuRootGenerated -match '^[A-Z]:\\|^\\\\') {
            $zuRootGenerated = $zuRootGenerated -replace '/', '\'
        }
    } elseif($pattern -match '\{bucket\}') {
        $bucketName = $envConfig.bucket_config.bucket_name
        if(-not $bucketName) {
            Write-Host "Error: bucket_name not configured for cloud deployment" -ForegroundColor Red
            return $null
        }
        $zuRootGenerated = $pattern -replace '\{bucket\}', $bucketName
    } else {
        $zuRootGenerated = $pattern
    }
    
    return $zuRootGenerated
}

# Determine config file path if not provided
if(-not $ConfigFile) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    if(-not $scriptDir) {
        $scriptDir = Split-Path -Parent $PSCommandPath
    }
    if(-not $scriptDir) {
        $scriptDir = $PSScriptRoot
    }
    if($scriptDir) {
        $ConfigFile = Join-Path $scriptDir "..\config\environments.json"
        $ConfigFile = Resolve-Path $ConfigFile -ErrorAction SilentlyContinue
        if($ConfigFile) {
            $ConfigFile = $ConfigFile.Path
        }
    }
    if(-not $ConfigFile) {
        # Fallback: try relative to current directory
        $ConfigFile = "storage-scripts\config\environments.json"
    }
}

# Load configuration
if(-not (Test-Path $ConfigFile)) {
    Write-Host "Error: Configuration file not found: $ConfigFile" -ForegroundColor Red
    exit 1
}

try {
    $config = Get-Content $ConfigFile -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
} catch {
    Write-Host "Error: Failed to parse configuration file: $_" -ForegroundColor Red
    exit 1
}

# Main execution
switch($Action) {
    'list' {
        Show-EnvironmentList -Config $config
    }
    'validate' {
        if(-not $Env -or -not $DeploymentType) {
            Write-Host "Error: -Env and -DeploymentType required for validate action" -ForegroundColor Red
            exit 1
        }
        $valid = Validate-EnvironmentConfig -Env $Env -DeploymentType $DeploymentType -Config $config
        exit $(if($valid) { 0 } else { 1 })
    }
    'generate' {
        if(-not $Env -or -not $DeploymentType) {
            Write-Host "Error: -Env and -DeploymentType required for generate action" -ForegroundColor Red
            exit 1
        }
        $generated = Generate-ZuRoot -Env $Env -DeploymentType $DeploymentType -Config $config -ZuRoot $ZuRoot
        if($generated) {
            Write-Host "Generated ZU_ROOT: $generated" -ForegroundColor Green
        } else {
            exit 1
        }
    }
    'show' {
        if(-not $Env) {
            Write-Host "Error: -Env required for show action" -ForegroundColor Red
            exit 1
        }
        if(-not $config.environments.$Env) {
            Write-Host "Error: Environment '$Env' not found" -ForegroundColor Red
            exit 1
        }
        $config.environments.$Env | ConvertTo-Json -Depth 10
    }
}

