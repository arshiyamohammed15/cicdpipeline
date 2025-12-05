# Test Reorganization Tools

Tools for reorganizing and migrating tests to the standardized structure.

## Tools

### 1. `create_structure.py`

Creates the standardized test directory structure.

**Usage**:
```bash
# Create structure
python tools/test_reorganization/create_structure.py

# Dry run (show what would be created)
python tools/test_reorganization/create_structure.py --dry-run
```

**What it does**:
- Creates `tests/cloud_services/` directory structure
- Creates directories for all modules (client, product, shared services)
- Creates test category directories (unit, integration, security, performance, resilience)
- Creates `conftest.py` templates
- Creates `README.md` templates

### 2. `migrate_tests.py`

Migrates existing tests to new structure.

**Usage**:
```bash
# Migrate all tests (dry run first)
python tools/test_reorganization/migrate_tests.py --dry-run

# Migrate all tests
python tools/test_reorganization/migrate_tests.py

# Migrate specific file
python tools/test_reorganization/migrate_tests.py --file path/to/test_file.py
```

**What it does**:
- Reads test manifest to find all test files
- Determines target location based on module and test type
- Copies test files to new structure
- Preserves original files (for safety)

### 3. `update_imports.py`

Updates imports in migrated test files.

**Usage**:
```bash
# Update imports (dry run first)
python tools/test_reorganization/update_imports.py --dry-run

# Update imports
python tools/test_reorganization/update_imports.py

# Update specific directory
python tools/test_reorganization/update_imports.py --directory tests/cloud_services/shared_services/identity_access_management
```

**What it does**:
- Updates import paths in test files
- Removes old path manipulation code
- Updates path calculations for new structure
- Adds comments about conftest.py handling imports

## Migration Workflow

### Step 1: Create Structure
```bash
python tools/test_reorganization/create_structure.py
```

### Step 2: Migrate Tests (Dry Run)
```bash
python tools/test_reorganization/migrate_tests.py --dry-run
```

### Step 3: Migrate Tests
```bash
python tools/test_reorganization/migrate_tests.py
```

### Step 4: Update Imports
```bash
python tools/test_reorganization/update_imports.py
```

### Step 5: Verify Tests
```bash
# Run tests in new location
pytest tests/cloud_services/shared_services/identity_access_management/ -v

# Update manifest
python tools/test_registry/generate_manifest.py
```

### Step 6: Remove Old Tests (After Verification)
```bash
# Remove old test directories after verifying new tests work
# (Manual step - be careful!)
```

## Module Name Mappings

The tools handle module name normalization:

**Hyphenated → Underscored**:
- `identity-access-management` → `identity_access_management`
- `key-management-service` → `key_management_service`
- `signal-ingestion-normalization` → `signal_ingestion_normalization`

## Test Category Detection

Tests are automatically categorized based on:
- File path (contains "security", "performance", etc.)
- File name (starts with "test_security", "test_performance", etc.)
- Default: "unit" if unclear

## Safety Features

1. **Dry Run Mode**: Always test with `--dry-run` first
2. **Preserves Originals**: Migration copies files, doesn't move them
3. **Verification**: Run tests after migration before removing old files
4. **Backup**: Consider backing up before migration

## Troubleshooting

### Import Errors After Migration

```bash
# Update imports
python tools/test_reorganization/update_imports.py

# Clear cache
python tools/test_registry/clear_cache.py

# Regenerate manifest
python tools/test_registry/generate_manifest.py
```

### Tests Not Found

```bash
# Verify structure exists
python tools/test_reorganization/create_structure.py

# Check test location
pytest --collect-only tests/cloud_services/
```

### Duplicate Tests

If tests exist in both old and new locations:
1. Verify new tests work
2. Remove old test directories
3. Update pytest configuration

