# Targeted Test Suite Execution Guide

## Overview

This guide provides detailed instructions for running targeted test suites for specific rule categories, such as exception handling vs TypeScript rules. It covers both Python and TypeScript test execution, with examples for common scenarios.

## Prerequisites

1. **Python Environment**: Python 3.9+ with dependencies installed
   ```bash
   python -m pip install ".[dev]"
   ```

2. **TypeScript Environment**: Node.js 18+ with dependencies installed
   ```bash
   cd src/edge-agent && npm install
   ```

3. **Storage Setup**: ZU_ROOT environment variable configured
   ```powershell
   $env:ZU_ROOT = "D:\ZeroUI\development"
   ```

---

## Test Suite Organization

### Python Test Suites

1. **Category-Based Tests**: `tests/test_constitution_*.py`
2. **Rule-Specific Tests**: `config/constitution/tests/test_*/`
3. **Integration Tests**: `tests/cccs/`, `tests/bdr/`, etc.
4. **Validator Tests**: `validator/rules/tests/`

### TypeScript Test Suites

1. **Edge Agent Storage**: `src/edge-agent/shared/storage/__tests__/`
2. **Platform Tests**: `tests/platform/`

---

## Running Exception Handling Tests

### Simple Test Suite

**Location**: `config/constitution/tests/test_exception_handling/test_rules_150_181_simple.py`

**Status**: ⚠️ **Note**: This test directory is referenced in README.md but may not exist yet. Use alternative test commands below.

**Run Command** (if directory exists):
```bash
python config/constitution/tests/test_exception_handling/test_rules_150_181_simple.py
```

**Alternative** (using general constitution tests):
```bash
python -m pytest tests -k "exception_handling" -v
```

**Expected Output**:
```
Running 18 tests...
test_rule_150_prevent_first ... OK
test_rule_151_error_codes ... OK
...
----------------------------------------------------------------------
Ran 18 tests in 0.5s

OK
```

### Comprehensive Test Suite

**Location**: `config/constitution/tests/test_exception_handling/test_rules_150_181_comprehensive.py`

**Status**: ⚠️ **Note**: This test directory is referenced in README.md but may not exist yet. Use alternative test commands below.

**Run Command** (if directory exists):
```bash
python config/constitution/tests/test_exception_handling/test_rules_150_181_comprehensive.py
```

**Alternative** (using general constitution tests):
```bash
python -m pytest tests/test_constitution_comprehensive_runner.py -k "exception" -v
```

**Expected Output**:
```
Running 100+ tests across 32 test classes...
test_TestRule150PreventFirst.test_input_validation ... OK
test_TestRule151ErrorCodes.test_canonical_codes ... OK
...
----------------------------------------------------------------------
Ran 100+ tests in 2.3s

OK
```

### Using pytest

**Run with pytest** (if test directory exists):
```bash
# Run all exception handling tests
python -m pytest config/constitution/tests/test_exception_handling/ -v

# Run specific test file
python -m pytest config/constitution/tests/test_exception_handling/test_rules_150_181_simple.py -v

# Run with coverage
python -m pytest config/constitution/tests/test_exception_handling/ --cov=validator.rules.exception_handling --cov-report=html
```

**Alternative** (using available tests):
```bash
# Run all exception handling tests
python -m pytest tests -k "exception_handling" -v

# Run with coverage on validator
python -m pytest tests/ -k "exception" --cov=validator.rules.exception_handling --cov-report=html
```

### Filter by Rule Number

**Run specific rule tests** (if test directory exists):
```bash
# Test Rule 150 only
python -m pytest config/constitution/tests/test_exception_handling/ -k "rule_150" -v

# Test Rules 150-155
python -m pytest config/constitution/tests/test_exception_handling/ -k "rule_15[0-5]" -v
```

**Alternative** (using available tests):
```bash
# Test exception handling rules via validator
python -m pytest tests/ -k "exception" -v
```

---

## Running TypeScript Tests

### Simple Test Suite

**Location**: `config/constitution/tests/test_typescript_rules/test_rules_182_215_simple.py`

**Status**: ⚠️ **Note**: This test directory is referenced in README.md but may not exist yet. Use alternative test commands below.

**Run Command** (if directory exists):
```bash
python config/constitution/tests/test_typescript_rules/test_rules_182_215_simple.py
```

**Alternative** (using general constitution tests):
```bash
python -m pytest tests -k "typescript" -v
```

**Expected Output**:
```
Running 20+ tests...
test_rule_182_no_any ... OK
test_rule_183_null_undefined ... OK
...
----------------------------------------------------------------------
Ran 20+ tests in 0.8s

OK
```

### Comprehensive Test Suite

**Location**: `config/constitution/tests/test_typescript_rules/test_rules_182_215_comprehensive.py`

**Status**: ⚠️ **Note**: This test directory is referenced in README.md but may not exist yet. Use alternative test commands below.

