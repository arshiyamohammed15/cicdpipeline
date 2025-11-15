#!/usr/bin/env python3
"""Non-blocking wrapper for constitution validator that reports violations but does not block commits.
Automatically stages any files that were modified by the validator."""
import sys
import subprocess
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent.parent

# Get list of modified files before running validator
def get_modified_files():
    """Get list of modified files from git status."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    modified = []
    for line in result.stdout.strip().split('\n'):
        if line and (line[0] == 'M' or line[1] == 'M'):
            # Extract filename (handle renames)
            filename = line[3:].split(' -> ')[-1].strip()
            if filename:
                modified.append(filename)
    return modified

# Get files before validation
files_before = set(get_modified_files())

# Run the validator
result = subprocess.run(
    [sys.executable, str(project_root / "tools" / "enhanced_cli.py"), "--directory", "."],
    cwd=project_root,
    capture_output=True,
    text=True
)

# Get files after validation and stage any newly modified files
files_after = set(get_modified_files())
newly_modified = files_after - files_before

# Auto-stage any files that were modified by the validator
if newly_modified:
    for file_path in newly_modified:
        full_path = project_root / file_path
        if full_path.exists():
            subprocess.run(
                ["git", "add", str(file_path)],
                cwd=project_root,
                capture_output=True
            )

# Always exit with 0 (success) to not block commits
# Output is still shown to inform the user of any violations
if result.stdout:
    print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

# Exit with 0 regardless of validation result (non-blocking)
sys.exit(0)
