#!/usr/bin/env python3
"""
Pre-commit hook to update test manifest.

This hook ensures the test manifest is always up to date before commits.
Can be used with pre-commit framework or standalone.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def update_manifest():
    """Update test manifest."""
    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "tools" / "test_registry" / "generate_manifest.py"), "--update"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            print("Warning: Failed to update test manifest:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return False
        
        print("Test manifest updated successfully")
        return True
    except Exception as e:
        print(f"Warning: Could not update test manifest: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = update_manifest()
    sys.exit(0 if success else 1)

