<#
.SYNOPSIS
  ZeroUI Folder Structure Test Script

.DESCRIPTION
  Tests the folder structure created by create-folder-structure.ps1.
  Verifies that all required folders exist according to folder-business-rules.md v2.0.
  Structure: Four environments (development, integration, staging, production) under ZU_ROOT.
  Each environment contains tenant, product, and shared planes.
  IDE plane is under the specified environment (default: development).

.PARAMETER ZuRoot
  Base path for ZU_ROOT. If not provided, constructed from Drive and ProductName, or uses $env:ZU_ROOT environment variable.

.PARAMETER Drive
  Drive letter for ZU_ROOT path. Default: "D". Ignored if -ZuRoot is specified.

.PARAMETER ProductName
  Product name for ZU_ROOT path. Default: "ZeroUI". Ignored if -ZuRoot is specified.

.PARAMETER Environment
  Default environment name. Default: "development". Used for IDE plane location.

.PARAMETER CompatAliases
  If specified, tests for deprecated alias folders (e.g., meta/schema/).

.EXAMPLE
  .\test-folder-structure.ps1
  .\test-folder-structure.ps1 -Drive "D" -ProductName "ZeroUI"
  .\test-folder-structure.ps1 -Drive "E" -ProductName "MyProduct"
  .\test-folder-structure.ps1 -ZuRoot "D:\ZeroUI"
  .\test-folder-structure.ps1 -ZuRoot "D:\ZeroUI" -CompatAliases

.NOTES
  Version: 2.0
  Based on: folder-business-rules.md
#>

[CmdletBinding()]
param(
    [string]$ZuRoot,
    [string]$Drive = "D",
    [string]$ProductName = "ZeroUI",
    [string]$Environment = "development",
    [switch]$CompatAliases
)

$ErrorActionPreference = "Stop"

# Function to test if a path exists
function Test-FolderExists {
    param(
        [string]$Path,
        [string]$Description = ""
    )

    $exists = Test-Path $Path -PathType Container
    if($exists) {
        Write-Host "[PASS] $Path" -ForegroundColor Green
        if($Description) {
            Write-Verbose "  Description: $Description"
        }
        return $true
    } else {
        Write-Host "[FAIL] $Path" -ForegroundColor Red
        if($Description) {
            Write-Host "  Expected: $Description" -ForegroundColor Yellow
        }
        return $false
    }
}

# Function to test IDE Plane
function Test-IDEFolderStructure {
    param(
        [string]$BasePath,
        [ref]$TestResults,
        [ref]$TotalTests,
        [ref]$PassedTests
    )

    Write-Host "Testing IDE Plane folders..." -ForegroundColor Yellow

    $ideBase = Join-Path $BasePath "ide"
    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path $ideBase)) { @{Result=$true; Path=$ideBase} } else { @{Result=$false; Path=$ideBase} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $ideBase "receipts") -Description "Append-only signed JSONL receipts")) { @{Result=$true; Path="ide/receipts"} } else { @{Result=$false; Path="ide/receipts"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $ideBase "policy") -Description "Signed snapshots + current pointer, cache")) { @{Result=$true; Path="ide/policy"} } else { @{Result=$false; Path="ide/policy"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $ideBase "policy" "trust" "pubkeys") -Description "Public keys only")) { @{Result=$true; Path="ide/policy/trust/pubkeys"} } else { @{Result=$false; Path="ide/policy/trust/pubkeys"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $ideBase "config") -Description "Non-secret consent snapshots and configuration")) { @{Result=$true; Path="ide/config"} } else { @{Result=$false; Path="ide/config"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $ideBase "queue") -Description "Envelope refs only")) { @{Result=$true; Path="ide/queue"} } else { @{Result=$false; Path="ide/queue"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $ideBase "logs") -Description "Log files")) { @{Result=$true; Path="ide/logs"} } else { @{Result=$false; Path="ide/logs"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $ideBase "db") -Description "SQLite mirror, raw JSON")) { @{Result=$true; Path="ide/db"} } else { @{Result=$false; Path="ide/db"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $ideBase "llm") -Description "LLM prompts, tools, adapters, cache")) { @{Result=$true; Path="ide/llm"} } else { @{Result=$false; Path="ide/llm"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $ideBase "fingerprint") -Description "Non-secret device fingerprint")) { @{Result=$true; Path="ide/fingerprint"} } else { @{Result=$false; Path="ide/fingerprint"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $ideBase "tmp") -Description "Temporary; RFC stamping")) { @{Result=$true; Path="ide/tmp"} } else { @{Result=$false; Path="ide/tmp"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }
}

