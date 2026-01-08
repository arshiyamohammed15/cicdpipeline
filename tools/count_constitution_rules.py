#!/usr/bin/env python3
"""
Count Constitution Rules - Direct from Source of Truth

This script counts rules directly from docs/constitution/*.json files
which are the single source of truth.
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.constitution.rule_count_loader import get_rule_count_loader

def main():
    """Count and display constitution rules."""
    loader = get_rule_count_loader()
    counts = loader.get_counts(force_reload=True)
    
    # Also count directly from files for verification
    constitution_dir = project_root / "docs" / "constitution"
    json_files = sorted(constitution_dir.glob("*.json"))
    
    file_counts = {}
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            rules = data.get('constitution_rules', [])
            file_enabled = sum(1 for r in rules if r.get('enabled', True))
            file_disabled = sum(1 for r in rules if not r.get('enabled', True))
            file_counts[json_file.name] = {
                'total': len(rules),
                'enabled': file_enabled,
                'disabled': file_disabled
            }
    
    print("="*70)
    print("CONSTITUTION RULES COUNT")
    print("="*70)
    print(f"Total Rules: {counts['total_rules']}")
    print(f"Enabled Rules: {counts['enabled_rules']}")
    print(f"Disabled Rules: {counts['disabled_rules']}")
    print("\nBreakdown by file:")
    print("-"*70)
    for filename in sorted(file_counts.keys()):
        fc = file_counts[filename]
        print(f"  {filename:50} {fc['total']:3} rules ({fc['enabled']:3} enabled, {fc['disabled']:3} disabled)")
    print("="*70)
    
    # Verify counts match
    direct_total = sum(fc['total'] for fc in file_counts.values())
    direct_enabled = sum(fc['enabled'] for fc in file_counts.values())
    direct_disabled = sum(fc['disabled'] for fc in file_counts.values())
    
    if (direct_total != counts['total_rules'] or 
        direct_enabled != counts['enabled_rules'] or 
        direct_disabled != counts['disabled_rules']):
        print("\nWARNING: Count mismatch detected!")
        print(f"Loader says: {counts['total_rules']} total, {counts['enabled_rules']} enabled, {counts['disabled_rules']} disabled")
        print(f"Direct count: {direct_total} total, {direct_enabled} enabled, {direct_disabled} disabled")
        sys.exit(1)
    else:
        print("\n[OK] Counts verified: Loader and direct count match")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
