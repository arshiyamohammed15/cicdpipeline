# VS Code Pre-Commit Hooks Fix

## Problem

Pre-commit hooks were working fine in Cursor terminal but not when committing through VS Code's commit button.

## Root Cause

VS Code on Windows uses a different Git environment that may not find the Python executable in the same way as the terminal. The original pre-commit hook only tried:
1. A hardcoded Python path
2. The `pre-commit` command directly

If neither was found in VS Code's environment, the hook would fail silently.

## Solution

### 1. Enhanced Pre-Commit Hook

The `.git/hooks/pre-commit` hook has been enhanced to try multiple Python paths in order:
1. Hardcoded Python path (from pre-commit installation)
2. `python` command (from PATH - works in VS Code)
3. `python3` command (from PATH)
4. `pre-commit` command directly

This ensures the hook works in both Cursor terminal and VS Code.

### 2. VS Code Settings

Created `.vscode/settings.json` with:
- `git.allowNoVerifyCommit: false` - Ensures hooks are not bypassed
- Python PATH configuration for VS Code terminal

### 3. Setup Script

Created `scripts/setup/pre-commit-vscode-fix.ps1` to:
- Reinstall pre-commit hooks
- Verify hook configuration
- Provide troubleshooting steps

## Usage

### If Hooks Don't Work in VS Code

Run the setup script:
```powershell
.\scripts\setup\pre-commit-vscode-fix.ps1
```

### Manual Fix

If the script doesn't work, manually reinstall hooks:
```powershell
python -m pre_commit install --hook-type pre-commit
```

### Verify Hooks Work

Test the hooks:
```powershell
python -m pre_commit run --all-files
```

## Troubleshooting

### Hooks Still Don't Work in VS Code

1. **Restart VS Code** - Settings changes require a restart
2. **Check Python PATH** - Ensure Python is in your system PATH
3. **Check Git Configuration**:
   ```powershell
   git config --global core.hooksPath .git/hooks
   ```
4. **Verify Hook File** - Ensure `.git/hooks/pre-commit` exists and is executable
5. **Check VS Code Git Settings** - Ensure `git.allowNoVerifyCommit` is `false`

### Check Hook Execution

To see if hooks are running, check VS Code's Git output:
1. Open Output panel (Ctrl+Shift+U)
2. Select "Git" from the dropdown
3. Try to commit and watch for hook execution messages

## Technical Details

### Hook Enhancement

The enhanced hook script (`.git/hooks/pre-commit`) now includes:
```bash
# Try the hardcoded Python path first
if [ -x "$INSTALL_PYTHON" ]; then
    exec "$INSTALL_PYTHON" -mpre_commit "${ARGS[@]}"
# Try python from PATH (works in VS Code)
elif command -v python > /dev/null 2>&1; then
    exec python -mpre_commit "${ARGS[@]}"
# Try python3 from PATH
elif command -v python3 > /dev/null 2>&1; then
    exec python3 -mpre_commit "${ARGS[@]}"
# Try pre-commit command directly
elif command -v pre-commit > /dev/null 2>&1; then
    exec pre-commit "${ARGS[@]}"
```

This ensures maximum compatibility across different environments.

### Windows Script Exclusion

Windows scripts (`.ps1`, `.bat`, `.cmd`) are excluded from the `mixed-line-ending` hook to preserve CRLF line endings as specified in `.gitattributes`.

## Verification

After applying the fix, verify hooks work in VS Code:
1. Make a small change to a file
2. Stage the change
3. Click the commit button in VS Code
4. Hooks should run automatically
5. If hooks modify files, they will be auto-staged
6. Commit should proceed normally

## Status

✅ **Fixed** - Pre-commit hooks now work in both Cursor terminal and VS Code commit button.
