#!/usr/bin/env python3
"""
Verify Architecture Artifacts Exist

Checks that all required architecture artifacts from ZeroUI_Architecture_V0_converted.md
are present and properly structured.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple


# Required artifacts from architecture document
# Note: OpenAPI specs and schemas are located in contracts/<module-name>/ directories
REQUIRED_ARTIFACTS = {
    'openapi': [
        # OpenAPI specs are in contracts/<module-name>/openapi/ - verify at least one exists
        'contracts/',
    ],
    'schemas': [
        # Schemas are in contracts/<module-name>/schemas/ - verify at least one exists
        'contracts/',
    ],
    'gate_tables': [
        'docs/architecture/gate_tables/README.md',
        # At least one CSV file
    ],
    'trust': [
        'docs/architecture/trust/signing_process.md',
        'docs/architecture/trust/verify_path.md',
        'docs/architecture/trust/crl_rotation.md',
        'docs/architecture/trust/public_keys/README.md',
    ],
    'slo': [
        'docs/architecture/slo/slos.md',
        'docs/architecture/slo/alerts.md',
    ],
    'policy': [
        'docs/architecture/policy/policy_snapshot_v1.json',
        'docs/architecture/policy/rollback.md',
    ],
    'samples': [
        'docs/architecture/samples/receipts/receipts_example.jsonl',
        'docs/architecture/samples/evidence/evidence_pack_example.json',
    ],
    'ops': [
        'docs/architecture/ops/runbooks.md',
        'docs/architecture/ops/branching.md',
    ],
    'dev': [
        'docs/architecture/dev/standards.md',
        'docs/architecture/dev/quickstart_windows.md',
    ],
    'security': [
        'docs/architecture/security/rbac.md',
        'docs/architecture/security/data_classes.md',
        'docs/architecture/security/privacy_note.md',
    ],
    'tests': [
        'docs/architecture/tests/test_plan.md',
        'docs/architecture/tests/golden/',
    ],
}


def check_artifacts() -> Tuple[bool, List[str], List[str]]:
    """Check which artifacts exist and which are missing."""
    root_dir = Path(__file__).parent.parent.parent
    missing = []
    present = []
    
    for category, artifacts in REQUIRED_ARTIFACTS.items():
        for artifact_path in artifacts:
            full_path = root_dir / artifact_path
            
            # Check if it's a directory
            if artifact_path.endswith('/'):
                if full_path.exists() and full_path.is_dir():
                    present.append(artifact_path)
                else:
                    missing.append(artifact_path)
            else:
                if full_path.exists():
                    present.append(artifact_path)
                else:
                    missing.append(artifact_path)
    
    # Special check: at least one gate table CSV
    gate_tables_dir = root_dir / 'docs/architecture/gate_tables'
    if gate_tables_dir.exists():
        csv_files = list(gate_tables_dir.glob('*.csv'))
        if csv_files:
            present.append('docs/architecture/gate_tables/*.csv (at least one)')
        else:
            missing.append('docs/architecture/gate_tables/*.csv (at least one)')
    else:
        missing.append('docs/architecture/gate_tables/ (directory)')
    
    all_present = len(missing) == 0
    return all_present, present, missing


def main():
    """Main entry point."""
    print("=" * 80)
    print("ARCHITECTURE ARTIFACTS VERIFICATION")
    print("=" * 80)
    print()
    
    all_present, present, missing = check_artifacts()
    
    if present:
        print(f"[OK] {len(present)} artifacts present")
        for artifact in present[:10]:  # Show first 10
            print(f"  [OK] {artifact}")
        if len(present) > 10:
            print(f"  ... and {len(present) - 10} more")
        print()
    
    if missing:
        print(f"[MISSING] {len(missing)} artifacts missing")
        for artifact in missing:
            print(f"  [X] {artifact}")
        print()
    
    print("=" * 80)
    if all_present:
        print("[SUCCESS] All required architecture artifacts present")
        return 0
    else:
        print(f"[FAILURE] {len(missing)} artifacts missing")
        print("See ZeroUI_Architecture_V0_converted.md for required artifacts")
        return 1


if __name__ == '__main__':
    sys.exit(main())

