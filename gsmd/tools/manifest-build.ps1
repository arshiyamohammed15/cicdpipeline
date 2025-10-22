<#
GSMD Manifest Builder
Builds a manifest over all snapshot.json files under -Root (the gsmd folder).
Usage:
  .\tools\manifest-build.ps1 -Root .\gsmd -OutDir .\gsmd\releases -Kid "KID:org.prod.ed25519:2025-10" [-SignScript .\tools\sign.ps1]
#>
param(
  [string]$Root = ".\gsmd",
  [string]$OutDir = ".\gsmd\releases",
  [string]$Kid,
  [string]$SignScript
)
$ErrorActionPreference="Stop"

function Sha256Hex([string]$p){ (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }
function MerkleRoot([string[]]$hexes){
  if($hexes.Count -eq 0){ return "" }
  $layer = $hexes
  while($layer.Count -gt 1){
    $next = @()
    for($i=0;$i -lt $layer.Count;$i+=2){
      $a=$layer[$i]; $b= if($i -eq $layer.Count-1){ $layer[$i] } else { $layer[$i+1] }
      $pair = [System.Text.Encoding]::UTF8.GetBytes($a+$b)
      $d = [System.Security.Cryptography.SHA256]::Create().ComputeHash($pair)
      $next += (-join ($d | ForEach-Object { $_.ToString("x2") }))
    }
    $layer = $next
  }
  return $layer[0]
}

$rootPath = (Resolve-Path -LiteralPath $Root).Path
$rootName = Split-Path -Leaf $rootPath
$snaps = Get-ChildItem -LiteralPath $rootPath -Recurse -Filter snapshot.json | Sort-Object FullName
if($snaps.Count -eq 0){ throw "No snapshot.json under $Root" }

$files = @(); $hashes = @()
foreach($f in $snaps){
  $rel = $f.FullName.Substring($rootPath.Length).TrimStart('\','/')
  $rel = ($rootName + "/" + $rel) -replace "\\","/"
  $sha = Sha256Hex $f.FullName
  $files += @{ path=$rel; sha256=$sha }
  $hashes += $sha
}

$root = MerkleRoot $hashes
$stamp = Get-Date -Format "yyyyMMdd.HHmmss"
$outDir = Join-Path -Path $OutDir -ChildPath $stamp
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$manifest = @{
  manifest_id   = "GSMD.$stamp"
  created_at    = (Get-Date).ToUniversalTime().ToString("o")
  files         = $files
  snapshot_count= $snaps.Count
  merkle_root   = $root
  signature     = "base64:PLACEHOLDER"
  kid           = $Kid
}

if($SignScript){
  $tmp = Join-Path $outDir "manifest.to.sign.json"
  ($manifest | ConvertTo-Json -Depth 40) | Out-File -FilePath $tmp -Encoding utf8 -NoNewline
  $out = Join-Path $outDir "sign.out.json"
  $p = Start-Process -FilePath "powershell" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$SignScript,"-InputJsonPath",$tmp) -Wait -PassThru -NoNewWindow -RedirectStandardOutput $out
  $sig = Get-Content -LiteralPath $out -Raw | ConvertFrom-Json
  if($sig.signature){ $manifest.signature = $sig.signature }
  if($sig.kid){ $manifest.kid = $sig.kid }
}

$manifestPath = Join-Path $outDir "manifest.json"
($manifest | ConvertTo-Json -Depth 40) | Out-File -FilePath $manifestPath -Encoding utf8 -NoNewline
Write-Host "Wrote manifest: $manifestPath"
Write-Host "Merkle root: $($manifest.merkle_root)"
