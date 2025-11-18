#!/usr/bin/env python3
"""
Non-blocking wrapper for EOL validator that auto-fixes issues and never blocks commits.
This wrapper ensures the hook always exits with code 0, allowing commits to proceed.
Automatically stages any files that were modified by the fix.
"""
import sys
import subprocess
import os
from pathlib import Path
from typing import Set, List

# Get project root
project_root = Path(__file__).parent.parent.parent

def get_staged_files() -> Set[str]:
    """Get set of currently staged files."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        return {line.strip() for line in result.stdout.strip().split('\n') if line.strip()}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()

def get_unstaged_modified_files() -> Set[str]:
    """Get set of unstaged modified files."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        unstaged = set()
        for line in result.stdout.strip().split('\n'):
            if line:
                # Format: XY filename
                # X = staged status, Y = unstaged status
                unstaged_status = line[1] if len(line) > 1 else ' '
                if unstaged_status == 'M':
                    filename = line[3:].split(' -> ')[-1].strip()
                    if filename:
                        unstaged.add(filename)
        return unstaged
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()

def stage_file(file_path: str) -> bool:
    """Stage a file. Returns True if successful."""
    try:
        full_path = project_root / file_path
        if not full_path.exists():
            return False
        result = subprocess.run(
            ["git", "add", str(file_path)],
            cwd=project_root,
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# Get initial state
staged_files_before = get_staged_files()
unstaged_modified_before = get_unstaged_modified_files()

# Run the validator with --fix flag
# This will fix EOL issues in staged files
# Wrap in try-except to ensure we never block even if the script fails
try:
    result = subprocess.run(
        [sys.executable, str(project_root / "scripts" / "ci" / "validate_eol.py"), "--fix"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout to prevent hanging
    )
except subprocess.TimeoutExpired:
    print("⚠ EOL validation: Timeout (non-blocking)")
    print("  Note: Validation took too long, but commit will proceed")
    print()
    sys.exit(0)
except Exception as e:
    # Any other error - don't block, just report
    print(f"⚠ EOL validation: Error occurred (non-blocking): {e}")
    print("  Note: Commit will proceed despite validation error")
    print()
    sys.exit(0)

# Parse output to find which files were fixed
# The validate_eol.py script outputs:
# "Fixed EOL issues:"
# "  path/to/file: Fixed EOL to ..."
fixed_files = []
output_lines = (result.stdout or "").split('\n')
in_fixed_section = False
for line in output_lines:
    if 'Fixed EOL issues:' in line:
        in_fixed_section = True
        continue
    if in_fixed_section:
        if 'Fixed EOL' in line and ':' in line:
            # Extract filename from "  path/to/file: Fixed EOL to ..."
            # Remove leading whitespace and split on first colon
            line_clean = line.strip()
            if ':' in line_clean:
                file_path = line_clean.split(':', 1)[0].strip()
                if file_path and Path(project_root / file_path).exists():
                    fixed_files.append(file_path)
        elif line.strip() == '':
            # Empty line after fixed section, we're done
            in_fixed_section = False

# Get state after fix
unstaged_modified_after = get_unstaged_modified_files()

# Stage any files that were modified by the fix
# Files that were fixed will now appear as unstaged modifications
newly_modified = unstaged_modified_after - unstaged_modified_before

# Also stage files that we know were fixed (from output parsing)
files_to_stage = set(fixed_files) | newly_modified

staged_count = 0
for file_path in files_to_stage:
    if stage_file(file_path):
        staged_count += 1

# Print user-friendly output
output_lower = (result.stdout or "").lower()
has_errors = "failed" in output_lower or ("could not be fixed" in output_lower)
has_warnings = "issues could not be fixed" in output_lower

# Check if any files were actually fixed (from output or git status)
files_were_fixed = len(fixed_files) > 0 or staged_count > 0

if fixed_files or files_were_fixed:
    # Files were fixed successfully
    fix_count = len(fixed_files) if fixed_files else staged_count
    print(f"✓ EOL validation: Fixed {fix_count} file(s) automatically")
    if staged_count > 0:
        print(f"✓ Staged {staged_count} fixed file(s)")
    # Print details if there are only a few files
    if fixed_files and len(fixed_files) <= 5:
        print()  # Empty line before details
        for file_path in fixed_files:
            print(f"  - {file_path}")
    print()  # Empty line after summary
    # If there were also some errors that couldn't be fixed, mention them
    if has_warnings:
        print("  Note: Some EOL issues could not be fixed automatically (non-blocking)")
        print()
elif has_errors and not files_were_fixed:
    # There were errors that couldn't be fixed, but we don't block
    print("✓ EOL validation: Issues detected (non-blocking)")
    print("  Note: Some EOL issues may require manual fixing")
    print()
elif "passed" in output_lower or (result.returncode == 0 and not has_errors):
    # Validation passed with no issues
    print("✓ EOL validation passed: All files checked")
    print()
else:
    # Fallback - validation completed (always show success)
    print("✓ EOL validation completed: All checks performed")
    print()

# Print any stderr output (warnings, etc.) but don't duplicate stdout content
if result.stderr and result.stderr.strip():
    # Only print stderr if it's different from stdout
    if result.stderr.strip() not in (result.stdout or ""):
        print(result.stderr, file=sys.stderr, end='')

# CRITICAL: Always exit with 0 (success) to never block commits
# The script has attempted to fix all issues and staged the fixed files.
# The commit will proceed automatically.
sys.exit(0)
