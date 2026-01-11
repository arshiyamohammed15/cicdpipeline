param(
  [string]$RootDrive = "D",
  [string]$RootFolder = "zero-ui-local-servers",
  [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Join-Root([string]$Drive, [string]$Folder) {
  return (Join-Path -Path ($Drive + ":\") -ChildPath $Folder)
}

function Fail([string]$Msg) {
  Write-Host "ERROR: $Msg" -ForegroundColor Red
  exit 1
}

$RootPath = Join-Root $RootDrive $RootFolder
Write-Host "Target root: $RootPath"

if (-not (Test-Path -LiteralPath $RootPath)) {
  Write-Host "SKIP: Target root does not exist."
  exit 0
}

# Safety: confirm expected plane roots exist before deletion (unless -Force)
$expectedPlaneDirs = @("IDE","Tenant","Product","Shared")
$missingPlanes = @()
foreach ($p in $expectedPlaneDirs) {
  $pp = Join-Path -Path $RootPath -ChildPath $p
  if (-not (Test-Path -LiteralPath $pp)) { $missingPlanes += $p }
}

if (-not $Force) {
  Write-Host ""
  Write-Host "About to REMOVE this folder tree (recursive):" -ForegroundColor Yellow
  Write-Host "  $RootPath" -ForegroundColor Yellow

  if ($missingPlanes.Count -gt 0) {
    Write-Host ""
    Write-Host "WARNING: Some expected plane folders are missing under the target root:" -ForegroundColor Yellow
    $missingPlanes | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    Write-Host "If this is not the intended folder, cancel now." -ForegroundColor Yellow
  }

  $ans = Read-Host "Type YES to confirm uninstall"
  if ($ans -ne "YES") {
    Write-Host "Cancelled."
    exit 0
  }
}

Remove-Item -LiteralPath $RootPath -Recurse -Force
Write-Host "DONE: Uninstalled (deleted) $RootPath"
