#!/usr/bin/env python3
"""
EOL (End of Line) Validation Script

Validates that all files have correct line endings according to .gitattributes and .editorconfig.
This is a prevent-first implementation that blocks commits with incorrect EOL.

By default, validates staged files only (for pre-commit hook compatibility).
Use --unstaged to include unstaged files, or --all to check all files in repository.

Usage:
    python scripts/ci/validate_eol.py [--fix] [--files FILE1 FILE2 ...] [--all] [--unstaged]
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
import argparse

# Expected EOL mappings from .gitattributes
EXPECTED_EOL = {
    # LF files (most files)
    '.py': '\n',
    '.pyi': '\n',
    '.ts': '\n',
    '.tsx': '\n',
    '.js': '\n',
    '.jsx': '\n',
    '.json': '\n',
    '.yaml': '\n',
    '.yml': '\n',
    '.md': '\n',
    '.txt': '\n',
    '.html': '\n',
    '.css': '\n',
    '.sql': '\n',
    '.sh': '\n',
    '.bash': '\n',
    '.toml': '\n',
    '.ini': '\n',
    '.cfg': '\n',
    '.conf': '\n',
    '.config': '\n',
    # CRLF files (Windows scripts)
    '.ps1': '\r\n',
    '.psm1': '\r\n',
    '.psd1': '\r\n',
    '.bat': '\r\n',
    '.cmd': '\r\n',
}

# Binary file extensions (skip these)
BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.bmp', '.tiff', '.webp',
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv',
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',
    '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
    '.exe', '.dll', '.so', '.dylib', '.a', '.lib',
    '.pyc', '.pyo', '.pyd',
    '.class', '.jar', '.war', '.ear',
    '.ttf', '.otf', '.woff', '.woff2', '.eot',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
}

# Directories to skip
SKIP_DIRS = {
    '.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache',
    'dist', 'build', '.mypy_cache', '.ruff_cache', 'out', 'target'
}


def get_file_eol(file_path: Path) -> Optional[str]:
    """
    Detect the EOL character used in a file.

    Returns:
        '\n' for LF, '\r\n' for CRLF, '\r' for CR, or None if file is binary/empty
    """
    try:
        with open(file_path, 'rb') as f:
            content = f.read()

        if len(content) == 0:
            return None

        # Check for binary content
        if b'\x00' in content[:1024]:  # Check first 1KB for null bytes
            return None

        # Convert to text for EOL detection
        try:
            text = content.decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            # Try other encodings
            try:
                text = content.decode('latin-1', errors='strict')
            except UnicodeDecodeError:
                return None  # Likely binary

        # Detect EOL
        if '\r\n' in text:
            return '\r\n'
        elif '\n' in text:
            return '\n'
        elif '\r' in text:
            return '\r'
        else:
            return None  # No line endings found

    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return None


def get_expected_eol(file_path: Path) -> Optional[str]:
    """
    Get expected EOL for a file based on extension and .gitattributes rules.

    Returns:
        Expected EOL character or None if file type not specified
    """
    ext = file_path.suffix.lower()

    # Check explicit mappings
    if ext in EXPECTED_EOL:
        return EXPECTED_EOL[ext]

    # Default: LF for text files (per .editorconfig)
    # But we only validate files we know about
    return None


def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped."""
    # Check extension
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    # Check if in skip directory
    for part in file_path.parts:
        if part in SKIP_DIRS:
            return True

    return False


def get_staged_files() -> List[Path]:
    """Get list of staged files from git."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
            capture_output=True,
            text=True,
            check=True
        )

        files = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                file_path = Path(line.strip())
                if file_path.exists():
                    files.append(file_path)

        return files
    except subprocess.CalledProcessError:
        return []
    except FileNotFoundError:
        print("Warning: git not found, cannot get staged files", file=sys.stderr)
        return []


def get_unstaged_files() -> List[Path]:
    """Get list of unstaged files from git."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', '--diff-filter=ACMR'],
            capture_output=True,
            text=True,
            check=True
        )

        files = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                file_path = Path(line.strip())
                if file_path.exists():
                    files.append(file_path)

        return files
    except subprocess.CalledProcessError:
        return []
    except FileNotFoundError:
        print("Warning: git not found, cannot get unstaged files", file=sys.stderr)
        return []


