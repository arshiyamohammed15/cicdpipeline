#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify database sync status"""

import json
from pathlib import Path

# Check JSON export
with open('config/constitution_rules.json', 'r', encoding='utf-8') as f:
    db = json.load(f)
    print(f"JSON Export: {db['statistics']['total_rules']} total, {db['statistics']['enabled_rules']} enabled, {db['statistics']['disabled_rules']} disabled")

# Check config file
with open('config/constitution_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    rules_dict = config.get('rules', {})
    enabled_count = sum(1 for r in rules_dict.values() if r.get('enabled', True))
    print(f"Config file: {config.get('total_rules', 'N/A')} total, {len(rules_dict)} rules in dict, {enabled_count} enabled")

# Check source files
from pathlib import Path
total = 0
for f in Path('docs/constitution').glob('*.json'):
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
        count = len(data.get('constitution_rules', []))
        total += count
        print(f"Source file {f.name}: {count} rules")

print(f"\nSource files total: {total} rules")
print(f"Database total: {db['statistics']['total_rules']} rules")
print(f"Config total: {config.get('total_rules', 'N/A')} rules")

if total == db['statistics']['total_rules'] == config.get('total_rules', 0):
    print("\n[OK] All sources are synchronized")
else:
    print("\n[ERROR] Sources are not synchronized!")

