<#
.SYNOPSIS
  ZeroUI 4-plane scaffold (Windows-first). Creates ONLY the folder structure, idempotently.

.DESCRIPTION
  Implements strict improvements:
    - Laptop receipts month partition when -CreateDt is provided: agent/receipts/<repo>/<YYYY>/<MM>/
    - Date partitions (dt=YYYY-MM-DD) for Observability, Adapters/Gateway logs, and Reporting
    - Per-consumer watermarks: .../evidence/watermarks/<consumer>/
    - RFC fallback scaffolding: ingest/staging/unclassified/ and -StampUnclassified <slug>
    - Deprecated alias 'meta/schema' gated by -CompatAliases
    - Strict -Shards validation (0,16,256)
    - Dry-run preview (-DryRun)
    - Removed undocumented laptop/extension/* paths to avoid drift

.PARAMETER ZuRoot
  Absolute or relative path to the root folder (will be created if missing).

.PARAMETER Tenant
  Tenant identifier (free-form; will be slugged to kebab-case).

.PARAMETER Org
  Organization identifier (optional; slugged).

.PARAMETER Region
  Region identifier (optional; slugged).

.PARAMETER Env
  Environment identifier (e.g., dev|stg|prod; slugged).

.PARAMETER Repo
  Repository identifier used for laptop receipts path (slugged).

.PARAMETER CreateDt
  UTC date partition in YYYY-MM-DD. Enables dt=<date> partitions and laptop YYYY/MM partitioning.

.PARAMETER Shards
  Optional shard count for hot-sharding (validated: 0,16,256). Directories are not created for shards unless
  your downstream tools require them; this parameter is validated only to keep config honest.

.PARAMETER Consumer
  Consumer-id for watermarks: creates .../evidence/watermarks/<consumer>/ under Tenant and Product.

.PARAMETER CompatAliases
  If set, also creates deprecated alias folder tenant/meta/schema for legacy compatibility.

.PARAMETER DryRun
  If set, prints intended mkdir operations without creating.

.PARAMETER StampUnclassified
  Slug to stamp 'UNCLASSIFIED__<slug>' under tenant/product ingest/staging/unclassified and laptop/agent/tmp.

.EXAMPLE
  pwsh -File tools\scaffold\zero_ui_scaffold.ps1 -ZuRoot D:\ZeroUI -Tenant acme -Env dev -Repo core -CreateDt 2025-10-18 -Consumer metrics -DryRun

#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$ZuRoot,
  [string]$Tenant = "default-tenant",
  [string]$Org,
  [string]$Region,
  [string]$Env = "dev",
  [string]$Repo = "repo",
  [ValidatePattern('^\d{4}-\d{2}-\d{2}$')][string]$CreateDt,
  [ValidateSet(0,16,256)][int]$Shards = 0,
  [string]$Consumer,
  [switch]$CompatAliases,
  [switch]$DryRun,
  [string]$StampUnclassified
)

# --- Helpers ---
function Slug([string]$s){
  if([string]::IsNullOrWhiteSpace($s)){ return "" }
  $x = $s.ToLower()
  $x = -join ($x.ToCharArray() | ForEach-Object { if( ($_ -match '[a-z0-9]') ){ $_ } else { '-' } })
  $x = $x -replace '-+', '-'
  $x = $x.Trim('-')
  if([string]::IsNullOrWhiteSpace($x)){ return "x" } else { return $x }
}

function MkdirSafe([string]$p){
  if($DryRun){
    Write-Host "[DRY] mkdir -p $p"
  } else {
    New-Item -ItemType Directory -Force -Path $p | Out-Null
  }
}

function JoinParts([string[]]$parts){
  $parts -join [IO.Path]::DirectorySeparatorChar
}

# Normalize identifiers
$Tenant = Slug $Tenant
$Org    = if($Org){ Slug $Org } else { "" }
$Region = if($Region){ Slug $Region } else { "" }
$Env    = Slug $Env
$Repo   = Slug $Repo
$Consumer = if($Consumer){ Slug $Consumer } else { "" }
$StampUnclassified = if($StampUnclassified){ "UNCLASSIFIED__" + (Slug $StampUnclassified) } else { "" }

$root = Resolve-Path -Path $ZuRoot -ErrorAction SilentlyContinue
if(-not $root){
  if($DryRun){ Write-Host "[DRY] mkdir -p $ZuRoot" } else { New-Item -ItemType Directory -Force -Path $ZuRoot | Out-Null }
  $root = Resolve-Path -Path $ZuRoot
}
$root = $root.Path

# Date parts
$YYYY = $null; $MM = $null
if($CreateDt){
  $YYYY = $CreateDt.Substring(0,4)
  $MM   = $CreateDt.Substring(5,2)
}

# --- Directory plan ---
$plan = New-Object System.Collections.Generic.List[string]

# Plane: ide
$laptop = Join-Path $root "ide"
$plan.Add($laptop)

# Laptop agent receipts (month partition when CreateDt)
if($CreateDt){
  $plan.Add( (JoinParts @($laptop,"agent","receipts",$Repo,$YYYY,$MM)) )
} else {
  $plan.Add( (JoinParts @($laptop,"agent","receipts",$Repo)) )
}
$plan.Add( (JoinParts @($laptop,"agent","receipts",$Repo,"index")) )
$plan.Add( (JoinParts @($laptop,"agent","receipts",$Repo,"quarantine")) )
$plan.Add( (JoinParts @($laptop,"agent","receipts",$Repo,"checkpoints")) )
# Laptop policy cache & trust
$plan.Add( (JoinParts @($laptop,"agent","policy","cache")) )
$plan.Add( (JoinParts @($laptop,"agent","trust","pubkeys")) )
# Laptop consent & queues
$plan.Add( (JoinParts @($laptop,"agent","config","consent")) )
$plan.Add( (JoinParts @($laptop,"agent","queue","evidence","pending")) )
$plan.Add( (JoinParts @($laptop,"agent","queue","evidence","sent")) )
$plan.Add( (JoinParts @($laptop,"agent","queue","evidence","failed")) )
# Laptop logs & db
$plan.Add( (JoinParts @($laptop,"agent","logs","metrics")) )
$plan.Add( (JoinParts @($laptop,"agent","db")) )
# Laptop llm sanitized trees
$plan.Add( (JoinParts @($laptop,"agent","llm","prompts")) )
$plan.Add( (JoinParts @($laptop,"agent","llm","tools")) )
$plan.Add( (JoinParts @($laptop,"agent","llm","adapters")) )
$plan.Add( (JoinParts @($laptop,"agent","llm","cache","token")) )
$plan.Add( (JoinParts @($laptop,"agent","llm","cache","embedding")) )
$plan.Add( (JoinParts @($laptop,"agent","llm","redaction")) )
$plan.Add( (JoinParts @($laptop,"agent","llm","runs")) )
# Laptop actor & tmp
$plan.Add( (JoinParts @($laptop,"agent","actor","fingerprint")) )
$plan.Add( (JoinParts @($laptop,"agent","tmp")) )

# Plane: tenant
$tenant = Join-Path $root "tenant"
$plan.Add($tenant)
# Evidence receipts mirror & watermarks
$plan.Add( (JoinParts @($tenant,"evidence","receipts")) )  # generic root if needed
$plan.Add( (JoinParts @($tenant,"evidence","manifests")) )
$plan.Add( (JoinParts @($tenant,"evidence","checksums")) )
$plan.Add( (JoinParts @($tenant,"evidence","dlq")) )
$plan.Add( (JoinParts @($tenant,"evidence","watermarks")) )
if($Consumer){ $plan.Add( (JoinParts @($tenant,"evidence","watermarks",$Consumer)) ) }
# Ingest staging (RFC fallback)
$plan.Add( (JoinParts @($tenant,"ingest","staging")) )
$plan.Add( (JoinParts @($tenant,"ingest","staging","unclassified")) )
# Observability partitions
if($CreateDt){
  foreach($k in @("metrics","traces","logs")){
    $plan.Add( (JoinParts @($tenant,"observability",$k,"dt=$CreateDt")) )
  }
} else {
  foreach($k in @("metrics","traces","logs")){
    $plan.Add( (JoinParts @($tenant,"observability",$k)) )
  }
}
# Adapters/webhooks & gateway logs
if($CreateDt){
  $plan.Add( (JoinParts @($tenant,"adapters","webhooks","dt=$CreateDt")) )
  $plan.Add( (JoinParts @($tenant,"adapters","gateway-logs","dt=$CreateDt")) )
} else {
  $plan.Add( (JoinParts @($tenant,"adapters","webhooks")) )
  $plan.Add( (JoinParts @($tenant,"adapters","gateway-logs")) )
}
# Reporting analytics
if($CreateDt){
  $plan.Add( (JoinParts @($tenant,"reporting","marts","dt=$CreateDt")) )
} else {
  $plan.Add( (JoinParts @($tenant,"reporting","marts")) )
}
# Policy mirror & trust
$plan.Add( (JoinParts @($tenant,"policy","snapshots")) )
$plan.Add( (JoinParts @($tenant,"policy","trust","pubkeys")) )
# Deprecated alias (compat)
if($CompatAliases){
  $plan.Add( (JoinParts @($tenant,"meta","schema")) )
}

# Plane: product
$product = Join-Path $root "product"
$plan.Add($product)
# Policy registry
$plan.Add( (JoinParts @($product,"policy-registry","releases")) )
$plan.Add( (JoinParts @($product,"policy-registry","templates")) )
$plan.Add( (JoinParts @($product,"policy-registry","revocations")) )
# Evidence watermarks (per-consumer optional)
$plan.Add( (JoinParts @($product,"evidence","watermarks")) )
if($Consumer){ $plan.Add( (JoinParts @($product,"evidence","watermarks",$Consumer)) ) }
# Adapters gateway logs
if($CreateDt){
  $plan.Add( (JoinParts @($product,"adapters","gateway-logs","dt=$CreateDt")) )
} else {
  $plan.Add( (JoinParts @($product,"adapters","gateway-logs")) )
}
# Product service metrics
if($CreateDt){
  $plan.Add( (JoinParts @($product,"service-metrics","dt=$CreateDt")) )
} else {
  $plan.Add( (JoinParts @($product,"service-metrics")) )
}
# Trust pubkeys (public only)
$plan.Add( (JoinParts @($product,"trust","pubkeys")) )
# Reporting aggregates (optional)
if($CreateDt){
  $plan.Add( (JoinParts @($product,"reporting","tenants","aggregates","dt=$CreateDt")) )
} else {
  $plan.Add( (JoinParts @($product,"reporting","tenants","aggregates")) )
}

# Plane: shared
$shared = Join-Path $root "shared"
$plan.Add($shared)
$plan.Add( (JoinParts @($shared,"pki","pubkeys")) )
$plan.Add( (JoinParts @($shared,"observability","otel")) )
$plan.Add( (JoinParts @($shared,"siem")) )
$plan.Add( (JoinParts @($shared,"bi-lake","curated","zero-ui")) )
$plan.Add( (JoinParts @($shared,"governance","controls","zero-ui")) )

# --- Execute plan ---
$plan = $plan | Select-Object -Unique
foreach($d in $plan){ MkdirSafe $d }

# RFC stamp if requested
if($StampUnclassified){
  foreach($b in @(
    (JoinParts @($tenant,"ingest","staging","unclassified",$StampUnclassified)),
    (JoinParts @($product,"ingest","staging","unclassified",$StampUnclassified)),
    (JoinParts @($laptop,"agent","tmp",$StampUnclassified))
  )){
    MkdirSafe $b
  }
}

Write-Host "Done." -ForegroundColor Green
if($DryRun){ Write-Host "DRY RUN: no directories were created." -ForegroundColor Yellow }
