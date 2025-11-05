<#
.SYNOPSIS
  ZeroUI Folder Structure Creator - Production Environment

.DESCRIPTION
  Creates the folder structure for production environment as per folder-business-rules.md v2.0.
  Creates tenant, product, and shared planes under {ZU_ROOT}/production.

.PARAMETER ZuRoot
  Base path for ZU_ROOT. If not provided, constructed from Drive and ProductName, or uses $env:ZU_ROOT environment variable.

.PARAMETER Drive
  Drive letter for ZU_ROOT path. Default: "D". Ignored if -ZuRoot is specified.

.PARAMETER ProductName
  Product name for ZU_ROOT path. Default: "ZeroUI". Ignored if -ZuRoot is specified.

.PARAMETER CompatAliases
  If specified, creates deprecated alias folders (e.g., meta/schema/).

.PARAMETER Consumer
  Consumer ID for creating watermark folders (created on-demand, but parent folders are created).

.EXAMPLE
  .\create-folder-structure-production.ps1
  .\create-folder-structure-production.ps1 -Drive "D" -ProductName "ZeroUI"
  .\create-folder-structure-production.ps1 -ZuRoot "D:\ZeroUI"
  .\create-folder-structure-production.ps1 -ZuRoot "D:\ZeroUI" -CompatAliases

.NOTES
  Version: 2.0
  Based on: folder-business-rules.md
  Lazy creation: Only parent folders are created; subfolders like receipts/{repo-id}/ are created on-demand.
#>

[CmdletBinding()]
param(
    [string]$ZuRoot,
    [string]$Drive = "D",
    [string]$ProductName = "ZeroUI",
    [switch]$CompatAliases,
    [string]$Consumer
)

# Function to create directory if it doesn't exist
function New-FolderStructure {
    param(
        [string]$Path,
        [string]$Description = ""
    )
    
    if(-not (Test-Path $Path)) {
        try {
            New-Item -ItemType Directory -Path $Path -Force | Out-Null
            Write-Host "Created: $Path" -ForegroundColor Green
            if($Description) {
                Write-Verbose "  Description: $Description"
            }
        } catch {
            Write-Error "Failed to create: $Path - $_"
            return $false
        }
    } else {
        Write-Verbose "Already exists: $Path"
    }
    return $true
}

# Function to create Tenant Plane
function New-TenantFolderStructure {
    param(
        [string]$BasePath,
        [switch]$CompatAliases,
        [ref]$Errors
    )
    
    $tenantBase = Join-Path $BasePath "tenant"
    $Errors.Value += if(-not (New-FolderStructure -Path $tenantBase)) { "tenant" }
    
    # evidence/ - Merged receipts, manifests, checksums
    $evidencePath = Join-Path $tenantBase "evidence"
    $Errors.Value += if(-not (New-FolderStructure -Path $evidencePath)) { "tenant/evidence" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $evidencePath "data") -Description "Merged receipts, manifests, checksums")) { "tenant/evidence/data" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $evidencePath "dlq") -Description "Dead letter queue")) { "tenant/evidence/dlq" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $evidencePath "watermarks") -Description "Per-consumer watermarks")) { "tenant/evidence/watermarks" }
    
    # ingest/ - RFC fallback
    $ingestPath = Join-Path $tenantBase "ingest"
    $Errors.Value += if(-not (New-FolderStructure -Path $ingestPath)) { "tenant/ingest" }
    
    # telemetry/ - Unified observability pattern
    $telemetryPath = Join-Path $tenantBase "telemetry"
    $Errors.Value += if(-not (New-FolderStructure -Path $telemetryPath -Description "Unified observability pattern")) { "tenant/telemetry" }
    
    # adapters/ - Webhooks and gateway logs
    $adaptersPath = Join-Path $tenantBase "adapters"
    $Errors.Value += if(-not (New-FolderStructure -Path $adaptersPath -Description "Webhooks and gateway logs")) { "tenant/adapters" }
    
    # reporting/ - Analytics marts
    $reportingPath = Join-Path $tenantBase "reporting"
    $Errors.Value += if(-not (New-FolderStructure -Path $reportingPath)) { "tenant/reporting" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $reportingPath "marts") -Description "Analytics marts")) { "tenant/reporting/marts" }
    
    # policy/ - Signed snapshots and public keys
    $tenantPolicyPath = Join-Path $tenantBase "policy"
    $Errors.Value += if(-not (New-FolderStructure -Path $tenantPolicyPath)) { "tenant/policy" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $tenantPolicyPath "snapshots") -Description "Signed snapshots")) { "tenant/policy/snapshots" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $tenantPolicyPath "trust")) -or
                         -not (New-FolderStructure -Path (Join-Path (Join-Path $tenantPolicyPath "trust") "pubkeys") -Description "Public keys only")) { "tenant/policy/trust/pubkeys" }
    
    # meta/schema/ - Deprecated alias (only with -CompatAliases)
    if($CompatAliases) {
        $metaPath = Join-Path $tenantBase "meta"
        $Errors.Value += if(-not (New-FolderStructure -Path $metaPath)) { "tenant/meta" }
        $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $metaPath "schema") -Description "Deprecated legacy alias")) { "tenant/meta/schema" }
    }
}