def validate_file_eol(file_path: Path, fix: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate EOL for a single file.

    Returns:
        (is_valid, error_message)
    """
    if should_skip_file(file_path):
        return (True, None)

    expected_eol = get_expected_eol(file_path)
    if expected_eol is None:
        # File type not in our mapping, skip
        return (True, None)

    actual_eol = get_file_eol(file_path)
    if actual_eol is None:
        # Binary or empty file, skip
        return (True, None)

    if actual_eol != expected_eol:
        expected_name = 'CRLF' if expected_eol == '\r\n' else 'LF'
        actual_name = 'CRLF' if actual_eol == '\r\n' else ('LF' if actual_eol == '\n' else 'CR')
        error_msg = (
            f"{file_path}: Wrong EOL detected\n"
            f"  Expected: {repr(expected_eol)} ({expected_name})\n"
            f"  Found: {repr(actual_eol)} ({actual_name})"
        )

        if fix:
            # Fix the file
            try:
                with open(file_path, 'r', encoding='utf-8', newline='') as f:
                    content = f.read()

                # Normalize to expected EOL
                if expected_eol == '\n':
                    content = content.replace('\r\n', '\n').replace('\r', '\n')
                elif expected_eol == '\r\n':
                    content = content.replace('\r\n', '\n').replace('\r', '\n')
                    content = content.replace('\n', '\r\n')

                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    f.write(content)

                return (True, f"{file_path}: Fixed EOL to {expected_eol}")
            except Exception as e:
                return (False, f"{file_path}: Failed to fix EOL: {e}")

        return (False, error_msg)

    return (True, None)


def main():
    parser = argparse.ArgumentParser(
        description='Validate EOL (End of Line) characters in files'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Automatically fix EOL issues'
    )
    parser.add_argument(
        '--files',
        nargs='+',
        type=str,
        help='Specific files to validate (default: staged files)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Check all files in repository (not just staged)'
    )
    parser.add_argument(
        '--unstaged',
        action='store_true',
        help='Include unstaged files in validation (default: staged files only)'
    )

    args = parser.parse_args()

    # Get files to check
    if args.files:
        files_to_check = [Path(f) for f in args.files if Path(f).exists()]
    elif args.all:
        # Check all files in repo
        repo_root = Path(__file__).parent.parent.parent
        files_to_check = []
        for ext in EXPECTED_EOL.keys():
            files_to_check.extend(repo_root.rglob(f'*{ext}'))
        # Filter out skipped files
        files_to_check = [f for f in files_to_check if not should_skip_file(f)]
    else:
        # Default: check staged files only (for pre-commit hooks)
        staged_files = get_staged_files()
        if args.unstaged:
            # Include unstaged files if requested
            unstaged_files = get_unstaged_files()
            files_to_check = list(set(staged_files + unstaged_files))
        else:
            files_to_check = staged_files

    if not files_to_check:
        print("No files to validate")
        return 0

    # Validate files
    errors = []
    fixed = []

    for file_path in files_to_check:
        is_valid, message = validate_file_eol(file_path, fix=args.fix)

        if not is_valid:
            if args.fix and message and 'Fixed' in message:
                fixed.append(message)
            else:
                errors.append(message)

    # Report results
    if fixed:
        print("Fixed EOL issues:")
        for msg in fixed:
            print(f"  {msg}")
        print()

    if errors:
        print("EOL Validation Failed:")
        for error in errors:
            print(f"  {error}")
        print()
        print("To fix automatically, run: python scripts/ci/validate_eol.py --fix")
        return 1

    if not errors and not fixed:
        print(f"EOL validation passed: {len(files_to_check)} files checked")

    return 0


if __name__ == '__main__':
    sys.exit(main())