# Function to test Tenant Plane
function Test-TenantFolderStructure {
    param(
        [string]$BasePath,
        [switch]$CompatAliases,
        [ref]$TestResults,
        [ref]$TotalTests,
        [ref]$PassedTests
    )

    $tenantBase = Join-Path $BasePath "tenant"
    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path $tenantBase)) { @{Result=$true; Path="tenant"} } else { @{Result=$false; Path="tenant"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $tenantBase "evidence" "data") -Description "Merged receipts, manifests, checksums")) { @{Result=$true; Path="tenant/evidence/data"} } else { @{Result=$false; Path="tenant/evidence/data"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $tenantBase "evidence" "dlq") -Description "Dead letter queue")) { @{Result=$true; Path="tenant/evidence/dlq"} } else { @{Result=$false; Path="tenant/evidence/dlq"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $tenantBase "evidence" "watermarks") -Description "Per-consumer watermarks")) { @{Result=$true; Path="tenant/evidence/watermarks"} } else { @{Result=$false; Path="tenant/evidence/watermarks"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $tenantBase "ingest") -Description "RFC fallback")) { @{Result=$true; Path="tenant/ingest"} } else { @{Result=$false; Path="tenant/ingest"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $tenantBase "telemetry") -Description "Unified observability pattern")) { @{Result=$true; Path="tenant/telemetry"} } else { @{Result=$false; Path="tenant/telemetry"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $tenantBase "adapters") -Description "Webhooks and gateway logs")) { @{Result=$true; Path="tenant/adapters"} } else { @{Result=$false; Path="tenant/adapters"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $tenantBase "reporting" "marts") -Description "Analytics marts")) { @{Result=$true; Path="tenant/reporting/marts"} } else { @{Result=$false; Path="tenant/reporting/marts"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $tenantBase "policy" "snapshots") -Description "Signed snapshots")) { @{Result=$true; Path="tenant/policy/snapshots"} } else { @{Result=$false; Path="tenant/policy/snapshots"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $tenantBase "policy" "trust" "pubkeys") -Description "Public keys only")) { @{Result=$true; Path="tenant/policy/trust/pubkeys"} } else { @{Result=$false; Path="tenant/policy/trust/pubkeys"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $tenantBase "context") -Description "Tenant context stores")) { @{Result=$true; Path="tenant/context"} } else { @{Result=$false; Path="tenant/context"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    # Deprecated alias (only if -CompatAliases)
    if($CompatAliases) {
        $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $tenantBase "meta" "schema") -Description "Deprecated legacy alias")) { @{Result=$true; Path="tenant/meta/schema"} } else { @{Result=$false; Path="tenant/meta/schema"} }
        if($TestResults.Value[-1].Result) { $PassedTests.Value++ }
    }
}

# Function to test Product Plane
function Test-ProductFolderStructure {
    param(
        [string]$BasePath,
        [ref]$TestResults,
        [ref]$TotalTests,
        [ref]$PassedTests
    )

    $productBase = Join-Path $BasePath "product"
    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path $productBase)) { @{Result=$true; Path="product"} } else { @{Result=$false; Path="product"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $productBase "policy" "registry" "releases") -Description "Policy releases")) { @{Result=$true; Path="product/policy/registry/releases"} } else { @{Result=$false; Path="product/policy/registry/releases"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $productBase "policy" "registry" "templates") -Description "Policy templates")) { @{Result=$true; Path="product/policy/registry/templates"} } else { @{Result=$false; Path="product/policy/registry/templates"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $productBase "policy" "registry" "revocations") -Description "Policy revocations")) { @{Result=$true; Path="product/policy/registry/revocations"} } else { @{Result=$false; Path="product/policy/registry/revocations"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $productBase "evidence" "watermarks") -Description "Per-consumer watermarks")) { @{Result=$true; Path="product/evidence/watermarks"} } else { @{Result=$false; Path="product/evidence/watermarks"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $productBase "reporting" "tenants") -Description "Tenant aggregates")) { @{Result=$true; Path="product/reporting/tenants"} } else { @{Result=$false; Path="product/reporting/tenants"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $productBase "adapters") -Description "Gateway logs")) { @{Result=$true; Path="product/adapters"} } else { @{Result=$false; Path="product/adapters"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $productBase "telemetry") -Description "Unified observability pattern")) { @{Result=$true; Path="product/telemetry"} } else { @{Result=$false; Path="product/telemetry"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $productBase "policy" "trust" "pubkeys") -Description "Public keys")) { @{Result=$true; Path="product/policy/trust/pubkeys"} } else { @{Result=$false; Path="product/policy/trust/pubkeys"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }
}

