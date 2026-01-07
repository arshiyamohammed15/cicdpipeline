# Fix for pip install hanging issue

## Root Cause
`pip install -r requirements.txt` hangs because pip's dependency resolver tries to resolve 93+ pinned dependencies simultaneously, causing it to exceed resolution depth limits and hang.

## Solution Options (Choose One)

### Option 1: Use Batched Installation Script (RECOMMENDED)
```powershell
powershell -ExecutionPolicy Bypass -File install_dependencies_batched.ps1
```
This installs dependencies in 13 logical batches, preventing the resolver from getting stuck.

### Option 2: Use Minimal Requirements File
```powershell
python -m pip install -r requirements-minimal.txt
```
This file contains only top-level dependencies. Pip will automatically resolve transitive dependencies without hanging.

### Option 3: Use Fast Installation Script
```powershell
powershell -ExecutionPolicy Bypass -File install_dependencies_fast.ps1
```
This uses a two-pass approach: install packages first without deps, then resolve dependencies.

### Option 4: Install with Resolver Timeout (if pip version supports it)
```powershell
python -m pip install -r requirements.txt --resolver=backtracking --timeout=300
```

## Verification
After installation, verify with:
```powershell
python -m pip check
python -m pip list
```

## Why This Happens
- requirements.txt has 93+ pinned dependencies
- Many are transitive (automatically installed by top-level packages)
- Pip's resolver tries to satisfy all constraints simultaneously
- Complex dependency graphs cause exponential backtracking
- Resolver exceeds depth/time limits and hangs

## Prevention
- Use requirements-minimal.txt for future installations
- Only pin top-level dependencies in requirements.txt
- Let pip resolve transitive dependencies automatically
- Use pip-tools or poetry for better dependency management
