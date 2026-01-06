# CI Check: Verify Database Services Use Canonical Environment Variables
# ID: CI.DB-ENV-VARS.CHECK.MT-01
# Purpose: Enforce that all database services use canonical plane-specific env vars per DB Plane Contract Option A

param(
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Canonical env vars per DB Plane Contract Option A
$canonicalEnvVars = @{
    "IDE" = "ZEROUI_IDE_SQLITE_URL"
    "TENANT" = "ZEROUI_TENANT_DB_URL"
    "PRODUCT" = "ZEROUI_PRODUCT_DB_URL"
    "SHARED" = "ZEROUI_SHARED_DB_URL"
}

# Service to plane mapping (per DB Plane Contract Option A)
$servicePlaneMap = @{
    "evidence-receipt-indexing-service" = "TENANT"
    "integration-adapters" = "TENANT"
    "user_behaviour_intelligence" = "PRODUCT"
    "mmm_engine" = "PRODUCT"
    "contracts-schema-registry" = "SHARED"
    "configuration-policy-management" = "SHARED"
    "health-reliability-monitoring" = "SHARED"
    "budgeting-rate-limiting-cost-observability" = "SHARED"
    "data-governance-privacy" = "SHARED"
}

# Normalize repo root path
if ([string]::IsNullOrEmpty($RepoRoot)) {
    $RepoRoot = (Get-Location).Path
}
if (-not (Test-Path -Path $RepoRoot)) {
    $currentDir = Get-Location
    $searchPath = $currentDir
    while ($searchPath -and $searchPath -ne $searchPath.Parent) {
        if (Test-Path (Join-Path $searchPath ".git") -PathType Container) {
            $RepoRoot = $searchPath.Path
            break
        }
        if (Test-Path (Join-Path $searchPath "AGENTS.md")) {
            $RepoRoot = $searchPath.Path
            break
        }
        $searchPath = $searchPath.Parent
    }
    if (-not $RepoRoot) {
        $RepoRoot = $currentDir.Path
    }
}
$RepoRoot = (Resolve-Path -Path $RepoRoot -ErrorAction Stop).Path

Write-Host "Verifying database environment variable usage..." -ForegroundColor Cyan
Write-Host "Repo root: $RepoRoot" -ForegroundColor Gray
Write-Host ""

# Collect violations
$violations = @()

# Check each service
foreach ($serviceName in $servicePlaneMap.Keys) {
    $plane = $servicePlaneMap[$serviceName]
    $canonicalVar = $canonicalEnvVars[$plane]
    
    # Find database connection files
    $connectionFiles = @()
    $servicePaths = @(
        "src\cloud_services\shared-services\$serviceName",
        "src\cloud_services\product_services\$serviceName",
        "src\cloud_services\client-services\$serviceName"
    )
    
    foreach ($servicePath in $servicePaths) {
        $fullPath = Join-Path $RepoRoot $servicePath
        if (Test-Path -Path $fullPath -PathType Container) {
            $dbFiles = Get-ChildItem -Path $fullPath -Recurse -Filter "*connection.py" -ErrorAction SilentlyContinue
            $dbFiles += Get-ChildItem -Path $fullPath -Recurse -Filter "*session.py" -ErrorAction SilentlyContinue
            $dbFiles += Get-ChildItem -Path $fullPath -Recurse -Filter "*config.py" -ErrorAction SilentlyContinue
            $connectionFiles += $dbFiles
        }
    }
    
    if ($connectionFiles.Count -eq 0) {
        Write-Host "  ⚠️  Service '$serviceName': No connection files found" -ForegroundColor Yellow
        continue
    }
    
    $serviceHasCanonicalVar = $false
    $serviceUsesGenericVar = $false
    
    foreach ($file in $connectionFiles) {
        $content = Get-Content -Path $file.FullName -Raw -ErrorAction Stop
        $relativePath = $file.FullName.Replace($RepoRoot, "").TrimStart("\", "/")
        
        # Check for canonical var usage
        if ($content -match [regex]::Escape($canonicalVar)) {
            $serviceHasCanonicalVar = $true
            Write-Host "  ✓  $relativePath: Uses $canonicalVar" -ForegroundColor Green
        }
        
        # Check for generic DATABASE_URL (without canonical var)
        if ($content -match '\bDATABASE_URL\b' -and -not $content -match [regex]::Escape($canonicalVar)) {
            $serviceUsesGenericVar = $true
            $violations += [PSCustomObject]@{
                Service = $serviceName
                Plane = $plane
                File = $relativePath
                Issue = "Uses generic DATABASE_URL without canonical $canonicalVar"
            }
        }
    }
    
    if (-not $serviceHasCanonicalVar) {
        $violations += [PSCustomObject]@{
            Service = $serviceName
            Plane = $plane
            File = "N/A"
            Issue = "Does not use canonical $canonicalVar"
        }
    }
}

# Report results
Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan

if ($violations.Count -gt 0) {
    Write-Host "VIOLATIONS DETECTED: Database services not using canonical env vars" -ForegroundColor Red
    Write-Host ("=" * 80) -ForegroundColor Red
    Write-Host ""
    Write-Host "Per DB Plane Contract Option A, all services must use:" -ForegroundColor Yellow
    Write-Host "  - IDE Plane: ZEROUI_IDE_SQLITE_URL" -ForegroundColor Yellow
    Write-Host "  - Tenant Plane: ZEROUI_TENANT_DB_URL" -ForegroundColor Yellow
    Write-Host "  - Product Plane: ZEROUI_PRODUCT_DB_URL" -ForegroundColor Yellow
    Write-Host "  - Shared Plane: ZEROUI_SHARED_DB_URL" -ForegroundColor Yellow
    Write-Host ""
    
    # Group by service
    $grouped = $violations | Group-Object -Property Service
    
    foreach ($group in $grouped) {
        Write-Host "Service: $($group.Name)" -ForegroundColor Red
        foreach ($violation in $group.Group) {
            Write-Host "  Plane: $($violation.Plane) → Should use: $($canonicalEnvVars[$violation.Plane])" -ForegroundColor Yellow
            Write-Host "  File: $($violation.File)" -ForegroundColor Gray
            Write-Host "  Issue: $($violation.Issue)" -ForegroundColor Gray
        }
        Write-Host ""
    }
    
    Write-Host "Total violations: $($violations.Count)" -ForegroundColor Red
    exit 1
} else {
    Write-Host "OK: All database services use canonical env vars" -ForegroundColor Green
    Write-Host ("=" * 80) -ForegroundColor Green
    exit 0
}