# Function to test Shared Plane
function Test-SharedFolderStructure {
    param(
        [string]$BasePath,
        [ref]$TestResults,
        [ref]$TotalTests,
        [ref]$PassedTests
    )

    $sharedBase = Join-Path $BasePath "shared"
    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path $sharedBase)) { @{Result=$true; Path="shared"} } else { @{Result=$false; Path="shared"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "pki") -Description "All PKI files (public only)")) { @{Result=$true; Path="shared/pki"} } else { @{Result=$false; Path="shared/pki"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "telemetry") -Description "Unified observability pattern")) { @{Result=$true; Path="shared/telemetry"} } else { @{Result=$false; Path="shared/telemetry"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "siem" "detections") -Description "SIEM detections")) { @{Result=$true; Path="shared/siem/detections"} } else { @{Result=$false; Path="shared/siem/detections"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "bi-lake" "curated" "zero-ui") -Description "BI lake curated data")) { @{Result=$true; Path="shared/bi-lake/curated/zero-ui"} } else { @{Result=$false; Path="shared/bi-lake/curated/zero-ui"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "governance" "controls") -Description "Governance controls")) { @{Result=$true; Path="shared/governance/controls"} } else { @{Result=$false; Path="shared/governance/controls"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "governance" "attestations") -Description "Governance attestations")) { @{Result=$true; Path="shared/governance/attestations"} } else { @{Result=$false; Path="shared/governance/attestations"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "llm" "guardrails") -Description "LLM guardrails")) { @{Result=$true; Path="shared/llm/guardrails"} } else { @{Result=$false; Path="shared/llm/guardrails"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "llm" "routing") -Description "LLM routing")) { @{Result=$true; Path="shared/llm/routing"} } else { @{Result=$false; Path="shared/llm/routing"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "llm" "tools") -Description "LLM tools")) { @{Result=$true; Path="shared/llm/tools"} } else { @{Result=$false; Path="shared/llm/tools"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "provider-registry") -Description "Provider metadata, versions, allowlists")) { @{Result=$true; Path="shared/provider-registry"} } else { @{Result=$false; Path="shared/provider-registry"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "eval") -Description "Shared evaluation harness")) { @{Result=$true; Path="shared/eval"} } else { @{Result=$false; Path="shared/eval"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "security" "sbom") -Description "SBOM artifacts")) { @{Result=$true; Path="shared/security/sbom"} } else { @{Result=$false; Path="shared/security/sbom"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }

    $TotalTests.Value++; $TestResults.Value += if((Test-FolderExists -Path (Join-Path $sharedBase "security" "supply-chain") -Description "Supply chain attestation")) { @{Result=$true; Path="shared/security/supply-chain"} } else { @{Result=$false; Path="shared/security/supply-chain"} }
    if($TestResults.Value[-1].Result) { $PassedTests.Value++ }
}

# Determine ZU_ROOT
if(-not $ZuRoot) {
    if($env:ZU_ROOT) {
        $ZuRoot = $env:ZU_ROOT
        Write-Host "Using ZU_ROOT from environment: $ZuRoot" -ForegroundColor Cyan
    } else {
        # Construct ZU_ROOT from Drive and ProductName
        $ZuRoot = "${Drive}:\${ProductName}"
        Write-Host "Constructed ZU_ROOT from Drive and ProductName: $ZuRoot" -ForegroundColor Cyan
        Write-Host "  Drive: $Drive" -ForegroundColor Cyan
        Write-Host "  ProductName: $ProductName" -ForegroundColor Cyan
    }
}

Write-Host "`nTesting ZeroUI folder structure under: $ZuRoot" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

# Test if ZU_ROOT exists
if(-not (Test-Path $ZuRoot)) {
    Write-Host "[ERROR] ZU_ROOT does not exist: $ZuRoot" -ForegroundColor Red
    Write-Host "Please run create-folder-structure.ps1 first." -ForegroundColor Yellow
    exit 1
}

$testResults = @()
$totalTests = 0
$passedTests = 0

# ============================================================================
# Test four environments
# ============================================================================
$environments = @("development", "integration", "staging", "production")

foreach($env in $environments) {
    Write-Host "`nTesting $env environment..." -ForegroundColor Yellow

    $envPath = Join-Path $ZuRoot $env
    if(-not (Test-Path $envPath)) {
        Write-Host "[ERROR] Environment folder does not exist: $envPath" -ForegroundColor Red
        continue
    }

    # IDE plane only under the specified environment (default: development)
    if($env -eq $Environment) {
        Test-IDEFolderStructure -BasePath $envPath -TestResults ([ref]$testResults) -TotalTests ([ref]$totalTests) -PassedTests ([ref]$passedTests)
    }

    # Test Tenant, Product, and Shared planes for each environment
    Write-Host "  Testing Tenant Plane..." -ForegroundColor Cyan
    Test-TenantFolderStructure -BasePath $envPath -CompatAliases:$CompatAliases -TestResults ([ref]$testResults) -TotalTests ([ref]$totalTests) -PassedTests ([ref]$passedTests)

    Write-Host "  Testing Product Plane..." -ForegroundColor Cyan
    Test-ProductFolderStructure -BasePath $envPath -TestResults ([ref]$testResults) -TotalTests ([ref]$totalTests) -PassedTests ([ref]$passedTests)

    Write-Host "  Testing Shared Plane..." -ForegroundColor Cyan
    Test-SharedFolderStructure -BasePath $envPath -TestResults ([ref]$testResults) -TotalTests ([ref]$totalTests) -PassedTests ([ref]$passedTests)
}

# ============================================================================
# Summary
# ============================================================================
Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $($totalTests - $passedTests)" -ForegroundColor $(if(($totalTests - $passedTests) -eq 0) { "Green" } else { "Red" })

if($passedTests -eq $totalTests) {
    Write-Host "`nAll tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`nSome tests failed. Please review the output above." -ForegroundColor Red
    exit 1
}