# Function to create Product Plane
function New-ProductFolderStructure {
    param(
        [string]$BasePath,
        [ref]$Errors
    )
    
    $productBase = Join-Path $BasePath "product"
    $Errors.Value += if(-not (New-FolderStructure -Path $productBase)) { "product" }
    
    # policy/registry/ - Unified policy structure
    $productPolicyPath = Join-Path $productBase "policy"
    $Errors.Value += if(-not (New-FolderStructure -Path $productPolicyPath)) { "product/policy" }
    $registryPath = Join-Path $productPolicyPath "registry"
    $Errors.Value += if(-not (New-FolderStructure -Path $registryPath -Description "Unified policy structure")) { "product/policy/registry" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $registryPath "releases") -Description "Policy releases")) { "product/policy/registry/releases" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $registryPath "templates") -Description "Policy templates")) { "product/policy/registry/templates" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $registryPath "revocations") -Description "Policy revocations")) { "product/policy/registry/revocations" }
    
    # evidence/watermarks/ - Per-consumer watermarks
    $productEvidencePath = Join-Path $productBase "evidence"
    $Errors.Value += if(-not (New-FolderStructure -Path $productEvidencePath)) { "product/evidence" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $productEvidencePath "watermarks") -Description "Per-consumer watermarks")) { "product/evidence/watermarks" }
    
    # reporting/tenants/ - Tenant aggregates
    $productReportingPath = Join-Path $productBase "reporting"
    $Errors.Value += if(-not (New-FolderStructure -Path $productReportingPath)) { "product/reporting" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $productReportingPath "tenants") -Description "Tenant aggregates")) { "product/reporting/tenants" }
    
    # adapters/gateway-logs/ - Gateway diagnostics
    $productAdaptersPath = Join-Path $productBase "adapters"
    $Errors.Value += if(-not (New-FolderStructure -Path $productAdaptersPath -Description "Gateway logs")) { "product/adapters" }
    
    # telemetry/ - Unified observability pattern
    $productTelemetryPath = Join-Path $productBase "telemetry"
    $Errors.Value += if(-not (New-FolderStructure -Path $productTelemetryPath -Description "Unified observability pattern")) { "product/telemetry" }
    
    # policy/trust/pubkeys/ - Public keys (merged with policy structure)
    $productPolicyTrustPath = Join-Path $productPolicyPath "trust"
    $Errors.Value += if(-not (New-FolderStructure -Path $productPolicyTrustPath)) { "product/policy/trust" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $productPolicyTrustPath "pubkeys") -Description "Public keys")) { "product/policy/trust/pubkeys" }
}

