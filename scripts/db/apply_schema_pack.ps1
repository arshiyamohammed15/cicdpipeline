Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$schemaPackRoot = Join-Path $repoRoot "infra\db\schema_pack"
$pgSql = Join-Path $schemaPackRoot "migrations\pg\001_core.sql"

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
  $logDir = Split-Path $logPath -Parent
  if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
  ($payload | ConvertTo-Json -Compress) | Add-Content -Path $logPath -Encoding utf8
}
#endregion

if (!(Test-Path $pgSql)) { throw "Missing Postgres migration: $pgSql" }

function Apply-Pg {
  param(
    [string]$ContainerName,
    [string]$DbUser,
    [string]$DbName,
    [string]$Label
  )

  Write-Host "Applying Postgres schema pack to $Label (container: $ContainerName)..." -ForegroundColor Yellow

  $dockerCli = Get-Command docker -ErrorAction SilentlyContinue
  #region agent log
  Write-AgentLog -HypothesisId "H5" -Location "apply_schema_pack.ps1:Apply-Pg" -Message "docker cli presence" -Data @{ label = $Label; dockerFound = ($dockerCli -ne $null) }
  #endregion
  if ($null -eq $dockerCli) {
    throw "Docker CLI not found in PATH. Install/start Docker Desktop and ensure 'docker' is available."
  }

  $containerExists = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" | Select-String -Pattern "^$ContainerName$"
  #region agent log
  Write-AgentLog -HypothesisId "H1" -Location "apply_schema_pack.ps1:Apply-Pg" -Message "container availability" -Data @{ label = $Label; container = $ContainerName; exists = [bool]$containerExists }
  #endregion
  if (-not $containerExists) {
    throw "Container '$ContainerName' not found. Start Docker containers first: cd infra/docker && docker compose -f compose.yaml up -d"
  }

  $sqlContent = Get-Content $pgSql -Raw
  $sqlContent | docker exec -i $ContainerName psql -U $DbUser -d $DbName -v ON_ERROR_STOP=1
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to apply Postgres schema pack to $Label (exit code: $LASTEXITCODE)"
  }
  Write-Host "   $Label Postgres: Schema pack applied" -ForegroundColor Green
}

Write-Host "=== ZeroUI Schema Pack Application ===" -ForegroundColor Cyan
Write-Host ""

Apply-Pg -ContainerName "zeroui-postgres-ide" -DbUser "zeroui_ide_user" -DbName "zeroui_ide_pg" -Label "IDE"
Apply-Pg -ContainerName "zeroui-postgres-tenant" -DbUser "zeroui_tenant_user" -DbName "zeroui_tenant_pg" -Label "TENANT"
Apply-Pg -ContainerName "zeroui-postgres-product" -DbUser "zeroui_product_user" -DbName "zeroui_product_pg" -Label "PRODUCT"
Apply-Pg -ContainerName "zeroui-postgres-shared" -DbUser "zeroui_shared_user" -DbName "zeroui_shared_pg" -Label "SHARED"

Write-Host ""
Write-Host "=== Schema Pack Application: SUCCESS ===" -ForegroundColor Green

