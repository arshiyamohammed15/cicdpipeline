<#
.SYNOPSIS
  Comprehensive Test Suite for ZeroUI Database Scripts

.DESCRIPTION
  Tests database schema pack and Phase 0 stub application scripts:
  - apply_schema_pack.ps1
  - apply_phase0_stubs.ps1
  - verify_schema_equivalence.ps1

.PARAMETER TestRoot
  Root directory for test execution. Default: uses temp directory.

.PARAMETER SkipDocker
  If specified, skips tests that require Docker.

.EXAMPLE
  .\test_db_scripts.ps1
  .\test_db_scripts.ps1 -SkipDocker
#>

[CmdletBinding()]
param(
    [string]$TestRoot = "",
    [switch]$SkipDocker
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = (Get-Item $PSScriptRoot).Parent.Parent.Parent.Parent.FullName
$scriptsRoot = Join-Path $repoRoot "scripts\db"
$applySchemaPack = Join-Path $scriptsRoot "apply_schema_pack.ps1"
$applyPhase0Stubs = Join-Path $scriptsRoot "apply_phase0_stubs.ps1"
$verifySchemaEquivalence = Join-Path $scriptsRoot "verify_schema_equivalence.ps1"

# Test results
$testResults = @()
$totalTests = 0
$passedTests = 0
$failedTests = 0

function Record-TestResult {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Message = "",
        [string]$ErrorDetails = ""
    )

    $script:totalTests++
    if ($Passed) {
        $script:passedTests++
        Write-Host "  ✓ $TestName" -ForegroundColor Green
        if ($Message) {
            Write-Host "    $Message" -ForegroundColor Gray
        }
    } else {
        $script:failedTests++
        Write-Host "  ✗ $TestName" -ForegroundColor Red
        if ($Message) {
            Write-Host "    $Message" -ForegroundColor Yellow
        }
        if ($ErrorDetails) {
            Write-Host "    Error: $ErrorDetails" -ForegroundColor Red
        }
    }

    $script:testResults += @{
        TestName = $TestName
        Passed = $Passed
        Message = $Message
        ErrorDetails = $ErrorDetails
    }
}

Write-Host "=== ZeroUI Database Scripts Test Suite ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Script file existence
Write-Host "Test Group: Script File Existence" -ForegroundColor Yellow
Record-TestResult -TestName "apply_schema_pack.ps1 exists" -Passed (Test-Path $applySchemaPack)
Record-TestResult -TestName "apply_phase0_stubs.ps1 exists" -Passed (Test-Path $applyPhase0Stubs)
Record-TestResult -TestName "verify_schema_equivalence.ps1 exists" -Passed (Test-Path $verifySchemaEquivalence)

# Test 2: Script syntax validation
Write-Host ""
Write-Host "Test Group: Script Syntax Validation" -ForegroundColor Yellow

$syntaxTests = @(
    @{Script = $applySchemaPack; Name = "apply_schema_pack.ps1 syntax"},
    @{Script = $applyPhase0Stubs; Name = "apply_phase0_stubs.ps1 syntax"},
    @{Script = $verifySchemaEquivalence; Name = "verify_schema_equivalence.ps1 syntax"}
)

foreach ($test in $syntaxTests) {
    try {
        $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $test.Script -Raw), [ref]$null)
        Record-TestResult -TestName $test.Name -Passed $true
    } catch {
        Record-TestResult -TestName $test.Name -Passed $false -ErrorDetails $_.Exception.Message
    }
}

# Test 3: Function definitions
Write-Host ""
Write-Host "Test Group: Function Definitions" -ForegroundColor Yellow

$applySchemaPackText = Get-Content $applySchemaPack -Raw
Record-TestResult -TestName "apply_schema_pack.ps1 has Apply-Pg function" -Passed ($applySchemaPackText -match "function\s+Apply-Pg")

$applyPhase0StubsText = Get-Content $applyPhase0Stubs -Raw
Record-TestResult -TestName "apply_phase0_stubs.ps1 has Apply-PgPhase0Stub function" -Passed ($applyPhase0StubsText -match "function\s+Apply-PgPhase0Stub")

$verifySchemaEquivalenceText = Get-Content $verifySchemaEquivalence -Raw
Record-TestResult -TestName "verify_schema_equivalence.ps1 has Normalize-PgDump function" -Passed ($verifySchemaEquivalenceText -match "function\s+Normalize-PgDump")
Record-TestResult -TestName "verify_schema_equivalence.ps1 has Get-PgSchemaDump function" -Passed ($verifySchemaEquivalenceText -match "function\s+Get-PgSchemaDump")

