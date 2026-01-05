Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$schemaPackRoot = Join-Path $repoRoot "infra\db\schema_pack"
$pgSql = Join-Path $schemaPackRoot "migrations\pg\001_core.sql"
$sqliteSql = Join-Path $schemaPackRoot "migrations\sqlite\001_core.sql"

if (!(Test-Path $pgSql)) { throw "Missing Postgres migration: $pgSql" }
if (!(Test-Path $sqliteSql)) { throw "Missing SQLite migration: $sqliteSql" }

function Apply-Pg {
  param([string]$ContainerName, [string]$DbUser, [string]$DbName, [string]$Label)

  Write-Host "Applying Postgres schema pack to $Label (container: $ContainerName)..." -ForegroundColor Yellow
  
  # Check if container exists
  $containerExists = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" | Select-String -Pattern "^$ContainerName$"
  if (-not $containerExists) {
    throw "Container '$ContainerName' not found. Start Docker containers first: cd infra/docker && docker compose -f compose.yaml up -d"
  }

  # Apply migration via docker exec
  $sqlContent = Get-Content $pgSql -Raw
  $sqlContent | docker exec -i $ContainerName psql -U $DbUser -d $DbName -v ON_ERROR_STOP=1
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to apply Postgres schema pack to $Label (exit code: $LASTEXITCODE)"
  }
  Write-Host "  ✓ $Label Postgres: Schema pack applied" -ForegroundColor Green
}

function Apply-Sqlite {
  param([string]$Path)

  if ([string]::IsNullOrWhiteSpace($Path)) { 
    Write-Host "  SKIP: ZEROUI_IDE_SQLITE_PATH not set" -ForegroundColor Gray
    return
  }

  $sqlite = Get-Command sqlite3 -ErrorAction SilentlyContinue
  if ($null -eq $sqlite) { 
    Write-Host "  SKIP: sqlite3 not found in PATH" -ForegroundColor Gray
    return
  }

  $dir = Split-Path $Path -Parent
  if (!(Test-Path $dir)) { 
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
  }

  Write-Host "Applying SQLite schema pack to IDE DB at $Path..." -ForegroundColor Yellow
  $sqlText = Get-Content $sqliteSql -Raw
  $sqlText | & sqlite3 $Path
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to apply SQLite schema pack (exit code: $LASTEXITCODE)"
  }
  Write-Host "  ✓ IDE SQLite: Schema pack applied" -ForegroundColor Green
}

Write-Host "=== ZeroUI Schema Pack Application ===" -ForegroundColor Cyan
Write-Host ""

# Apply to all 3 Postgres databases
Apply-Pg -ContainerName "zeroui-postgres-tenant" -DbUser "zeroui_tenant_user" -DbName "zeroui_tenant_pg" -Label "TENANT"
Apply-Pg -ContainerName "zeroui-postgres-product" -DbUser "zeroui_product_user" -DbName "zeroui_product_pg" -Label "PRODUCT"
Apply-Pg -ContainerName "zeroui-postgres-shared" -DbUser "zeroui_shared_user" -DbName "zeroui_shared_pg" -Label "SHARED"

# Apply to SQLite (IDE plane)
$sqlitePath = $env:ZEROUI_IDE_SQLITE_PATH
if ([string]::IsNullOrWhiteSpace($sqlitePath)) {
  $sqlitePath = $env:ZEROUI_IDE_SQLITE_URL
  if ($sqlitePath -match '^sqlite:///(.+)') {
    $sqlitePath = $Matches[1]
  }
}
Apply-Sqlite -Path $sqlitePath

Write-Host ""
Write-Host "=== Schema Pack Application: SUCCESS ===" -ForegroundColor Green

