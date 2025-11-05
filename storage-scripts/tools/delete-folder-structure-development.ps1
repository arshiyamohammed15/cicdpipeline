<#
.SYNOPSIS
  ZeroUI Folder Structure Deletion Script - Development Environment

.DESCRIPTION
  Deletes the folder structure for development environment created by create-folder-structure-development.ps1.
  Deletes IDE plane, tenant, product, and shared planes under {ZU_ROOT}/development.

.PARAMETER ZuRoot
  Base path for ZU_ROOT. If not provided, constructed from Drive and ProductName, or uses $env:ZU_ROOT environment variable.

.PARAMETER Drive
  Drive letter for ZU_ROOT path. Default: "D". Ignored if -ZuRoot is specified.

.PARAMETER ProductName
  Product name for ZU_ROOT path. Default: "ZeroUI". Ignored if -ZuRoot is specified.

.PARAMETER Force
  If specified, skips confirmation prompt. Use with caution.

.PARAMETER WhatIf
  If specified, shows what would be deleted without actually deleting.

.EXAMPLE
  .\delete-folder-structure-development.ps1
  .\delete-folder-structure-development.ps1 -Drive "D" -ProductName "ZeroUI"
  .\delete-folder-structure-development.ps1 -ZuRoot "D:\ZeroUI"
  .\delete-folder-structure-development.ps1 -ZuRoot "D:\ZeroUI" -Force
  .\delete-folder-structure-development.ps1 -ZuRoot "D:\ZeroUI" -WhatIf

.NOTES
  Version: 2.0
  Based on: folder-business-rules.md
  WARNING: This script will delete all folders under the development environment.
  It will NOT delete the ZU_ROOT directory itself, only the development environment folder.
#>

[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [string]$ZuRoot,
    [string]$Drive = "D",
    [string]$ProductName = "ZeroUI",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Function to delete directory if it exists
function Remove-FolderStructure {
    param(
        [string]$Path,
        [string]$Description = ""
    )
    
    if(Test-Path $Path) {
        if($WhatIfPreference) {
            Write-Host "[WHATIF] Would delete: $Path" -ForegroundColor Yellow
            if($Description) {
                Write-Verbose "  Description: $Description"
            }
            return $true
        }
        
        try {
            if($PSCmdlet.ShouldProcess($Path, "Delete folder")) {
                Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
                Write-Host "Deleted: $Path" -ForegroundColor Green
                if($Description) {
                    Write-Verbose "  Description: $Description"
                }
                return $true
            }
        } catch {
            Write-Error "Failed to delete: $Path - $_"
            return $false
        }
    } else {
        Write-Verbose "Does not exist: $Path"
        return $true
    }
}

# Function to delete IDE Plane
function Remove-IDEFolderStructure {
    param(
        [string]$BasePath,
        [ref]$Errors,
        [ref]$DeletedCount
    )
    
    $ideBase = Join-Path $BasePath "ide"
    
    # Delete ide/tmp
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $ideBase "tmp") -Description "Temporary; RFC stamping")) { "ide/tmp" } else { $null; $DeletedCount.Value++ }
    
    # Delete ide/fingerprint
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $ideBase "fingerprint") -Description "Non-secret device fingerprint")) { "ide/fingerprint" } else { $null; $DeletedCount.Value++ }
    
    # Delete ide/llm
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $ideBase "llm") -Description "LLM prompts, tools, adapters, cache")) { "ide/llm" } else { $null; $DeletedCount.Value++ }
    
    # Delete ide/db
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $ideBase "db") -Description "SQLite mirror, raw JSON")) { "ide/db" } else { $null; $DeletedCount.Value++ }
    
    # Delete ide/logs
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $ideBase "logs") -Description "Log files")) { "ide/logs" } else { $null; $DeletedCount.Value++ }
    
    # Delete ide/queue
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $ideBase "queue") -Description "Envelope refs only")) { "ide/queue" } else { $null; $DeletedCount.Value++ }
    
    # Delete ide/config
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $ideBase "config") -Description "Non-secret consent snapshots and configuration")) { "ide/config" } else { $null; $DeletedCount.Value++ }
    
    # Delete ide/policy/trust/pubkeys
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path (Join-Path $ideBase "policy") "trust") "pubkeys") -Description "Public keys only")) { "ide/policy/trust/pubkeys" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $ideBase "policy") "trust") -Description "Policy trust")) { "ide/policy/trust" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $ideBase "policy") -Description "Signed snapshots + current pointer, cache")) { "ide/policy" } else { $null; $DeletedCount.Value++ }
    
    # Delete ide/receipts
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $ideBase "receipts") -Description "Append-only signed JSONL receipts")) { "ide/receipts" } else { $null; $DeletedCount.Value++ }
    
    # Delete ide base
    $Errors.Value += if(-not (Remove-FolderStructure -Path $ideBase -Description "IDE plane base")) { "ide" } else { $null; $DeletedCount.Value++ }
}

