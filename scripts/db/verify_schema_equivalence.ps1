Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "lib\schema_parse.ps1")

$repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$schemaPackRoot = Join-Path $repoRoot "infra\db\schema_pack"
$contractPath = Join-Path $schemaPackRoot "canonical_schema_contract.json"
$contract = Get-CanonicalSchemaContract -Path $contractPath

#region agent log
function Write-AgentLog {
  param(
    [string]$HypothesisId,
    [string]$Location,
    [string]$Message,
    [hashtable]$Data = @{}
  )

  $payload = @{
    sessionId    = "debug-session"
    runId        = "pre-fix"
    hypothesisId = $HypothesisId
    location     = $Location
    message      = $Message
    data         = $Data
    timestamp    = [int64](([datetime]::UtcNow - [datetime]"1970-01-01").TotalMilliseconds)
  }

  $logPath = "d:\Projects\ZeroUI2.1\.cursor\debug.log"
  $dir = Split-Path $logPath -Parent
  if (!(Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  ($payload | ConvertTo-Json -Compress) | Add-Content -Path $logPath -Encoding utf8
}
#endregion

function Normalize-PgDump {
  param([string]$Text)

  $lines = $Text -split "`n"
  $out = New-Object System.Collections.Generic.List[string]
  foreach ($ln in $lines) {
    $t = $ln.TrimEnd()
    if ($t -match '^(--|/\*|SET\s|SELECT\s+pg_catalog|COMMENT\s+ON|ALTER\s+.*OWNER\s+TO|GRANT\s|REVOKE\s|\\(connect|restrict|unrestrict)|WARNING:|HINT:|DETAIL:)') { continue }
    if ($t -eq "") { continue }
    $out.Add($t)
  }
  return ($out -join "`n")
}

function Get-PgSchemaDump {
  param([string]$ContainerName, [string]$DbUser, [string]$DbName, [string]$Label)

  Write-Host "Dumping schema from $Label Postgres..." -ForegroundColor Yellow
  
  $dockerCli = Get-Command docker -ErrorAction SilentlyContinue
  #region agent log
  Write-AgentLog -HypothesisId "H5" -Location "verify_schema_equivalence.ps1:Get-PgSchemaDump" -Message "docker cli presence" -Data @{ label = $Label; dockerFound = ($dockerCli -ne $null) }
  #endregion
  if ($null -eq $dockerCli) {
    throw "Docker CLI not found in PATH. Install/start Docker Desktop and ensure 'docker' is available."
  }

  # Check if container exists
  $containerExists = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" | Select-String -Pattern "^$ContainerName$"
  if (-not $containerExists) {
    #region agent log
    Write-AgentLog -HypothesisId "H1" -Location "verify_schema_equivalence.ps1:Get-PgSchemaDump" -Message "container missing" -Data @{ label = $Label; container = $ContainerName }
    #endregion
    throw "Container '$ContainerName' not found. Start Docker containers first: cd infra/docker && docker compose -f compose.yaml up -d"
  }

  $prevErrorAction = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $raw = docker exec $ContainerName pg_dump -U $DbUser -d $DbName --schema-only 2>&1
  } finally {
    $ErrorActionPreference = $prevErrorAction
  }
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to dump schema from $Label Postgres: $raw"
  }
  $rawText = $raw -join "`n"
  #region agent log
  Write-AgentLog -HypothesisId "H2" -Location "verify_schema_equivalence.ps1:Get-PgSchemaDump" -Message "pg dump captured" -Data @{ label = $Label; container = $ContainerName; dumpLength = $rawText.Length }
  #endregion
  return Normalize-PgDump -Text $rawText
}

Write-Host "=== ZeroUI Schema Equivalence Verification ===" -ForegroundColor Cyan
Write-Host ""

# Verify Postgres schemas are identical
Write-Host "Verifying Postgres schemas are identical (tenant vs product vs shared)..." -ForegroundColor Yellow
$tenantDump  = Get-PgSchemaDump -ContainerName "zeroui-postgres-tenant" -DbUser "zeroui_tenant_user" -DbName "zeroui_tenant_pg" -Label "TENANT"
$productDump = Get-PgSchemaDump -ContainerName "zeroui-postgres-product" -DbUser "zeroui_product_user" -DbName "zeroui_product_pg" -Label "PRODUCT"
$sharedDump  = Get-PgSchemaDump -ContainerName "zeroui-postgres-shared" -DbUser "zeroui_shared_user" -DbName "zeroui_shared_pg" -Label "SHARED"

if ($tenantDump -ne $productDump) { 
  Write-Host " Postgres schema mismatch: TENANT vs PRODUCT" -ForegroundColor Red
  throw "Postgres schema mismatch: TENANT vs PRODUCT"
}
if ($tenantDump -ne $sharedDump) { 
  Write-Host " Postgres schema mismatch: TENANT vs SHARED" -ForegroundColor Red
  throw "Postgres schema mismatch: TENANT vs SHARED"
}