**Run Command** (if directory exists):
```bash
python config/constitution/tests/test_typescript_rules/test_rules_182_215_comprehensive.py
```

**Alternative** (using general constitution tests):
```bash
python -m pytest tests/test_constitution_comprehensive_runner.py -k "typescript" -v
```

### Using pytest

**Run with pytest**:
```bash
# Run all TypeScript rule tests
python -m pytest config/constitution/tests/test_typescript_rules/ -v

# Run specific test file
python -m pytest config/constitution/tests/test_typescript_rules/test_rules_182_215_simple.py -v

# Run with coverage
python -m pytest config/constitution/tests/test_typescript_rules/ --cov=validator.rules.typescript --cov-report=html
```

### Filter by Rule Number

**Run specific rule tests**:
```bash
# Test Rule 182 only
python -m pytest config/constitution/tests/test_typescript_rules/ -k "rule_182" -v

# Test Rules 182-190
python -m pytest config/constitution/tests/test_typescript_rules/ -k "rule_18[2-9]|rule_190" -v
```

### TypeScript/Edge Agent Tests

**Location**: `src/edge-agent/shared/storage/__tests__/`

**Run Command**:
```bash
cd src/edge-agent
npm test -- --testPathPattern=storage
```

**Run with coverage**:
```bash
cd src/edge-agent
npm test -- --coverage --testPathPattern=storage
```

---

## Running Storage Governance Tests

### Python Tests

**Location**: `tests/bdr/test_storage.py`

**Run Command**:
```bash
python -m pytest tests/bdr/test_storage.py -v
```

### PowerShell Scaffold Tests

**Location**: `storage-scripts/tests/`

**Run Command**:
```powershell
# Run all scaffold tests
pwsh storage-scripts/tests/test-all-scripts.ps1

# Run specific environment test
pwsh storage-scripts/tests/test-create-development.ps1
```

### Edge Agent Storage Tests (TypeScript)

**Location**: `src/edge-agent/shared/storage/__tests__/`

**Run Command**:
```bash
cd src/edge-agent
npm test -- shared/storage
```

---

## Running Category-Based Test Suites

### All Constitution Tests

**Run all constitution tests**:
```bash
python -m pytest tests -k "constitution" -v
```

**Expected Output**:
```
tests/test_constitution_all_files.py::ConstitutionStructureTests::test_all_files_exist ... OK
tests/test_constitution_all_files.py::ConstitutionRuleStructureTests::test_all_rules_have_required_fields ... OK
...
----------------------------------------------------------------------
Ran 200+ tests in 15.2s

OK
```

### Exception Handling Only

**Run exception handling category tests**:
```bash
python -m pytest tests -k "exception_handling" -v
```

### TypeScript Only

**Run TypeScript category tests**:
```bash
python -m pytest tests -k "typescript" -v
```

### Storage Governance Only

**Run storage governance category tests**:
```bash
python -m pytest tests -k "storage_governance" -v
```

---

## Running Validator-Specific Tests

### Exception Handling Validator

**Test the validator directly**:
```bash
# Run validator tests
python -m pytest validator/rules/tests/ -k "exception" -v

# Test validator with sample code
python -c "
from validator.rules.exception_handling import ExceptionHandlingValidator
validator = ExceptionHandlingValidator()
violations = validator.validate_all(None, 'def test(): pass', 'test.py')
print(f'Found {len(violations)} violations')
"
```

### TypeScript Validator

**Test the validator directly**:
```bash
# Run validator tests
python -m pytest validator/rules/tests/ -k "typescript" -v

# Test validator with sample code
python -c "
from validator.rules.typescript import TypeScriptValidator
validator = TypeScriptValidator()
violations = validator.validate_all(None, 'const x: any = 1;', 'test.ts')
print(f'Found {len(violations)} violations')
"
```

### Storage Governance Validator

**Test the validator directly**:
```bash
# Run validator tests
python -m pytest validator/rules/tests/ -k "storage" -v

# Test validator with sample code
python -c "
from validator.rules.storage_governance import StorageGovernanceValidator
validator = StorageGovernanceValidator()
violations = validator.validate_all(None, 'path = \"storage/MyFolder\"', 'test.py')
print(f'Found {len(violations)} violations')
"
```

---

## Running Integration Tests

### CCCS (Cross-Cutting Concern Services)

**Location**: `tests/cccs/`

**Run Command**:
```bash
# Run all CCCS tests
python -m pytest tests/cccs/ -v

# Run specific CCCS test
python -m pytest tests/cccs/test_receipts.py -v
```

### BDR (Backup/Disaster Recovery)

**Location**: `tests/bdr/`

**Run Command**:
```bash
# Run all BDR tests
python -m pytest tests/bdr/ -v

# Run storage-specific BDR tests
python -m pytest tests/bdr/test_storage.py -v
```

---

## Advanced Test Execution

### Parallel Execution

**Run tests in parallel**:
```bash
# Install pytest-xdist
python -m pip install pytest-xdist

# Run with 4 workers
python -m pytest tests/ -n 4 -k "exception_handling"
```

