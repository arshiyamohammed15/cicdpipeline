<#
GSMD Manifest Verifier
Verifies file hashes and recomputes Merkle root. Optional external signature check.
Usage:
  .\tools\manifest-verify.ps1 -Root . -Manifest .\gsmd\releases\<ts>\manifest.json [-VerifyScript .\tools\verify.ps1]
#>
param(
  [string]$Root = ".",
  [string]$Manifest,
  [string]$VerifyScript
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

if(-not $Manifest){ throw "Provide -Manifest path" }
$man = Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json

$bad = @(); $hex = @()
foreach($f in $man.files){
  $p = Join-Path -Path $Root -ChildPath $f.path
  if(-not (Test-Path -LiteralPath $p)){ $bad += "Missing: $($f.path)"; continue }
  $sha = Sha256Hex $p
  if($sha -ne $f.sha256){ $bad += "Hash mismatch: $($f.path)" }
  $hex += $sha
}
if($bad.Count -gt 0){
  Write-Host "FILE FAILURES:" -ForegroundColor Red
  $bad | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
  exit 2
}

$root = MerkleRoot $hex
if($root -ne $man.merkle_root){
  Write-Host "MERKLE ROOT MISMATCH (found=$root expected=$($man.merkle_root))" -ForegroundColor Red
  exit 3
}

if($VerifyScript){
  $tmp = "$Manifest.verify.in.json"
  ($man | ConvertTo-Json -Depth 40) | Out-File -FilePath $tmp -Encoding utf8 -NoNewline
  $out = "$Manifest.verify.out.json"
  $p = Start-Process -FilePath "powershell" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$VerifyScript,"-InputJsonPath",$tmp) -Wait -PassThru -NoNewWindow -RedirectStandardOutput $out
  $v = Get-Content -LiteralPath $out -Raw | ConvertFrom-Json
  if(-not $v.verified){ throw "Signature verification script returned false" }
}

Write-Host "MANIFEST VERIFIED OK"
exit 0
