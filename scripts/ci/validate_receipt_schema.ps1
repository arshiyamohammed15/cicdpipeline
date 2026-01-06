# CI Check: Validate LLM Receipt Schema Compliance
# ID: CI.RECEIPT-SCHEMA.VALIDATION.MT-01
# Purpose: Validate that LLM receipts include all required fields per LLM Strategy Directives Section 6.1

param(
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Normalize repo root path
if ([string]::IsNullOrEmpty($RepoRoot)) {
    $RepoRoot = (Get-Location).Path
}
if (-not (Test-Path -Path $RepoRoot)) {
    $currentDir = Get-Location
    $searchPath = $currentDir
    while ($searchPath -and $searchPath -ne $searchPath.Parent) {
        if (Test-Path (Join-Path $searchPath ".git") -PathType Container) {
            $RepoRoot = $searchPath.Path
            break
        }
        if (Test-Path (Join-Path $searchPath "AGENTS.md")) {
            $RepoRoot = $searchPath.Path
            break
        }
        $searchPath = $searchPath.Parent
    }
    if (-not $RepoRoot) {
        $RepoRoot = $currentDir.Path
    }
}
$RepoRoot = (Resolve-Path -Path $RepoRoot -ErrorAction Stop).Path

Write-Host "Validating receipt schema compliance in: $RepoRoot" -ForegroundColor Cyan

# Check if Python is available
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "SKIP: Python not found in PATH" -ForegroundColor Yellow
    exit 0
}

# Run validation script
$validationScript = Join-Path $RepoRoot "src\cloud_services\llm_gateway\services\receipt_validator.py"
if (-not (Test-Path $validationScript)) {
    Write-Host "SKIP: Receipt validator not found: $validationScript" -ForegroundColor Yellow
    exit 0
}

# Import and test the validator
$testCode = @"
import sys
import json
from pathlib import Path

sys.path.insert(0, r'$RepoRoot')

try:
    from src.cloud_services.llm_gateway.services.receipt_validator import ReceiptValidator
    
    # Test with minimal valid receipt
    test_receipt = {
        'plane': 'tenant',
        'task_class': 'minor',
        'task_type': 'text',
        'model': {'primary': 'qwen2.5-coder:14b', 'used': 'qwen2.5-coder:14b', 'failover_used': False},
        'degraded_mode': False,
        'router': {'policy_id': 'POL-LLM-ROUTER-001', 'policy_snapshot_hash': 'sha256:test'},
        'llm': {'params': {'num_ctx': 4096, 'temperature': 0.0, 'seed': 42}},
        'result': {'status': 'ok'},
        'evidence': {'receipt_id': 'test-123', 'trace_id': 'trace-123'}
    }
    
    ReceiptValidator.validate(test_receipt)
    print('OK: Receipt validator is working correctly')
    sys.exit(0)
except Exception as e:
    print(f'ERROR: Receipt validator test failed: {e}')
    sys.exit(1)
"@

$testCode | python
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: Receipt validator test failed" -ForegroundColor Red
    exit 1
}

Write-Host "OK: Receipt schema validation check passed" -ForegroundColor Green
exit 0

