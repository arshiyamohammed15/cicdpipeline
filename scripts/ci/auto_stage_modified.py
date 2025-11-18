#!/usr/bin/env python3
"""
Auto-stage hook that stages any files modified by previous pre-commit hooks.
This prevents the "unstaged files detected" warning after hooks auto-fix files.
This is a safety net to ensure all modified files are staged.
"""
import sys
import os
import subprocess
from pathlib import Path
from typing import Set

# Get project root
project_root = Path(__file__).parent.parent.parent

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
                # We want files that are modified but not staged (Y = M)
                unstaged_status = line[1] if len(line) > 1 else ' '

                # If unstaged is M (modified), stage it
                # Handles: ' M' (modified, not staged), 'MM' (modified in both)
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

# Get unstaged modified files
# Wrap in try-except to ensure we never block even if git commands fail
try:
    unstaged_modified = get_unstaged_modified_files()

    # Stage any unstaged modified files
    staged_count = 0
    if unstaged_modified:
        for file_path in unstaged_modified:
            if stage_file(file_path):
                staged_count += 1

    # Silently succeed - this is a safety net hook
    # Only print if we actually staged something (for debugging)
    # In normal operation, this should be quiet
    if staged_count > 0:
        # Only log if in verbose mode (check environment variable)
        if os.environ.get('PRE_COMMIT_VERBOSE') == '1':
            print(f"Auto-staged {staged_count} modified file(s)")
except Exception as e:
    # Any error - don't block, just silently continue
    # This is a safety net hook, so failures shouldn't block commits
    if os.environ.get('PRE_COMMIT_VERBOSE') == '1':
        print(f"Auto-stage hook: Error (non-blocking): {e}")

# Always exit successfully - this is a safety net hook
sys.exit(0)
