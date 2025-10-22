<#
GSMD Check (lite)
Usage: .\tools\gsmd-check.ps1 -Root .\gsmd
#>
param([string]$Root = ".\gsmd",[switch]$VerboseOutput)
$ErrorActionPreference = "Stop"
function Get-Json($p){ try{ Get-Content -LiteralPath $p -Raw | ConvertFrom-Json }catch{ throw "Invalid JSON: $p"}}
function Get-FileSha256Tag($p){ $h=(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower(); "sha256:$h" }
function Require-Keys($obj,$p,$keys){ foreach($k in $keys){ if(-not ($obj.PSObject.Properties.Name -contains $k)){ throw "Missing key '$k' in $p"}}}
$fails=@(); $snaps=Get-ChildItem -LiteralPath $Root -Recurse -Filter snapshot.json
if($snaps.Count -eq 0){ Write-Host "No snapshot.json files under $Root"; exit 1}
foreach($f in $snaps){
  $rel = Resolve-Path -LiteralPath $f.FullName | Split-Path -NoQualifier
  try{
    $j = Get-Json $f.FullName
    Require-Keys $j $rel @("snapshot_id","module_id","slug","version","schema_version","policy_version_ids","snapshot_hash","signature","kid","effective_from","evaluation_points","messages","rollout","observability","privacy","evidence","receipts","tests")
    if($j.snapshot_id -notmatch "^SNAP\.M\d{2}\.[a-z0-9_\.]+\.(v|V)\d+$"){ throw "Invalid snapshot_id in $rel" }
    if($j.module_id -notmatch "^M\d{2}$"){ throw "Invalid module_id in $rel" }
    if($j.snapshot_hash -notmatch "^sha256:[0-9a-f]{64}$"){ throw "Invalid snapshot_hash format in $rel" }
    $calc = Get-FileSha256Tag $f.FullName
    if($calc -ne $j.snapshot_hash){ throw "snapshot_hash mismatch in $rel (found=$($j.snapshot_hash) expected=$calc)" }
    if($VerboseOutput){ Write-Host "OK $rel" }
  } catch { $fails += $_.Exception.Message }
}
if($fails.Count -gt 0){ Write-Host "GSMD CHECK FAILED:" -ForegroundColor Red; $fails | % { Write-Host " - $_" -ForegroundColor Red }; exit 2 }
Write-Host "GSMD CHECK PASSED ($($snaps.Count) files)"; exit 0
