#!/usr/bin/env python3
"""
CI Check: Privacy-Split Enforcement

Detects code that violates privacy-split principle by attempting to send
raw code or PII outside IDE/Client planes without proper redaction.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Patterns that indicate potential privacy violations
PRIVACY_VIOLATION_PATTERNS = [
    # Raw code egress patterns
    r'\.send\(.*code|\.post\(.*code|\.put\(.*code',
    r'fetch\(.*code|axios\.(get|post|put).*code',
    r'http\.(get|post|put).*code',
    # PII patterns
    r'\.send\(.*password|\.post\(.*password',
    r'\.send\(.*ssn|\.post\(.*ssn',
    r'\.send\(.*credit.*card|\.post\(.*credit.*card',
    # Direct file content transmission
    r'readFile.*\.send|readFile.*\.post',
    r'fs\.read.*\.send|fs\.read.*\.post',
]

# Allowed patterns (explicit redaction flags)
ALLOWED_PATTERNS = [
    r'redact.*before.*send',
    r'privacy.*split.*export',
    r'redaction.*enabled',
    r'#.*redaction.*ok',
]

# Files to exclude
EXCLUDE_PATTERNS = [
    r'.*test.*\.py$',
    r'.*test.*\.ts$',
    r'.*__tests__.*',
    r'.*\.spec\.',
]


def should_exclude_file(file_path: Path) -> bool:
    """Check if file should be excluded."""
    file_str = str(file_path)
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, file_str, re.IGNORECASE):
            return True
    return False


def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Scan file for privacy violations."""
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                for pattern in PRIVACY_VIOLATION_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Check if explicitly allowed
                        is_allowed = any(
                            re.search(allowed, line, re.IGNORECASE)
                            for allowed in ALLOWED_PATTERNS
                        )
                        if not is_allowed:
                            violations.append((
                                line_num,
                                pattern,
                                line.strip()
                            ))
    except Exception as e:
        print(f"Warning: Could not scan {file_path}: {e}", file=sys.stderr)
    
    return violations


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent.parent.parent
    
    print("=" * 80)
    print("PRIVACY-SPLIT ENFORCEMENT CHECK")
    print("=" * 80)
    print(f"Scanning: {root_dir}")
    print()
    
    violations = []
    for file_path in root_dir.rglob('*'):
        if not file_path.is_file():
            continue
        
        if should_exclude_file(file_path):
            continue
        
        # Only scan code files
        if file_path.suffix not in ['.py', '.ts', '.tsx', '.js', '.jsx']:
            continue
        
        file_violations = scan_file(file_path)
        violations.extend([(file_path, ln, pat, ctx) for ln, pat, ctx in file_violations])
    
    if violations:
        print(f"[FAIL] FOUND {len(violations)} POTENTIAL PRIVACY VIOLATIONS")
        print()
        print("Raw code or PII may be sent outside IDE/Client planes without redaction.")
        print("Use privacy-split export flags or redaction before transmission.")
        print()
        
        for file_path, line_num, pattern, context in violations[:20]:  # Limit output
            rel_path = file_path.relative_to(root_dir)
            print(f"  {rel_path}:{line_num}")
            print(f"    Pattern: {pattern}")
            print(f"    Context: {context[:100]}")
            print()
        
        if len(violations) > 20:
            print(f"  ... and {len(violations) - 20} more violations")
        
        print("=" * 80)
        print("FAILED: Privacy violations detected")
        print("=" * 80)
        return 1
    else:
        print("[OK] No privacy violations detected")
        print("=" * 80)
        return 0


if __name__ == '__main__':
    sys.exit(main())

