Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName

function Apply-PgPhase0Stub {
  param([string]$ContainerName, [string]$DbUser, [string]$DbName, [string]$Label, [string]$MigrationFile)

  Write-Host "Applying Phase 0 stub to $Label (container: $ContainerName)..." -ForegroundColor Yellow
  
  # Check if container exists
  $containerExists = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" | Select-String -Pattern "^$ContainerName$"
  if (-not $containerExists) {
    throw "Container '$ContainerName' not found. Start Docker containers first: cd infra/docker && docker compose -f compose.yaml up -d"
  }

  # Apply migration via docker exec
  $sqlContent = Get-Content $MigrationFile -Raw
  $sqlContent | docker exec -i $ContainerName psql -U $DbUser -d $DbName -v ON_ERROR_STOP=1
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to apply Phase 0 stub to $Label (exit code: $LASTEXITCODE)"
  }
  Write-Host "  ✓ $Label Postgres: Phase 0 stub applied" -ForegroundColor Green
}

function Apply-SqlitePhase0Stub {
  param([string]$Path, [string]$MigrationFile)

  if ([string]::IsNullOrWhiteSpace($Path)) { 
    Write-Host "  SKIP: ZEROUI_IDE_SQLITE_PATH not set" -ForegroundColor Gray
    return
  }

  $sqlite = Get-Command sqlite3 -ErrorAction SilentlyContinue
  if ($null -eq $sqlite) { 
    Write-Host "  SKIP: sqlite3 not found in PATH" -ForegroundColor Gray
    return
  }

  Write-Host "Applying Phase 0 stub to IDE SQLite at $Path..." -ForegroundColor Yellow
  $sqlText = Get-Content $MigrationFile -Raw
  $sqlText | & sqlite3 $Path
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to apply Phase 0 stub to SQLite (exit code: $LASTEXITCODE)"
  }
  Write-Host "  ✓ IDE SQLite: Phase 0 stub applied" -ForegroundColor Green
}

Write-Host "=== ZeroUI Phase 0 Stubs Application ===" -ForegroundColor Cyan
Write-Host ""

# Apply BKG Phase 0 stubs (separate migrations for documentation, though BKG is also in schema pack)
$bkgTenant = Join-Path $repoRoot "infra\db\migrations\tenant\002_bkg_phase0.sql"
$bkgProduct = Join-Path $repoRoot "infra\db\migrations\product\003_bkg_phase0.sql"
$bkgShared = Join-Path $repoRoot "infra\db\migrations\shared\002_bkg_phase0.sql"
$bkgSqlite = Join-Path $repoRoot "infra\db\migrations\sqlite\002_bkg_phase0.sql"

if (Test-Path $bkgTenant) {
  Apply-PgPhase0Stub -ContainerName "zeroui-postgres-tenant" -DbUser "zeroui_tenant_user" -DbName "zeroui_tenant_pg" -Label "TENANT" -MigrationFile $bkgTenant
}
if (Test-Path $bkgProduct) {
  Apply-PgPhase0Stub -ContainerName "zeroui-postgres-product" -DbUser "zeroui_product_user" -DbName "zeroui_product_pg" -Label "PRODUCT" -MigrationFile $bkgProduct
}
if (Test-Path $bkgShared) {
  Apply-PgPhase0Stub -ContainerName "zeroui-postgres-shared" -DbUser "zeroui_shared_user" -DbName "zeroui_shared_pg" -Label "SHARED" -MigrationFile $bkgShared
}
if (Test-Path $bkgSqlite) {
  $sqlitePath = $env:ZEROUI_IDE_SQLITE_PATH
  if ([string]::IsNullOrWhiteSpace($sqlitePath)) {
    $sqlitePath = $env:ZEROUI_IDE_SQLITE_URL
    if ($sqlitePath -match '^sqlite:///(.+)') {
      $sqlitePath = $Matches[1]
    }
  }
  Apply-SqlitePhase0Stub -Path $sqlitePath -MigrationFile $bkgSqlite
}

# Apply Semantic Q&A Cache Phase 0 stub (Product plane only)
$qaCacheProduct = Join-Path $repoRoot "infra\db\migrations\product\004_semantic_qa_cache_phase0.sql"
if (Test-Path $qaCacheProduct) {
  Apply-PgPhase0Stub -ContainerName "zeroui-postgres-product" -DbUser "zeroui_product_user" -DbName "zeroui_product_pg" -Label "PRODUCT" -MigrationFile $qaCacheProduct
}

Write-Host ""
Write-Host "=== Phase 0 Stubs Application: SUCCESS ===" -ForegroundColor Green