# Test 4: Required file references
Write-Host ""
Write-Host "Test Group: Required File References" -ForegroundColor Yellow

$schemaPackRoot = Join-Path $repoRoot "infra\db\schema_pack"
$pgMigration = Join-Path $schemaPackRoot "migrations\pg\001_core.sql"
$contract = Join-Path $schemaPackRoot "canonical_schema_contract.json"

Record-TestResult -TestName "Postgres migration file exists" -Passed (Test-Path $pgMigration)
Record-TestResult -TestName "Canonical schema contract exists" -Passed (Test-Path $contract)

# Test 5: Phase 0 stub migration files
Write-Host ""
Write-Host "Test Group: Phase 0 Stub Migration Files" -ForegroundColor Yellow

$bkgTenant = Join-Path $repoRoot "infra\db\migrations\tenant\002_bkg_phase0.sql"
$bkgProduct = Join-Path $repoRoot "infra\db\migrations\product\003_bkg_phase0.sql"
$bkgShared = Join-Path $repoRoot "infra\db\migrations\shared\002_bkg_phase0.sql"
$qaCacheProduct = Join-Path $repoRoot "infra\db\migrations\product\004_semantic_qa_cache_phase0.sql"

Record-TestResult -TestName "BKG tenant migration exists" -Passed (Test-Path $bkgTenant)
Record-TestResult -TestName "BKG product migration exists" -Passed (Test-Path $bkgProduct)
Record-TestResult -TestName "BKG shared migration exists" -Passed (Test-Path $bkgShared)
Record-TestResult -TestName "Semantic Q&A Cache product migration exists" -Passed (Test-Path $qaCacheProduct)

# Test 6: Script content validation (positive cases)
Write-Host ""
Write-Host "Test Group: Script Content Validation" -ForegroundColor Yellow

Record-TestResult -TestName "apply_schema_pack.ps1 references all 3 Postgres containers" -Passed (
    ($applySchemaPackText -match "zeroui-postgres-tenant") -and
    ($applySchemaPackText -match "zeroui-postgres-product") -and
    ($applySchemaPackText -match "zeroui-postgres-shared")
)

Record-TestResult -TestName "apply_schema_pack.ps1 references IDE Postgres" -Passed (
    ($applySchemaPackText -match "zeroui-postgres-ide") -and
    ($applySchemaPackText -match "ZEROUI_IDE_DB_URL")
)

Record-TestResult -TestName "apply_phase0_stubs.ps1 references BKG migrations" -Passed (
    ($applyPhase0StubsText -match "002_bkg_phase0") -or
    ($applyPhase0StubsText -match "bkg_phase0")
)

Record-TestResult -TestName "apply_phase0_stubs.ps1 references Semantic Q&A Cache migration" -Passed (
    ($applyPhase0StubsText -match "004_semantic_qa_cache_phase0") -or
    ($applyPhase0StubsText -match "semantic_qa_cache")
)

Record-TestResult -TestName "verify_schema_equivalence.ps1 compares all Postgres DBs" -Passed (
    ($verifySchemaEquivalenceText -match "tenant") -and
    ($verifySchemaEquivalenceText -match "product") -and
    ($verifySchemaEquivalenceText -match "shared")
)

Record-TestResult -TestName "verify_schema_equivalence.ps1 checks schema_version" -Passed (
    ($verifySchemaEquivalenceText -match "meta\.schema_version") -or
    ($verifySchemaEquivalenceText -match "meta__schema_version")
)

# Test 7: Error handling (negative cases)
Write-Host ""
Write-Host "Test Group: Error Handling" -ForegroundColor Yellow

Record-TestResult -TestName "apply_schema_pack.ps1 checks for missing files" -Passed (
    ($applySchemaPackText -match "Test-Path") -or
    ($applySchemaPackText -match "if.*Missing")
)

Record-TestResult -TestName "apply_schema_pack.ps1 checks for missing containers" -Passed (
    ($applySchemaPackText -match "docker ps") -or
    ($applySchemaPackText -match "container.*not found")
)

Record-TestResult -TestName "apply_phase0_stubs.ps1 checks for missing files" -Passed (
    ($applyPhase0StubsText -match "Test-Path")
)


# Summary
Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor $(if ($failedTests -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failedTests -eq 0) {
    Write-Host "=== ALL TESTS PASSED ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=== SOME TESTS FAILED ===" -ForegroundColor Red
    exit 1
}

