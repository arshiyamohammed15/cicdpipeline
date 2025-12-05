# Root Cause Fix: Test Import Issues

## Problem Identified

**Root Cause**: Python cannot import from hyphenated directory names (`integration-adapters`, `identity-access-management`). This caused:
1. Inconsistent import patterns across test files
2. Duplicate module setup logic in every conftest.py
3. Fragile path calculations that break easily
4. 84+ collection errors

## Solution Implemented

### 1. Centralized Root Conftest (`tests/conftest.py`)

All module package setup is handled in ONE place:
- Maps hyphenated directory names to Python package names
- Sets up package structures for all modules
- Loads key modules automatically
- Creates subpackages (services, database, etc.)

### 2. Standardized Module-Specific Conftest Files

All module conftest.py files now:
- Rely on root conftest.py for package setup
- Only ensure module path is in sys.path
- No duplicate logic

### 3. Comprehensive Import Fix Script

`tools/fix_all_test_imports_comprehensive.py`:
- Fixes all hyphenated imports to use Python package names
- Standardizes relative imports
- Fixes path issues in root test files

## Usage

1. Root conftest.py automatically sets up all modules
2. Tests use Python package names: `from identity_access_management.main import app`
3. No manual path manipulation needed in test files

## Maintenance

- Add new modules to `MODULE_MAPPINGS` in root conftest.py
- Run `python tools/fix_all_test_imports_comprehensive.py` after adding tests
- All conftest files follow the same pattern