# Function to delete Tenant Plane
function Remove-TenantFolderStructure {
    param(
        [string]$BasePath,
        [ref]$Errors,
        [ref]$DeletedCount
    )
    
    $tenantBase = Join-Path $BasePath "tenant"
    
    # Delete tenant/meta/schema (deprecated alias, if exists)
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $tenantBase "meta") "schema") -Description "Deprecated legacy alias")) { "tenant/meta/schema" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $tenantBase "meta") -Description "Meta folder")) { "tenant/meta" } else { $null; $DeletedCount.Value++ }
    
    # Delete tenant/policy/trust/pubkeys
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path (Join-Path $tenantBase "policy") "trust") "pubkeys") -Description "Public keys only")) { "tenant/policy/trust/pubkeys" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $tenantBase "policy") "trust") -Description "Policy trust")) { "tenant/policy/trust" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $tenantBase "policy") "snapshots") -Description "Signed snapshots")) { "tenant/policy/snapshots" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $tenantBase "policy") -Description "Policy folder")) { "tenant/policy" } else { $null; $DeletedCount.Value++ }
    
    # Delete tenant/reporting/marts
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $tenantBase "reporting") "marts") -Description "Analytics marts")) { "tenant/reporting/marts" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $tenantBase "reporting") -Description "Reporting folder")) { "tenant/reporting" } else { $null; $DeletedCount.Value++ }
    
    # Delete tenant/adapters
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $tenantBase "adapters") -Description "Webhooks and gateway logs")) { "tenant/adapters" } else { $null; $DeletedCount.Value++ }
    
    # Delete tenant/telemetry
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $tenantBase "telemetry") -Description "Unified observability pattern")) { "tenant/telemetry" } else { $null; $DeletedCount.Value++ }
    
    # Delete tenant/ingest
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $tenantBase "ingest") -Description "RFC fallback")) { "tenant/ingest" } else { $null; $DeletedCount.Value++ }
    
    # Delete tenant/evidence
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $tenantBase "evidence") "watermarks") -Description "Per-consumer watermarks")) { "tenant/evidence/watermarks" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $tenantBase "evidence") "dlq") -Description "Dead letter queue")) { "tenant/evidence/dlq" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $tenantBase "evidence") "data") -Description "Merged receipts, manifests, checksums")) { "tenant/evidence/data" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $tenantBase "evidence") -Description "Evidence folder")) { "tenant/evidence" } else { $null; $DeletedCount.Value++ }
    
    # Delete tenant base
    $Errors.Value += if(-not (Remove-FolderStructure -Path $tenantBase -Description "Tenant plane base")) { "tenant" } else { $null; $DeletedCount.Value++ }
}

