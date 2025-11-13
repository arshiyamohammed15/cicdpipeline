# EOL (End of Line) Enforcement Guide

## Overview

This guide explains how to proactively enforce correct line endings (EOL) in the ZeroUI 2.0 codebase using a prevent-first approach.

## Current Configuration

### 1. `.gitattributes` (292 lines)
- **Purpose**: Git-level line ending normalization
- **Location**: Project root
- **Behavior**: Automatically normalizes line endings on commit/checkout
- **Default**: `* text=auto` (auto-detect)
- **Most files**: `eol=lf` (Unix-style)
- **Windows scripts**: `eol=crlf` (`.ps1`, `.bat`, `.cmd`)

### 2. `.editorconfig` (58 lines)
- **Purpose**: Editor-level formatting enforcement
- **Location**: Project root
- **Behavior**: Configures editors to use LF by default
- **Default**: `end_of_line = lf`
- **Windows exceptions**: Batch files use `crlf`

## Prevent-First Implementation

### Installation Steps

#### Option 1: Pre-commit Framework (Recommended)

1. **Install pre-commit**:
   ```bash
   pip install pre-commit
   ```

2. **Install hooks**:
   ```bash
   pre-commit install
   ```

3. **Test the hook**:
   ```bash
   pre-commit run --all-files
   ```

#### Option 2: Git Hook (Manual)

1. **Copy the hook**:
   ```bash
   cp scripts/git-hooks/pre-commit-eol .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```

2. **Test the hook**:
   ```bash
   # Stage a file with wrong EOL
   git add some_file.py
   git commit -m "test"
   # Should block if EOL is wrong
   ```

#### Option 3: Manual Validation Script

1. **Validate staged files**:
   ```bash
   python scripts/ci/validate_eol.py
   ```

2. **Fix issues automatically**:
   ```bash
   python scripts/ci/validate_eol.py --fix
   ```

3. **Check all files**:
   ```bash
   python scripts/ci/validate_eol.py --all
   ```

## Validation Script

**File**: `scripts/ci/validate_eol.py`

**Features**:
- Validates EOL against `.gitattributes` rules
- Detects LF, CRLF, and CR line endings
- Can auto-fix EOL issues
- Skips binary files automatically
- Works with staged files or specific file lists

**Usage**:
```bash
# Validate staged files
python scripts/ci/validate_eol.py

# Fix issues automatically
python scripts/ci/validate_eol.py --fix

# Check specific files
python scripts/ci/validate_eol.py --files file1.py file2.ts

# Check all files in repository
python scripts/ci/validate_eol.py --all
```

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  eol-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Validate EOL
        run: |
          python scripts/ci/validate_eol.py --all
```

### Jenkins

Add to `Jenkinsfile`:

```groovy
stage('EOL Validation') {
    steps {
        sh '''
            python scripts/ci/validate_eol.py --all
        '''
    }
}
```

## Expected EOL by File Type

### LF (Unix-style) - Most Files
- Source code: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`
- Configuration: `.json`, `.yaml`, `.yml`, `.toml`
- Documentation: `.md`, `.txt`
- Web files: `.html`, `.css`
- Shell scripts: `.sh`, `.bash`

### CRLF (Windows-style) - Windows Scripts Only
- PowerShell: `.ps1`, `.psm1`, `.psd1`
- Batch files: `.bat`, `.cmd`

## Troubleshooting

### Issue: Hook not running

**Solution**:
1. Check hook is executable: `chmod +x .git/hooks/pre-commit`
2. Verify pre-commit is installed: `pre-commit --version`
3. Reinstall hooks: `pre-commit install --install-hooks`

### Issue: Files have wrong EOL

**Solution**:
1. Auto-fix: `python scripts/ci/validate_eol.py --fix`
2. Re-stage files: `git add -u`
3. Commit again

### Issue: Binary files being checked

**Solution**:
- Binary files are automatically skipped
- If a file is incorrectly detected, add its extension to `BINARY_EXTENSIONS` in `validate_eol.py`

## Verification

### Test EOL Validation

1. **Create test file with wrong EOL**:
   ```bash
   printf "line1\r\nline2\r\n" > test_crlf.py
   ```

2. **Stage and try to commit**:
   ```bash
   git add test_crlf.py
   git commit -m "test"
   # Should be blocked
   ```

3. **Fix and commit**:
   ```bash
   python scripts/ci/validate_eol.py --fix
   git add test_crlf.py
   git commit -m "test"
   # Should succeed
   ```

## Summary

**Prevent-First EOL Enforcement**:
1. ✅ `.gitattributes` - Normalizes on commit
2. ✅ `.editorconfig` - Configures editors
3. ✅ Pre-commit hook - Blocks commits with wrong EOL
4. ✅ Validation script - Manual checking/fixing
5. ✅ CI integration - Validates in pipelines

**Result**: EOL issues are prevented before they enter the repository.
