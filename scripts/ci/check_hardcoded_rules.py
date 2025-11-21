#!/usr/bin/env python3
"""
CI Check: Detect Hardcoded Rule Counts

This script scans the codebase for hardcoded rule counts or IDs that violate
the single source of truth principle. All rule counts must come from JSON files.
"""

import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATIC_FORBIDDEN_NUMBERS = {'149', '293', '414', '423', '424', '425'}


def get_canonical_rule_count() -> Optional[int]:
    """Retrieve the canonical rule count from the single source of truth."""
    try:
        from config.constitution.rule_count_loader import get_rule_counts
        counts = get_rule_counts()
        total = counts.get('total_rules')
        if isinstance(total, int):
            return total
    except Exception:
        pass
    return None


def build_forbidden_patterns() -> List[str]:
    """Build the forbidden regex patterns, including dynamic rule counts."""
    number_pattern = build_number_pattern()

    patterns = [
        r'total.*rules.*=\s*\d+',
        r'expected.*rules.*=\s*\d+',
        r'rule.*count.*=\s*\d+',
        r'rule.*range.*\(.*\d+.*,.*\d+.*\)',
        r'rule.*\d+.*to.*\d+',
        r'8.*json.*files|8.*JSON.*files',
        r'json.*files.*=\s*8',
    ]

    if number_pattern:
        patterns.insert(0, number_pattern)

    return patterns


def build_number_pattern() -> Optional[str]:
    """Construct a regex for explicitly hardcoded rule counts."""
    numbers = set(STATIC_FORBIDDEN_NUMBERS)
    canonical = get_canonical_rule_count()
    if canonical is not None:
        numbers.add(str(canonical))

    if not numbers:
        return None

    # Sort to avoid partial matches when numbers share prefixes
    sorted_numbers = sorted(numbers, key=lambda x: (-len(x), x))
    joined = '|'.join(sorted_numbers)
    return rf'\b({joined})\b'


FORBIDDEN_PATTERNS = build_forbidden_patterns()

# Files to exclude from scanning
EXCLUDE_PATTERNS = [
    r'.*\.pyc$',
    r'.*__pycache__.*',
    r'.*node_modules.*',
    r'.*\.git.*',
    r'.*\.json$',  # JSON files themselves are allowed
    r'.*count_rules\.py$',  # Utility scripts
    r'.*verify.*\.py$',  # Verification scripts (they check, not hardcode)
    r'.*test.*\.py$',  # Test files may have expected values
    r'.*rule_count_loader\.py$',  # The loader itself
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


def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Scan a file for hardcoded rule counts."""
    violations = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                for pattern in FORBIDDEN_PATTERNS:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        # Check if it's in a comment explaining the check
                        if '# check' in line.lower() or '# verify' in line.lower():
                            continue
                        # Check if it's in a test assertion (tests may check values)
                        if 'assert' in line.lower() or 'test' in line.lower():
                            # Only flag if it's not a dynamic check
                            if 'total_rules' not in line and 'hook_manager' not in line:
                                continue

                        violations.append((
                            line_num,
                            match.group(),
                            line.strip()
                        ))
    except Exception as e:
        print(f"Warning: Could not scan {file_path}: {e}", file=sys.stderr)

    return violations


def scan_directory(root_dir: Path, include_built_artifacts: bool = True) -> List[Tuple[Path, int, str, str]]:
    """Scan directory recursively for violations."""
    all_violations = []

    # Directories to scan for built artifacts
    built_artifact_dirs = ['dist', 'build', 'out', 'lib']
    
    for file_path in root_dir.rglob('*'):
        if not file_path.is_file():
            continue

        # Skip built artifacts unless explicitly included
        if not include_built_artifacts:
            if any(part in built_artifact_dirs for part in file_path.parts):
                continue

        if should_exclude_file(file_path):
            continue

        # Scan source files and built artifacts
        if file_path.suffix not in ['.py', '.ts', '.tsx', '.js', '.jsx', '.map']:
            continue

        violations = scan_file(file_path)
        for line_num, match, context in violations:
            all_violations.append((file_path, line_num, match, context))

    return all_violations


def scan_generated_stubs(root_dir: Path) -> List[Tuple[Path, int, str, str]]:
    """Scan generated stub files and type definitions."""
    violations = []
    
    # Scan for .d.ts files (type definitions)
    for file_path in root_dir.rglob('*.d.ts'):
        if should_exclude_file(file_path):
            continue
        if not file_path.is_file():
            continue
        
        file_violations = scan_file(file_path)
        for line_num, match, context in file_violations:
            violations.append((file_path, line_num, match, context))
    
    # Scan for .d.ts.map files
    for file_path in root_dir.rglob('*.d.ts.map'):
        if should_exclude_file(file_path):
            continue
        if not file_path.is_file():
            continue
        
        file_violations = scan_file(file_path)
        for line_num, match, context in file_violations:
            violations.append((file_path, line_num, match, context))
    
    # Scan generated directories
    for gen_dir in ['__generated__', 'generated']:
        for file_path in root_dir.rglob(f'**/{gen_dir}/**/*'):
            if should_exclude_file(file_path):
                continue
            if not file_path.is_file():
                continue
            if file_path.suffix not in ['.ts', '.tsx', '.js', '.jsx', '.py']:
                continue
            
            file_violations = scan_file(file_path)
            for line_num, match, context in file_violations:
                violations.append((file_path, line_num, match, context))
    
    return violations


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent.parent.parent

    print("=" * 80)
    print("HARDCODED RULE COUNT DETECTION")
    print("=" * 80)
    print(f"Scanning: {root_dir}")
    print()
    print("Scanning source files...")
    violations = scan_directory(root_dir, include_built_artifacts=False)
    
    print("Scanning built artifacts...")
    built_violations = scan_directory(root_dir, include_built_artifacts=True)
    violations.extend(built_violations)
    
    print("Scanning generated stubs...")
    stub_violations = scan_generated_stubs(root_dir)
    violations.extend(stub_violations)

    if violations:
        print(f"[FAIL] FOUND {len(violations)} POTENTIAL VIOLATIONS")
        print()
        print("Hardcoded rule counts violate single source of truth principle.")
        print("All rule counts must come from JSON files via PreImplementationHookManager.")
        print()

        for file_path, line_num, match, context in violations:
            rel_path = file_path.relative_to(root_dir)
            print(f"  {rel_path}:{line_num}")
            print(f"    Pattern: {match}")
            print(f"    Context: {context[:100]}")
            print()

        print("=" * 80)
        print("FAILED: Hardcoded rule counts detected")
        print("=" * 80)
        return 1
    else:
        print("[OK] No hardcoded rule counts detected")
        print("=" * 80)
        return 0


if __name__ == '__main__':
    sys.exit(main())