# Function to delete Product Plane
function Remove-ProductFolderStructure {
    param(
        [string]$BasePath,
        [ref]$Errors,
        [ref]$DeletedCount
    )
    
    $productBase = Join-Path $BasePath "product"
    
    # Delete product/policy/trust/pubkeys
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path (Join-Path $productBase "policy") "trust") "pubkeys") -Description "Public keys")) { "product/policy/trust/pubkeys" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $productBase "policy") "trust") -Description "Policy trust")) { "product/policy/trust" } else { $null; $DeletedCount.Value++ }
    
    # Delete product/telemetry
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $productBase "telemetry") -Description "Unified observability pattern")) { "product/telemetry" } else { $null; $DeletedCount.Value++ }
    
    # Delete product/adapters
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $productBase "adapters") -Description "Gateway logs")) { "product/adapters" } else { $null; $DeletedCount.Value++ }
    
    # Delete product/reporting/tenants
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $productBase "reporting") "tenants") -Description "Tenant aggregates")) { "product/reporting/tenants" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $productBase "reporting") -Description "Reporting folder")) { "product/reporting" } else { $null; $DeletedCount.Value++ }
    
    # Delete product/evidence/watermarks
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $productBase "evidence") "watermarks") -Description "Per-consumer watermarks")) { "product/evidence/watermarks" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $productBase "evidence") -Description "Evidence folder")) { "product/evidence" } else { $null; $DeletedCount.Value++ }
    
    # Delete product/policy/registry
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path (Join-Path $productBase "policy") "registry") "revocations") -Description "Policy revocations")) { "product/policy/registry/revocations" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path (Join-Path $productBase "policy") "registry") "templates") -Description "Policy templates")) { "product/policy/registry/templates" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path (Join-Path $productBase "policy") "registry") "releases") -Description "Policy releases")) { "product/policy/registry/releases" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $productBase "policy") "registry") -Description "Policy registry")) { "product/policy/registry" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $productBase "policy") -Description "Policy folder")) { "product/policy" } else { $null; $DeletedCount.Value++ }
    
    # Delete product base
    $Errors.Value += if(-not (Remove-FolderStructure -Path $productBase -Description "Product plane base")) { "product" } else { $null; $DeletedCount.Value++ }
}

# Function to delete Shared Plane
function Remove-SharedFolderStructure {
    param(
        [string]$BasePath,
        [ref]$Errors,
        [ref]$DeletedCount
    )
    
    $sharedBase = Join-Path $BasePath "shared"
    
    # Delete shared/llm subfolders
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $sharedBase "llm") "tools") -Description "LLM tools")) { "shared/llm/tools" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $sharedBase "llm") "routing") -Description "LLM routing")) { "shared/llm/routing" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $sharedBase "llm") "guardrails") -Description "LLM guardrails")) { "shared/llm/guardrails" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $sharedBase "llm") -Description "LLM folder")) { "shared/llm" } else { $null; $DeletedCount.Value++ }
    
    # Delete shared/governance subfolders
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $sharedBase "governance") "attestations") -Description "Governance attestations")) { "shared/governance/attestations" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $sharedBase "governance") "controls") -Description "Governance controls")) { "shared/governance/controls" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $sharedBase "governance") -Description "Governance folder")) { "shared/governance" } else { $null; $DeletedCount.Value++ }
    
    # Delete shared/bi-lake
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path (Join-Path $sharedBase "bi-lake") "curated") "zero-ui") -Description "BI lake curated data")) { "shared/bi-lake/curated/zero-ui" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $sharedBase "bi-lake") "curated") -Description "BI lake curated")) { "shared/bi-lake/curated" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $sharedBase "bi-lake") -Description "BI lake")) { "shared/bi-lake" } else { $null; $DeletedCount.Value++ }
    
    # Delete shared/siem
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path (Join-Path $sharedBase "siem") "detections") -Description "SIEM detections")) { "shared/siem/detections" } else { $null; $DeletedCount.Value++ }
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $sharedBase "siem") -Description "SIEM folder")) { "shared/siem" } else { $null; $DeletedCount.Value++ }
    
    # Delete shared/telemetry
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $sharedBase "telemetry") -Description "Unified observability pattern")) { "shared/telemetry" } else { $null; $DeletedCount.Value++ }
    
    # Delete shared/pki
    $Errors.Value += if(-not (Remove-FolderStructure -Path (Join-Path $sharedBase "pki") -Description "All PKI files")) { "shared/pki" } else { $null; $DeletedCount.Value++ }
    
    # Delete shared base
    $Errors.Value += if(-not (Remove-FolderStructure -Path $sharedBase -Description "Shared plane base")) { "shared" } else { $null; $DeletedCount.Value++ }
}

