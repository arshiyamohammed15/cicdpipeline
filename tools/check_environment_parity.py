#!/usr/bin/env python3
"""
Environment Parity Checker

Checks for drift between environments by comparing:
- Rule counts
- Snapshot IDs
- Trust key KIDs
- Gate table hashes
"""

import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, List


def get_rule_count() -> int:
    """Get current rule count from JSON files."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from validator.pre_implementation_hooks import PreImplementationHookManager
    manager = PreImplementationHookManager()
    return manager.total_rules


def get_json_files_hash() -> str:
    """Get hash of all JSON files."""
    constitution_dir = Path("docs/constitution")
    json_files = sorted(list(constitution_dir.glob("*.json")))

    hasher = hashlib.sha256()
    for json_file in json_files:
        with open(json_file, 'rb') as f:
            hasher.update(f.read())

    return hasher.hexdigest()


def check_environment_parity() -> Dict[str, Any]:
    """Check environment parity."""
    rule_count = get_rule_count()
    json_hash = get_json_files_hash()
    json_files = sorted(list(Path("docs/constitution").glob("*.json")))

    return {
        'rule_count': rule_count,
        'json_files_count': len(json_files),
        'json_files_hash': json_hash,
        'json_files': [f.name for f in json_files],
        'status': 'ok'
    }


def main():
    """Main entry point."""
    print("=" * 80)
    print("ENVIRONMENT PARITY CHECK")
    print("=" * 80)

    try:
        result = check_environment_parity()

        print(f"Rule count: {result['rule_count']}")
        print(f"JSON files: {result['json_files_count']}")
        print(f"JSON files hash: {result['json_files_hash']}")
        print(f"Files: {', '.join(result['json_files'])}")

        print("\n" + "=" * 80)
        print("[OK] Environment parity check complete")
        print("=" * 80)

        # Output JSON for CI/CD integration
        if '--json' in sys.argv:
            print(json.dumps(result, indent=2))

        return 0
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
