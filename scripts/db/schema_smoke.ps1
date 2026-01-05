# ZeroUI Core Schema Smoke Test
# Validates that core schema tables exist and basic SELECT queries work
#
# Usage:
#   .\scripts\db\schema_smoke.ps1

$ErrorActionPreference = "Stop"
$failed = $false

Write-Host "=== ZeroUI Core Schema Smoke Test ===" -ForegroundColor Cyan
Write-Host ""

# Tenant Plane
Write-Host "Testing Tenant Plane schema..." -ForegroundColor Yellow
try {
    $result = docker exec zeroui-postgres-tenant psql -U zeroui_tenant_user -d zeroui_tenant_pg -c "SELECT COUNT(*) FROM app.tenant_receipt_index;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ tenant_receipt_index: Table exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ tenant_receipt_index: Table missing or error" -ForegroundColor Red
        Write-Host "    $result" -ForegroundColor Red
        $failed = $true
    }
    
    $result = docker exec zeroui-postgres-tenant psql -U zeroui_tenant_user -d zeroui_tenant_pg -c "SELECT COUNT(*) FROM app.tenant_integration_cursor;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ tenant_integration_cursor: Table exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ tenant_integration_cursor: Table missing or error" -ForegroundColor Red
        Write-Host "    $result" -ForegroundColor Red
        $failed = $true
    }
} catch {
    Write-Host "  ✗ Tenant Plane: Error - $_" -ForegroundColor Red
    $failed = $true
}

# Product Plane
Write-Host "Testing Product Plane schema..." -ForegroundColor Yellow
try {
    $result = docker exec zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg -c "SELECT COUNT(*) FROM app.policy_bundle;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ policy_bundle: Table exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ policy_bundle: Table missing or error" -ForegroundColor Red
        Write-Host "    $result" -ForegroundColor Red
        $failed = $true
    }
    
    $result = docker exec zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg -c "SELECT COUNT(*) FROM app.policy_release;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ policy_release: Table exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ policy_release: Table missing or error" -ForegroundColor Red
        Write-Host "    $result" -ForegroundColor Red
        $failed = $true
    }
    
    $result = docker exec zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg -c "SELECT COUNT(*) FROM app.embedding_document;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ embedding_document: Table exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ embedding_document: Table missing or error" -ForegroundColor Red
        Write-Host "    $result" -ForegroundColor Red
        $failed = $true
    }
    
    $result = docker exec zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg -c "SELECT COUNT(*) FROM app.embedding_vector;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ embedding_vector: Table exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ embedding_vector: Table missing or error" -ForegroundColor Red
        Write-Host "    $result" -ForegroundColor Red
        $failed = $true
    }
    
    # Check pgvector extension
    $result = docker exec zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';" 2>&1
    if ($LASTEXITCODE -eq 0 -and $result -match "vector") {
        Write-Host "  ✓ pgvector extension: Enabled" -ForegroundColor Green
    } else {
        Write-Host "  ✗ pgvector extension: Not enabled or error" -ForegroundColor Red
        Write-Host "    $result" -ForegroundColor Red
        $failed = $true
    }
} catch {
    Write-Host "  ✗ Product Plane: Error - $_" -ForegroundColor Red
    $failed = $true
}

# Shared Plane
Write-Host "Testing Shared Plane schema..." -ForegroundColor Yellow
try {
    $result = docker exec zeroui-postgres-shared psql -U zeroui_shared_user -d zeroui_shared_pg -c "SELECT COUNT(*) FROM app.provider_registry;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ provider_registry: Table exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ provider_registry: Table missing or error" -ForegroundColor Red
        Write-Host "    $result" -ForegroundColor Red
        $failed = $true
    }
    
    $result = docker exec zeroui-postgres-shared psql -U zeroui_shared_user -d zeroui_shared_pg -c "SELECT COUNT(*) FROM app.eval_run;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ eval_run: Table exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ eval_run: Table missing or error" -ForegroundColor Red
        Write-Host "    $result" -ForegroundColor Red
        $failed = $true
    }
    
    $result = docker exec zeroui-postgres-shared psql -U zeroui_shared_user -d zeroui_shared_pg -c "SELECT COUNT(*) FROM app.supply_chain_artifact;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ supply_chain_artifact: Table exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ supply_chain_artifact: Table missing or error" -ForegroundColor Red
        Write-Host "    $result" -ForegroundColor Red
        $failed = $true
    }
} catch {
    Write-Host "  ✗ Shared Plane: Error - $_" -ForegroundColor Red
    $failed = $true
}

Write-Host ""
if ($failed) {
    Write-Host "=== Schema Smoke Test: FAILED ===" -ForegroundColor Red
    exit 1
} else {
    Write-Host "=== Schema Smoke Test: PASSED ===" -ForegroundColor Green
    exit 0
}