# Function to create Shared Plane
function New-SharedFolderStructure {
    param(
        [string]$BasePath,
        [ref]$Errors
    )
    
    $sharedBase = Join-Path $BasePath "shared"
    $Errors.Value += if(-not (New-FolderStructure -Path $sharedBase)) { "shared" }
    
    # pki/ - All PKI files (public only)
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $sharedBase "pki") -Description "All PKI files (public only)")) { "shared/pki" }
    
    # telemetry/ - Unified observability pattern
    $sharedTelemetryPath = Join-Path $sharedBase "telemetry"
    $Errors.Value += if(-not (New-FolderStructure -Path $sharedTelemetryPath -Description "Unified observability pattern")) { "shared/telemetry" }
    
    # siem/ - Flattened SIEM structure
    $siemPath = Join-Path $sharedBase "siem"
    $Errors.Value += if(-not (New-FolderStructure -Path $siemPath -Description "Flattened SIEM structure")) { "shared/siem" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $siemPath "detections") -Description "SIEM detections")) { "shared/siem/detections" }
    
    # bi-lake/curated/zero-ui/ - BI lake
    $biLakePath = Join-Path $sharedBase "bi-lake"
    $Errors.Value += if(-not (New-FolderStructure -Path $biLakePath)) { "shared/bi-lake" }
    $curatedPath = Join-Path $biLakePath "curated"
    $Errors.Value += if(-not (New-FolderStructure -Path $curatedPath)) { "shared/bi-lake/curated" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $curatedPath "zero-ui") -Description "BI lake curated data")) { "shared/bi-lake/curated/zero-ui" }
    
    # governance/ - Flattened governance structure
    $governancePath = Join-Path $sharedBase "governance"
    $Errors.Value += if(-not (New-FolderStructure -Path $governancePath -Description "Flattened governance structure")) { "shared/governance" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $governancePath "controls") -Description "Governance controls")) { "shared/governance/controls" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $governancePath "attestations") -Description "Governance attestations")) { "shared/governance/attestations" }
    
    # llm/ - Flattened governance structure
    $sharedLlmPath = Join-Path $sharedBase "llm"
    $Errors.Value += if(-not (New-FolderStructure -Path $sharedLlmPath -Description "LLM guardrails, routing, tools")) { "shared/llm" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $sharedLlmPath "guardrails") -Description "LLM guardrails")) { "shared/llm/guardrails" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $sharedLlmPath "routing") -Description "LLM routing")) { "shared/llm/routing" }
    $Errors.Value += if(-not (New-FolderStructure -Path (Join-Path $sharedLlmPath "tools") -Description "LLM tools")) { "shared/llm/tools" }
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

# Validate ZU_ROOT path
if(-not (Test-Path (Split-Path $ZuRoot -Parent))) {
    Write-Warning "Parent directory of ZU_ROOT does not exist: $(Split-Path $ZuRoot -Parent)"
    Write-Host "Creating ZU_ROOT directory: $ZuRoot" -ForegroundColor Yellow
    try {
        New-Item -ItemType Directory -Path $ZuRoot -Force | Out-Null
    } catch {
        Write-Error "Failed to create ZU_ROOT: $ZuRoot - $_"
        exit 1
    }
}

Write-Host "`nCreating ZeroUI folder structure for production environment under: $ZuRoot" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

$errors = @()

# ============================================================================
# Create production environment with tenant, product, and shared planes
# ============================================================================
$envPath = Join-Path $ZuRoot "production"
$errors += if(-not (New-FolderStructure -Path $envPath -Description "production environment")) { "production" }

# Tenant, Product, and Shared planes
Write-Host "Creating Tenant, Product, and Shared planes for production..." -ForegroundColor Cyan
New-TenantFolderStructure -BasePath $envPath -CompatAliases:$CompatAliases -Errors ([ref]$errors)
New-ProductFolderStructure -BasePath $envPath -Errors ([ref]$errors)
New-SharedFolderStructure -BasePath $envPath -Errors ([ref]$errors)

# ============================================================================
# Summary
# ============================================================================
Write-Host "`n==========================================" -ForegroundColor Cyan
$errorCount = ($errors | Where-Object { $_ -ne $null }).Count
if($errorCount -eq 0) {
    Write-Host "Folder structure created successfully!" -ForegroundColor Green
    Write-Host "ZU_ROOT: $ZuRoot" -ForegroundColor Cyan
    Write-Host "Environment: production" -ForegroundColor Cyan
    Write-Host "Planes: tenant, product, shared" -ForegroundColor Cyan
    if($CompatAliases) {
        Write-Host "Deprecated aliases: Enabled" -ForegroundColor Yellow
    }
    exit 0
} else {
    Write-Host "Folder structure creation completed with $errorCount error(s)." -ForegroundColor Yellow
    Write-Host "Failed paths:" -ForegroundColor Red
    $errors | Where-Object { $_ -ne $null } | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    exit 1
}

