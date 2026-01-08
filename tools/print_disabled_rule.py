#!/usr/bin/env python3
"""
Print Disabled Constitution Rule

This script prints the disabled rule from docs/constitution/DISABLED RULES.json
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def main():
    """Print the disabled rule."""
    disabled_file = project_root / "docs" / "constitution" / "DISABLED RULES.json"
    
    if not disabled_file.exists():
        print(f"Error: File not found: {disabled_file}")
        return 1
    
    with open(disabled_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    rules = data.get('constitution_rules', [])
    disabled_rules = [r for r in rules if not r.get('enabled', True)]
    
    if not disabled_rules:
        print("No disabled rules found.")
        return 0
    
    print("="*70)
    print("DISABLED RULE")
    print("="*70)
    
    for rule in disabled_rules:
        print(f"\nRule ID: {rule.get('rule_id', 'N/A')}")
        print(f"Title: {rule.get('title', 'N/A')}")
        print(f"Category: {rule.get('category', 'N/A')}")
        print(f"Severity Level: {rule.get('severity_level', 'N/A')}")
        print(f"Enabled: {rule.get('enabled', True)}")
        print(f"Version: {rule.get('version', 'N/A')}")
        print(f"Effective Date: {rule.get('effective_date', 'N/A')}")
        print(f"Last Updated: {rule.get('last_updated', 'N/A')}")
        print(f"Last Updated By: {rule.get('last_updated_by', 'N/A')}")
        print(f"\nDescription:")
        print(f"  {rule.get('description', 'N/A')}")
        
        if 'requirements' in rule:
            print(f"\nRequirements:")
            for req in rule['requirements']:
                print(f"  - {req}")
        
        if 'validation' in rule:
            print(f"\nValidation:")
            print(f"  {rule.get('validation', 'N/A')}")
        
        if 'policy_linkage' in rule:
            policy = rule['policy_linkage']
            print(f"\nPolicy Linkage:")
            if 'policy_version_ids' in policy:
                print(f"  Policy Version IDs: {', '.join(policy['policy_version_ids'])}")
            if 'policy_snapshot_hash' in policy:
                print(f"  Policy Snapshot Hash: {policy['policy_snapshot_hash']}")
    
    print("\n" + "="*70)
    return 0

if __name__ == '__main__':
    sys.exit(main())
