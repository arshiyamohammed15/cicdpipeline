#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find and enable any disabled rules"""

import json
from pathlib import Path

# Check JSON export
with open('config/constitution_rules.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

disabled = [r for r in db['rules'].values() if not r.get('enabled', True)]
print(f"Disabled rules: {len(disabled)}")
for r in disabled:
    print(f"  Rule {r['rule_number']}: {r['title']} (category: {r['category']})")
    # Enable it
    r['enabled'] = True
    r['config']['disabled_reason'] = None
    r['config']['disabled_at'] = None

if disabled:
    # Update statistics
    enabled_count = sum(1 for r in db['rules'].values() if r.get('enabled', True))
    db['statistics']['enabled_rules'] = enabled_count
    db['statistics']['disabled_rules'] = len(db['rules']) - enabled_count

    # Save
    with open('config/constitution_rules.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Enabled {len(disabled)} rule(s)")
    print(f"Total enabled: {enabled_count} / {len(db['rules'])}")
else:
    print("\n[OK] All rules are enabled")
