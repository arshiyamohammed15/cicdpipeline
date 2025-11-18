#!/usr/bin/env python3
"""
Pre-stage hook that stages ALL modified files before other pre-commit hooks run.
This prevents stash conflicts by ensuring all files are staged upfront.
"""
import sys
import os
import subprocess
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent.parent

def stage_all_modified_files() -> int:
    """Stage ALL modified files (both staged and unstaged). Returns count staged."""
    try:
        # First, get current staged files count
        before_result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        before_count = len([f for f in before_result.stdout.strip().split('\n') if f.strip()])

        # Stage all modified files (staged + unstaged)
        result = subprocess.run(
            ["git", "add", "-u"],  # -u stages modified files, doesn't add new files
            cwd=project_root,
            capture_output=True,
            check=True
        )

        # Count how many files are now staged
        after_result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        after_count = len([f for f in after_result.stdout.strip().split('\n') if f.strip()])

        return after_count - before_count

    except (subprocess.CalledProcessError, FileNotFoundError):
        return 0

# Stage ALL modified files before other hooks run
try:
    staged_count = stage_all_modified_files()
    if staged_count > 0:
        print(f"✓ Pre-commit: Staged {staged_count} modified file(s) to prevent conflicts")
        print("  This ensures hooks can modify files without stash conflicts")
        print()
except Exception as e:
    print(f"Warning: Pre-stage hook failed: {e}")
    print("Continuing with commit anyway...")
    print()

# Always exit successfully - this prevents blocking commits
sys.exit(0)
