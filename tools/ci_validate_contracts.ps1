Param(
  [string]$RepoRoot = "$(Get-Location)"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Validating OpenAPI specs..." -ForegroundColor Cyan

function Invoke-OpenApiLint {
  param([string]$FilePath)
  if (-not (Test-Path $FilePath)) {
    throw "OpenAPI file not found: $FilePath"
  }
  # Use swagger-cli if available; otherwise ensure the file parses as YAML
  $swagger = Get-Command swagger-cli -ErrorAction SilentlyContinue
  if ($swagger) {
    & $swagger validate $FilePath
  } else {
    Write-Host "swagger-cli not found; performing YAML parse check only" -ForegroundColor Yellow
    Get-Content $FilePath | Out-String | ConvertFrom-Yaml | Out-Null
  }
}

Invoke-OpenApiLint -FilePath (Join-Path $RepoRoot "docs/design/openapi_sin.yaml")
Invoke-OpenApiLint -FilePath (Join-Path $RepoRoot "docs/design/openapi_validator.yaml")

Write-Host "Validating JSON Schemas..." -ForegroundColor Cyan

function Invoke-JsonLint {
  param([string]$FilePath)
  if (-not (Test-Path $FilePath)) {
    throw "JSON file not found: $FilePath"
  }
  $json = Get-Content $FilePath -Raw
  $null = $json | ConvertFrom-Json
  # optional: validate against draft-07 using ajv if available
  $ajv = Get-Command ajv -ErrorAction SilentlyContinue
  if ($ajv) {
    # ajv requires schema and data; here we just compile the schema itself
    & $ajv compile -s $FilePath | Out-Null
  }
}

Invoke-JsonLint -FilePath (Join-Path $RepoRoot "docs/design/events_budget_threshold.json")
Invoke-JsonLint -FilePath (Join-Path $RepoRoot "docs/design/events_sin_dlq.json")

Write-Host "Contract validation completed." -ForegroundColor Green