Write-Host "   Postgres schema equivalence: OK" -ForegroundColor Green

# Verify SQLite schema matches canonical contract
Write-Host "Verifying SQLite schema matches canonical contract (table/column names)..." -ForegroundColor Yellow
$sqlitePath = $env:ZEROUI_IDE_SQLITE_PATH
if ([string]::IsNullOrWhiteSpace($sqlitePath)) {
  $sqlitePath = $env:ZEROUI_IDE_SQLITE_URL
  if ($sqlitePath -match '^sqlite:///(.+)') {
    $sqlitePath = $Matches[1]
  }
}

#region agent log
$sqlitePathExists = -not [string]::IsNullOrWhiteSpace($sqlitePath) -and (Test-Path $sqlitePath)
$sqliteCli = Get-Command sqlite3 -ErrorAction SilentlyContinue
Write-AgentLog -HypothesisId "H3" -Location "verify_schema_equivalence.ps1:SQLite" -Message "sqlite path resolution" -Data @{ path = $sqlitePath; pathExists = $sqlitePathExists; sqliteCliFound = ($sqliteCli -ne $null) }
#endregion


if ([string]::IsNullOrWhiteSpace($sqlitePath)) {
  Write-Host "  SKIP: ZEROUI_IDE_SQLITE_PATH not set" -ForegroundColor Gray
} else {
  if (!(Test-Path $sqlitePath)) {
    Write-Host "  SKIP: SQLite file not found: $sqlitePath" -ForegroundColor Gray
  } else {
    $sqlite = Get-Command sqlite3 -ErrorAction SilentlyContinue
    if ($null -eq $sqlite) { 
      Write-Host "  SKIP: sqlite3 not found in PATH" -ForegroundColor Gray
    } else {
      $schemaText = & sqlite3 $sqlitePath ".schema"
      $parsed = Parse-SqliteSchema -SqliteSchemaText ($schemaText -join "`n")

      foreach ($t in $contract.sqlite.tables) {
        Assert-TableHasColumns -ParsedTables $parsed -TableName $t.name -RequiredColumns $t.columns
      }

      Write-Host "   SQLite contract check: OK" -ForegroundColor Green
    }
  }
}

# Verify meta.schema_version values
Write-Host "Verifying meta.schema_version values..." -ForegroundColor Yellow

# Postgres check (tenant DB as representative)
$prevEA = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
  $verTenant = docker exec zeroui-postgres-tenant psql -U zeroui_tenant_user -d zeroui_tenant_pg -t -A -c "SELECT schema_version FROM meta.schema_version WHERE schema_pack_id='zeroui_core_schema_pack';" 2>&1
} finally {
  $ErrorActionPreference = $prevEA
}
if ($LASTEXITCODE -eq 0) {
  $verTenantFiltered = @()
  foreach ($line in $verTenant) {
    if ($line -match '^(WARNING:|HINT:|DETAIL:)') { continue }
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $verTenantFiltered += $line
  }
  $verTenantTrimmed = ($verTenantFiltered -join "").Trim()
  if ($verTenantTrimmed -ne "001") { 
    throw "Postgres schema_version mismatch (expected 001, got: $verTenantTrimmed)"
  }
  #region agent log
  Write-AgentLog -HypothesisId "H4" -Location "verify_schema_equivalence.ps1:PostgresSchemaVersion" -Message "postgres schema_version fetched" -Data @{ value = $verTenantTrimmed }
  #endregion
  Write-Host "   Postgres meta.schema_version: OK (version 001)" -ForegroundColor Green
} else {
  Write-Host "   Postgres schema_version query failed: $verTenant" -ForegroundColor Red
  throw "Postgres schema_version query failed"
}

# SQLite check
if (-not [string]::IsNullOrWhiteSpace($sqlitePath) -and (Test-Path $sqlitePath)) {
  $sqlite = Get-Command sqlite3 -ErrorAction SilentlyContinue
  if ($null -ne $sqlite) {
    $verSqlite = & sqlite3 $sqlitePath "SELECT schema_version FROM meta__schema_version WHERE schema_pack_id='zeroui_core_schema_pack';" 2>&1
    $verSqliteTrimmed = ($verSqlite -join "").Trim()
    if ($verSqliteTrimmed -ne "001") { 
      throw "SQLite schema_version mismatch (expected 001, got: $verSqliteTrimmed)"
    }
    Write-Host "   SQLite meta__schema_version: OK (version 001)" -ForegroundColor Green
  }
}

Write-Host ""
Write-Host "=== ALL SCHEMA IDENTITY CHECKS PASSED ===" -ForegroundColor Green

