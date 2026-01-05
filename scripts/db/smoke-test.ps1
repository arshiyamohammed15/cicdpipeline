# ZeroUI Database Smoke Test
# Validates connectivity to all Postgres databases and Redis, plus pgvector extension

param(
    [string]$TenantDbUrl = $env:ZEROUI_TENANT_DB_URL,
    [string]$ProductDbUrl = $env:ZEROUI_PRODUCT_DB_URL,
    [string]$SharedDbUrl = $env:ZEROUI_SHARED_DB_URL,
    [string]$RedisUrl = $env:REDIS_URL
)

$ErrorActionPreference = "Stop"
$failed = $false

Write-Host "=== ZeroUI Database Smoke Test ===" -ForegroundColor Cyan
Write-Host ""

# Test Tenant Postgres
Write-Host "Testing Tenant Postgres..." -ForegroundColor Yellow
try {
    if (-not $TenantDbUrl) {
        Write-Host "  SKIP: ZEROUI_TENANT_DB_URL not set" -ForegroundColor Gray
    } else {
        $result = docker exec zeroui-postgres-tenant psql -U zeroui_tenant_user -d zeroui_tenant_pg -c "SELECT version();" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Tenant Postgres: Connected" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Tenant Postgres: Failed" -ForegroundColor Red
            Write-Host "    $result" -ForegroundColor Red
            $failed = $true
        }
    }
} catch {
    Write-Host "  ✗ Tenant Postgres: Error - $_" -ForegroundColor Red
    $failed = $true
}

# Test Product Postgres + pgvector
Write-Host "Testing Product Postgres + pgvector..." -ForegroundColor Yellow
try {
    if (-not $ProductDbUrl) {
        Write-Host "  SKIP: ZEROUI_PRODUCT_DB_URL not set" -ForegroundColor Gray
    } else {
        $result = docker exec zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';" 2>&1
        if ($LASTEXITCODE -eq 0 -and $result -match "vector") {
            Write-Host "  ✓ Product Postgres: Connected" -ForegroundColor Green
            Write-Host "  ✓ pgvector extension: Enabled" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Product Postgres or pgvector: Failed" -ForegroundColor Red
            Write-Host "    $result" -ForegroundColor Red
            $failed = $true
        }
    }
} catch {
    Write-Host "  ✗ Product Postgres: Error - $_" -ForegroundColor Red
    $failed = $true
}

# Test Shared Postgres
Write-Host "Testing Shared Postgres..." -ForegroundColor Yellow
try {
    if (-not $SharedDbUrl) {
        Write-Host "  SKIP: ZEROUI_SHARED_DB_URL not set" -ForegroundColor Gray
    } else {
        $result = docker exec zeroui-postgres-shared psql -U zeroui_shared_user -d zeroui_shared_pg -c "SELECT version();" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Shared Postgres: Connected" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Shared Postgres: Failed" -ForegroundColor Red
            Write-Host "    $result" -ForegroundColor Red
            $failed = $true
        }
    }
} catch {
    Write-Host "  ✗ Shared Postgres: Error - $_" -ForegroundColor Red
    $failed = $true
}

# Test Redis
Write-Host "Testing Redis..." -ForegroundColor Yellow
try {
    if (-not $RedisUrl) {
        Write-Host "  SKIP: REDIS_URL not set" -ForegroundColor Gray
    } else {
        $result = docker exec zeroui-redis redis-cli PING 2>&1
        if ($LASTEXITCODE -eq 0 -and $result -match "PONG") {
            Write-Host "  ✓ Redis: Connected" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Redis: Failed" -ForegroundColor Red
            Write-Host "    $result" -ForegroundColor Red
            $failed = $true
        }
    }
} catch {
    Write-Host "  ✗ Redis: Error - $_" -ForegroundColor Red
    $failed = $true
}

Write-Host ""
if ($failed) {
    Write-Host "=== Smoke Test: FAILED ===" -ForegroundColor Red
    exit 1
} else {
    Write-Host "=== Smoke Test: PASSED ===" -ForegroundColor Green
    exit 0
}