### Coverage Reports

**Generate coverage reports**:
```bash
# Exception handling coverage
python -m pytest config/constitution/tests/test_exception_handling/ \
  --cov=validator.rules.exception_handling \
  --cov-report=html \
  --cov-report=term

# TypeScript coverage
python -m pytest config/constitution/tests/test_typescript_rules/ \
  --cov=validator.rules.typescript \
  --cov-report=html \
  --cov-report=term

# Storage governance coverage
python -m pytest tests/bdr/test_storage.py \
  --cov=validator.rules.storage_governance \
  --cov-report=html \
  --cov-report=term
```

### Verbose Output

**Get detailed test output**:
```bash
# Very verbose
python -m pytest tests/ -k "exception_handling" -vv

# Show print statements
python -m pytest tests/ -k "exception_handling" -v -s
```

### Stop on First Failure

**Stop on first failure**:
```bash
python -m pytest tests/ -k "exception_handling" -x
```

### Run Last Failed Tests

**Run only failed tests from last run**:
```bash
python -m pytest tests/ --lf -k "exception_handling"
```

---

## Test Execution Examples

### Example 1: Test Exception Handling Rules 150-155

```bash
# Run specific rule range
python -m pytest config/constitution/tests/test_exception_handling/ \
  -k "rule_15[0-5]" \
  -v \
  --tb=short
```

### Example 2: Test TypeScript Rules 182-190

```bash
# Run specific rule range
python -m pytest config/constitution/tests/test_typescript_rules/ \
  -k "rule_18[2-9]|rule_190" \
  -v \
  --tb=short
```

### Example 3: Compare Exception Handling vs TypeScript

```bash
# Run both suites and compare
python -m pytest config/constitution/tests/test_exception_handling/ \
  config/constitution/tests/test_typescript_rules/ \
  -v \
  --tb=line \
  -k "not comprehensive"
```

### Example 4: Test Storage Governance with Edge Agent

```bash
# Run Python storage tests
python -m pytest tests/bdr/test_storage.py -v

# Run TypeScript storage tests
cd src/edge-agent && npm test -- shared/storage

# Run PowerShell scaffold tests
pwsh storage-scripts/tests/test-folder-structure.ps1
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Exception Handling Rules

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: python -m pip install ".[dev]"
      - run: python -m pytest config/constitution/tests/test_exception_handling/ -v
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    stages {
        stage('Test Exception Handling') {
            steps {
                sh 'python -m pytest config/constitution/tests/test_exception_handling/ -v'
            }
        }
        stage('Test TypeScript') {
            steps {
                sh 'python -m pytest config/constitution/tests/test_typescript_rules/ -v'
            }
        }
    }
}
```

---

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure project root is in PYTHONPATH
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Missing Dependencies**: Install dev dependencies
   ```bash
   python -m pip install ".[dev]"
   ```

3. **ZU_ROOT Not Set**: Set environment variable
   ```powershell
   $env:ZU_ROOT = "D:\ZeroUI\development"
   ```

4. **Test Discovery Issues**: Use explicit paths
   ```bash
   python -m pytest config/constitution/tests/test_exception_handling/test_rules_150_181_simple.py -v
   ```

### Debug Mode

**Run with debug output**:
```bash
python -m pytest tests/ -k "exception_handling" -vv --tb=long --capture=no
```

---

## Summary

| Test Suite | Command | Location |
|------------|---------|----------|
| Exception Handling (Simple) | `python config/constitution/tests/test_exception_handling/test_rules_150_181_simple.py` | `config/constitution/tests/test_exception_handling/` |
| Exception Handling (Comprehensive) | `python -m pytest config/constitution/tests/test_exception_handling/ -v` | `config/constitution/tests/test_exception_handling/` |
| TypeScript (Simple) | `python config/constitution/tests/test_typescript_rules/test_rules_182_215_simple.py` | `config/constitution/tests/test_typescript_rules/` |
| TypeScript (Comprehensive) | `python -m pytest config/constitution/tests/test_typescript_rules/ -v` | `config/constitution/tests/test_typescript_rules/` |
| Storage Governance (Python) | `python -m pytest tests/bdr/test_storage.py -v` | `tests/bdr/test_storage.py` |
| Storage Governance (TypeScript) | `cd src/edge-agent && npm test -- shared/storage` | `src/edge-agent/shared/storage/__tests__/` |
| Storage Governance (PowerShell) | `pwsh storage-scripts/tests/test-folder-structure.ps1` | `storage-scripts/tests/` |
| All Constitution Tests | `python -m pytest tests -k "constitution" -v` | `tests/test_constitution_*.py` |

---

**Last Updated**: 2025-01-XX  
**Maintained By**: ZeroUI 2.0 Constitution Team  
**Related Docs**: `docs/guides/RULE_CATEGORY_VALIDATOR_TEST_MAPPING.md`

