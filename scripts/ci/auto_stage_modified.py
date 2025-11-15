#!/usr/bin/env python3
"""
Auto-stage hook that stages any files modified by previous pre-commit hooks.
This prevents the "unstaged files detected" warning after hooks auto-fix files.
"""
import sys
import subprocess
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent.parent

# Get list of unstaged modified files and stage them
result = subprocess.run(
    ["git", "status", "--porcelain"],
    cwd=project_root,
    capture_output=True,
    text=True
)

unstaged_modified = []
for line in result.stdout.strip().split('\n'):
    if line:
        # Format: XY filename
        # X = staged status, Y = unstaged status
        # We want files that are modified but not staged (Y = M, X = space or ?)
        staged_status = line[0] if len(line) > 0 else ' '
        unstaged_status = line[1] if len(line) > 1 else ' '

        # If unstaged is M (modified), stage it (handles both ' M' and 'MM' cases)
        if unstaged_status == 'M':
            filename = line[3:].split(' -> ')[-1].strip()
            if filename:
                unstaged_modified.append(filename)

# Stage any unstaged modified files
if unstaged_modified:
    for file_path in unstaged_modified:
        full_path = project_root / file_path
        if full_path.exists():
            subprocess.run(
                ["git", "add", str(file_path)],
                cwd=project_root,
                capture_output=True
            )

# Always exit successfully
sys.exit(0)