# Determine ZU_ROOT
if(-not $ZuRoot) {
    if($env:ZU_ROOT) {
        $ZuRoot = $env:ZU_ROOT
        Write-Host "Using ZU_ROOT from environment: $ZuRoot" -ForegroundColor Cyan
    } else {
        # Construct ZU_ROOT from Drive and ProductName
        $ZuRoot = "${Drive}:\${ProductName}"
        Write-Host "Constructed ZU_ROOT from Drive and ProductName: $ZuRoot" -ForegroundColor Cyan
        Write-Host "  Drive: $Drive" -ForegroundColor Cyan
        Write-Host "  ProductName: $ProductName" -ForegroundColor Cyan
    }
}

# Check if ZU_ROOT exists - if not, exit gracefully (nothing to delete)
if(-not (Test-Path $ZuRoot)) {
    Write-Host "ZU_ROOT does not exist: $ZuRoot" -ForegroundColor Yellow
    Write-Host "No folders to delete. Exiting gracefully." -ForegroundColor Yellow
    exit 0
}

Write-Host "`nDeleting ZeroUI folder structure for development environment under: $ZuRoot" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

if($WhatIf) {
    Write-Host "WHATIF MODE: No actual deletions will be performed.`n" -ForegroundColor Yellow
} elseif(-not $Force) {
    Write-Host "WARNING: This will delete all folders under the development environment." -ForegroundColor Red
    Write-Host "ZU_ROOT directory itself will NOT be deleted.`n" -ForegroundColor Yellow
    $response = Read-Host "Are you sure you want to continue? (yes/no)"
    if($response -ne "yes" -and $response -ne "y") {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        exit 0
    }
    Write-Host ""
}

$errors = @()
$deletedCount = 0

# ============================================================================
# Delete development environment
# ============================================================================
$envPath = Join-Path $ZuRoot "development"
if(-not (Test-Path $envPath)) {
    Write-Host "Development environment folder does not exist: $envPath" -ForegroundColor Yellow
    exit 0
}

Write-Host "Deleting development environment folders..." -ForegroundColor Yellow

# IDE plane only under development
Write-Host "  Deleting IDE Plane..." -ForegroundColor Cyan
Remove-IDEFolderStructure -BasePath $envPath -Errors ([ref]$errors) -DeletedCount ([ref]$deletedCount)

# Delete Tenant, Product, and Shared planes
Write-Host "  Deleting Tenant, Product, and Shared planes..." -ForegroundColor Cyan
Remove-TenantFolderStructure -BasePath $envPath -Errors ([ref]$errors) -DeletedCount ([ref]$deletedCount)
Remove-ProductFolderStructure -BasePath $envPath -Errors ([ref]$errors) -DeletedCount ([ref]$deletedCount)
Remove-SharedFolderStructure -BasePath $envPath -Errors ([ref]$errors) -DeletedCount ([ref]$deletedCount)

# Delete environment folder
$errors += if(-not (Remove-FolderStructure -Path $envPath -Description "development environment")) { "development" } else { $null; $deletedCount++ }

# ============================================================================
# Summary
# ============================================================================
Write-Host "`n==========================================" -ForegroundColor Cyan
$errorCount = ($errors | Where-Object { $_ -ne $null }).Count
if($errorCount -eq 0) {
    if($WhatIf) {
        Write-Host "WhatIf completed. No actual deletions performed." -ForegroundColor Yellow
    } else {
        Write-Host "Folder structure deleted successfully!" -ForegroundColor Green
        Write-Host "Folders deleted: $deletedCount" -ForegroundColor Cyan
        Write-Host "Environment: development" -ForegroundColor Cyan
        Write-Host "ZU_ROOT preserved: $ZuRoot" -ForegroundColor Cyan
    }
    exit 0
} else {
    Write-Host "Folder structure deletion completed with $errorCount error(s)." -ForegroundColor Yellow
    if(-not $WhatIfPreference) {
        Write-Host "Failed paths:" -ForegroundColor Red
        $errors | Where-Object { $_ -ne $null } | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    }
    exit 1
}

