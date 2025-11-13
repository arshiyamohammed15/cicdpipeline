# EOL Enforcement - Windows/PowerShell Setup Guide

## Windows-Specific Installation

### Option 1: Using Python Directly (No Pre-commit Framework)

Since `pip` and `pre-commit` may not be in PATH on Windows, use Python directly:

#### Step 1: Verify Python Installation
```powershell
python --version
# Should show Python 3.x.x
```

#### Step 2: Install Pre-commit (if needed)
```powershell
python -m pip install pre-commit
```

#### Step 3: Install Git Hooks (Alternative - Direct Hook)
```powershell
# Copy the pre-commit hook directly
Copy-Item scripts\git-hooks\pre-commit-eol .git\hooks\pre-commit -Force

# Make executable (if needed)
# Git hooks should be executable by default on Windows
```

#### Step 4: Test EOL Validation
```powershell
# Validate staged files
python scripts\ci\validate_eol.py

# Fix issues automatically
python scripts\ci\validate_eol.py --fix

# Check all files
python scripts\ci\validate_eol.py --all
```

### Option 2: Using Pre-commit Framework (After Installation)

#### Step 1: Install Pre-commit
```powershell
python -m pip install pre-commit
```

#### Step 2: Verify Installation
```powershell
python -m pre_commit --version
```

#### Step 3: Install Hooks
```powershell
python -m pre_commit install
```

#### Step 4: Test Hooks
```powershell
python -m pre_commit run eol-validator --all-files
```

### Option 3: Manual Git Hook (Simplest for Windows)

#### Step 1: Create Pre-commit Hook
```powershell
# Navigate to .git/hooks
cd .git\hooks

# Create pre-commit file
@"
#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.ci.validate_eol import validate_file_eol, get_staged_files

staged_files = get_staged_files()
if not staged_files:
    sys.exit(0)

errors = []
for file_path in staged_files:
    is_valid, error_msg = validate_file_eol(file_path, fix=False)
    if not is_valid and error_msg:
        errors.append(error_msg)

if errors:
    print("EOL Validation Failed:")
    for error in errors:
        print(f"  {error}")
    print("\nTo fix: python scripts\ci\validate_eol.py --fix")
    sys.exit(1)

print(f"EOL validation passed: {len(staged_files)} files")
sys.exit(0)
"@ | Out-File -FilePath pre-commit -Encoding utf8
```

#### Step 2: Test the Hook
```powershell
# Create test file with wrong EOL
"line1`r`nline2`r`n" | Out-File -FilePath test_crlf.py -Encoding utf8 -NoNewline

# Stage and try to commit
git add test_crlf.py
git commit -m "test eol"
# Should be blocked

# Fix and commit
python scripts\ci\validate_eol.py --fix
git add test_crlf.py
git commit -m "test eol"
# Should succeed
```

## Windows-Specific Notes

### PowerShell vs CMD
- Use `python` not `pip` directly
- Use `python -m pip` instead of `pip`
- Use `python -m pre_commit` instead of `pre-commit`

### Path Separators
- Use backslashes `\` in PowerShell paths
- Use forward slashes `/` in Python code (works on Windows too)

### Line Ending Testing
```powershell
# Create file with CRLF (Windows style)
"line1`r`nline2`r`n" | Out-File -FilePath test.py -Encoding utf8

# Create file with LF (Unix style)
"line1`nline2`n" | Out-File -FilePath test.py -Encoding utf8 -NoNewline
```

## Quick Start (Windows)

### Minimal Setup (No Pre-commit Framework)
```powershell
# 1. Test validation script
python scripts\ci\validate_eol.py

# 2. If issues found, fix them
python scripts\ci\validate_eol.py --fix

# 3. Manually validate before commits
python scripts\ci\validate_eol.py
```

### Full Setup (With Pre-commit Framework)
```powershell
# 1. Install pre-commit
python -m pip install pre-commit

# 2. Install hooks
python -m pre_commit install

# 3. Test
python -m pre_commit run --all-files
```

## Troubleshooting Windows Issues

### Issue: "pip is not recognized"
**Solution**: Use `python -m pip` instead of `pip`

### Issue: "pre-commit is not recognized"
**Solution**: Use `python -m pre_commit` instead of `pre-commit`

### Issue: Git hook not running
**Solution**:
1. Check hook exists: `Test-Path .git\hooks\pre-commit`
2. Check hook is executable (should be automatic on Windows)
3. Test manually: `python .git\hooks\pre-commit`

### Issue: PowerShell encoding issues
**Solution**: Use `-Encoding utf8` when creating files:
```powershell
"content" | Out-File -FilePath file.py -Encoding utf8
```
