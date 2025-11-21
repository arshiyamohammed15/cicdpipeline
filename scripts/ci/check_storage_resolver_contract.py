#!/usr/bin/env python3
"""
CI Check: Storage Resolver Contract Enforcement

Ensures that all ZU_ROOT and plane path logic uses BaseStoragePathResolver
instead of direct path computation. This enforces the single API contract.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Patterns that indicate direct path computation (forbidden)
FORBIDDEN_PATTERNS = [
    # Direct ZU_ROOT path construction
    (r'ZU_ROOT\s*[+\-*/]\s*["\']', 'Direct ZU_ROOT path concatenation'),
    (r'process\.env\.ZU_ROOT\s*[+\-*/]\s*["\']', 'Direct ZU_ROOT env var path construction'),
    (r'os\.getenv\(["\']ZU_ROOT["\']\)\s*[+\-*/]\s*["\']', 'Direct ZU_ROOT os.getenv path construction'),
    (r'os\.environ\[["\']ZU_ROOT["\']\]\s*[+\-*/]\s*["\']', 'Direct ZU_ROOT os.environ path construction'),
    
    # Direct plane path construction
    (r'["\']/(?:ide|tenant|product|shared)/', 'Direct plane path construction'),
    (r'path.*join.*["\'](?:ide|tenant|product|shared)', 'Direct plane path join'),
    (r'Path\(.*\)\s*/\s*["\'](?:ide|tenant|product|shared)', 'Direct plane Path construction'),
    
    # Direct receipt path construction without resolver
    (r'receipts/.*ZU_ROOT', 'Direct receipt path without resolver'),
    (r'ZU_ROOT.*receipts/', 'Direct receipt path without resolver'),
]

# Allowed patterns (exceptions)
ALLOWED_PATTERNS = [
    r'BaseStoragePathResolver',  # The resolver itself
    r'resolveIdePath|resolveTenantPath|resolveProductPath|resolveSharedPath',  # Resolver methods
    r'resolveReceiptPath|resolvePolicyPath',  # Resolver methods
    r'getZuRoot\(\)',  # Resolver getter
    r'from.*BaseStoragePathResolver',  # Imports
    r'extends.*BaseStoragePathResolver',  # Class extension
    r'class.*BaseStoragePathResolver',  # Class definition
    r'#.*ZU_ROOT',  # Comments
    r'//.*ZU_ROOT',  # Comments
    r'/\*.*ZU_ROOT.*\*/',  # Comments
    r'description.*ZU_ROOT',  # Documentation strings
    r'ZU_ROOT.*environment.*variable',  # Documentation
    r'ZU_ROOT.*required',  # Documentation
    r'process\.env\.ZU_ROOT\s*[?:]',  # Conditional checks (not path construction)
    r'os\.getenv\(["\']ZU_ROOT["\']\)\s*[?:]',  # Conditional checks
    r'assert.*ZU_ROOT',  # Assertions
    r'if.*ZU_ROOT',  # Conditional checks
    r'ZU_ROOT.*undefined',  # Undefined checks
    r'ZU_ROOT.*null',  # Null checks
    r'ZU_ROOT.*empty',  # Empty checks
    r'ZU_ROOT.*must',  # Error messages
    r'ZU_ROOT.*required',  # Error messages
    r'ZU_ROOT.*configured',  # Configuration checks
    r'\.test\.|\.spec\.',  # Test files (may have test-specific patterns)
    r'__tests__',  # Test directories
    r'__mocks__',  # Mock directories
]

# Files to exclude
EXCLUDE_PATTERNS = [
    r'.*BaseStoragePathResolver\.(ts|js)$',  # The resolver itself
    r'.*\.test\.(ts|js|py)$',  # Test files (handled separately)
    r'.*\.spec\.(ts|js|py)$',  # Spec files
    r'.*__tests__.*',  # Test directories
    r'.*__mocks__.*',  # Mock directories
    r'.*node_modules.*',
    r'.*\.git.*',
    r'.*__pycache__.*',
    r'.*\.pyc$',
    r'.*dist.*',
    r'.*build.*',
]

# Directories to exclude
EXCLUDE_DIRS = {
    'node_modules',
    '.git',
    '__pycache__',
    '.pytest_cache',
    'venv',
    'env',
    '.venv',
    'dist',
    'build',
}


def should_exclude_file(file_path: Path) -> bool:
    """Check if file should be excluded from scanning."""
    # Check directory exclusions
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return True

    # Check pattern exclusions
    file_str = str(file_path)
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, file_str, re.IGNORECASE):
            return True

    return False


def is_allowed_pattern(line: str) -> bool:
    """Check if line matches an allowed pattern."""
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Scan a file for forbidden storage path patterns."""
    violations = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                for pattern, description in FORBIDDEN_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Check if it's an allowed pattern
                        if not is_allowed_pattern(line):
                            violations.append((
                                line_num,
                                description,
                                line.strip()
                            ))
    except Exception as e:
        print(f"Warning: Could not scan {file_path}: {e}", file=sys.stderr)

    return violations


def scan_directory(root_dir: Path) -> List[Tuple[Path, int, str, str]]:
    """Scan directory recursively for violations."""
    all_violations = []

    for file_path in root_dir.rglob('*'):
        if not file_path.is_file():
            continue

        if should_exclude_file(file_path):
            continue

        # Only scan source files
        if file_path.suffix not in ['.py', '.ts', '.tsx', '.js', '.jsx']:
            continue

        violations = scan_file(file_path)
        for line_num, description, context in violations:
            all_violations.append((file_path, line_num, description, context))

    return all_violations


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent.parent.parent

    print("=" * 80)
    print("STORAGE RESOLVER CONTRACT ENFORCEMENT")
    print("=" * 80)
    print(f"Scanning: {root_dir}")
    print()
    print("Checking for direct ZU_ROOT/plane path computation...")
    print("All path logic must use BaseStoragePathResolver API")
    print()

    violations = scan_directory(root_dir)

    if violations:
        print(f"[FAIL] FOUND {len(violations)} VIOLATIONS")
        print()
        print("Direct ZU_ROOT or plane path computation violates storage resolver contract.")
        print("All path logic must use BaseStoragePathResolver methods:")
        print("  - resolveIdePath(), resolveTenantPath(), resolveProductPath(), resolveSharedPath()")
        print("  - resolveReceiptPath(), resolvePolicyPath()")
        print()

        for file_path, line_num, description, context in violations:
            rel_path = file_path.relative_to(root_dir)
            print(f"  {rel_path}:{line_num}")
            print(f"    Issue: {description}")
            print(f"    Context: {context[:100]}")
            print()

        print("=" * 80)
        print("FAILED: Storage resolver contract violations detected")
        print("=" * 80)
        return 1
    else:
        print("[OK] No storage resolver contract violations detected")
        print("All path logic uses BaseStoragePathResolver API")
        print("=" * 80)
        return 0


if __name__ == '__main__':
    sys.exit(main())

