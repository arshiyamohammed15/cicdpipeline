# ZeroUI Core Schema Migration Application Script
# Applies contract-derived core schema migrations to Tenant/Product/Shared Postgres databases
#
# Usage:
#   .\scripts\db\apply_migrations.ps1
#
# Environment Variables (from .env):
#   - ZEROUI_TENANT_DB_URL (or uses docker exec with container name)
#   - ZEROUI_PRODUCT_DB_URL (or uses docker exec with container name)
#   - ZEROUI_SHARED_DB_URL (or uses docker exec with container name)

$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$tenantMigration = Join-Path $repoRoot "infra\db\migrations\tenant\001_core.sql"
$productMigration1 = Join-Path $repoRoot "infra\db\migrations\product\001_core.sql"
$productMigration2 = Join-Path $repoRoot "infra\db\migrations\product\002_embeddings.sql"
$sharedMigration = Join-Path $repoRoot "infra\db\migrations\shared\001_core.sql"

$failed = $false

Write-Host "=== ZeroUI Core Schema Migration Application ===" -ForegroundColor Cyan
Write-Host ""

# Tenant Plane
Write-Host "Applying Tenant Plane migration..." -ForegroundColor Yellow
if (Test-Path $tenantMigration) {
    try {
        Get-Content $tenantMigration | docker exec -i zeroui-postgres-tenant psql -U zeroui_tenant_user -d zeroui_tenant_pg
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Tenant Plane: Migration applied" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Tenant Plane: Migration failed (exit code $LASTEXITCODE)" -ForegroundColor Red
            $failed = $true
        }
    } catch {
        Write-Host "  ✗ Tenant Plane: Error - $_" -ForegroundColor Red
        $failed = $true
    }
} else {
    Write-Host "  ✗ Tenant Plane: Migration file not found: $tenantMigration" -ForegroundColor Red
    $failed = $true
}

# Product Plane (Core)
Write-Host "Applying Product Plane core migration..." -ForegroundColor Yellow
if (Test-Path $productMigration1) {
    try {
        Get-Content $productMigration1 | docker exec -i zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Product Plane (core): Migration applied" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Product Plane (core): Migration failed (exit code $LASTEXITCODE)" -ForegroundColor Red
            $failed = $true
        }
    } catch {
        Write-Host "  ✗ Product Plane (core): Error - $_" -ForegroundColor Red
        $failed = $true
    }
} else {
    Write-Host "  ✗ Product Plane (core): Migration file not found: $productMigration1" -ForegroundColor Red
    $failed = $true
}

# Product Plane (Embeddings)
Write-Host "Applying Product Plane embeddings migration..." -ForegroundColor Yellow
if (Test-Path $productMigration2) {
    try {
        Get-Content $productMigration2 | docker exec -i zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Product Plane (embeddings): Migration applied" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Product Plane (embeddings): Migration failed (exit code $LASTEXITCODE)" -ForegroundColor Red
            $failed = $true
        }
    } catch {
        Write-Host "  ✗ Product Plane (embeddings): Error - $_" -ForegroundColor Red
        $failed = $true
    }
} else {
    Write-Host "  ✗ Product Plane (embeddings): Migration file not found: $productMigration2" -ForegroundColor Red
    $failed = $true
}

# Shared Plane
Write-Host "Applying Shared Plane migration..." -ForegroundColor Yellow
if (Test-Path $sharedMigration) {
    try {
        Get-Content $sharedMigration | docker exec -i zeroui-postgres-shared psql -U zeroui_shared_user -d zeroui_shared_pg
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Shared Plane: Migration applied" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Shared Plane: Migration failed (exit code $LASTEXITCODE)" -ForegroundColor Red
            $failed = $true
        }
    } catch {
        Write-Host "  ✗ Shared Plane: Error - $_" -ForegroundColor Red
        $failed = $true
    }
} else {
    Write-Host "  ✗ Shared Plane: Migration file not found: $sharedMigration" -ForegroundColor Red
    $failed = $true
}

Write-Host ""
if ($failed) {
    Write-Host "=== Migration Application: FAILED ===" -ForegroundColor Red
    exit 1
} else {
    Write-Host "=== Migration Application: SUCCESS ===" -ForegroundColor Green
    exit 0
}

