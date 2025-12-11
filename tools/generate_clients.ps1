Param(
  [string]$RepoRoot = "$(Get-Location)",
  [string]$OutputDir = "$(Get-Location)\\generated-clients",
  [string]$Generator = "typescript-fetch"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Dir {
  param([string]$Path)
  if (-not (Test-Path $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

Ensure-Dir -Path $OutputDir

$openapi = Get-Command openapi-generator -ErrorAction SilentlyContinue
if (-not $openapi) {
  throw "openapi-generator CLI not found in PATH. Install from https://openapi-generator.tech/."
}

$specs = @(
  @{ Name = "sin"; Path = Join-Path $RepoRoot "docs/design/openapi_sin.yaml" },
  @{ Name = "validator"; Path = Join-Path $RepoRoot "docs/design/openapi_validator.yaml" }
)

foreach ($spec in $specs) {
  if (-not (Test-Path $spec.Path)) {
    throw "Spec not found: $($spec.Path)"
  }
  $outPath = Join-Path $OutputDir $spec.Name
  Ensure-Dir -Path $outPath
  & $openapi generate `
    -i $spec.Path `
    -g $Generator `
    -o $outPath
}

Write-Host "Client generation completed under $OutputDir" -ForegroundColor Green
