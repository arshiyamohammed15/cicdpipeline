#!/usr/bin/env python3
"""Wrapper script for constitution validator that handles pre-commit hook execution."""
import sys
import subprocess
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent.parent

# Run the validator
result = subprocess.run(
    [sys.executable, str(project_root / "tools" / "enhanced_cli.py"), "--directory", "."],
    cwd=project_root,
    capture_output=True,
    text=True
)

# If no files found or no violations, pass
if "No Python files found" in result.stdout or result.returncode == 0:
    sys.exit(0)

# Otherwise, pass through the exit code
sys.exit(result.returncode)
