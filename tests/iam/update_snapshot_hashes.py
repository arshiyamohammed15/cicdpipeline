#!/usr/bin/env python3
"""
Update GSMD snapshot hashes with real SHA-256 values.

Calculates hash from canonical JSON representation (excluding hash and signature fields).
"""

import json
import hashlib
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
gsmd_dir = project_root / "gsmd" / "gsmd" / "modules" / "EPC-1"

snapshot_files = [
    "messages/v1/snapshot.json",
    "receipts_schema/v1/snapshot.json",
    "evidence_map/v1/snapshot.json",
    "gate_rules/v1/snapshot.json",
    "observability/v1/snapshot.json",
    "risk_model/v1/snapshot.json"
]

for snapshot_file in snapshot_files:
    file_path = gsmd_dir / snapshot_file
    if not file_path.exists():
        continue

    # Read JSON
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Remove hash and signature for calculation
    original_hash = data.get('snapshot_hash', '')
    original_sig = data.get('signature', '')
    data['snapshot_hash'] = ''
    data['signature'] = ''

    # Calculate hash from canonical JSON
    canonical_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
    hash_value = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

    # Restore and update
    data['snapshot_hash'] = f"sha256:{hash_value}"
    data['signature'] = original_sig  # Keep PLACEHOLDER for now

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print(f"Updated {snapshot_file}: sha256:{hash_value}")
