#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify database sync status"""

import json
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.utils.file_utils import load_rules_from_json_files

# Check JSON export
with open('config/constitution_rules.json', 'r', encoding='utf-8') as f:
    db = json.load(f)
    logger.info(f"JSON Export: {db['statistics']['total_rules']} total, {db['statistics']['enabled_rules']} enabled, {db['statistics']['disabled_rules']} disabled")

# Check config file
with open('config/constitution_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    rules_dict = config.get('rules', {})
    enabled_count = sum(1 for r in rules_dict.values() if r.get('enabled', True))
    logger.info(f"Config file: {config.get('total_rules', 'N/A')} total, {len(rules_dict)} rules in dict, {enabled_count} enabled")

# Check source files using shared utility
source_rules = load_rules_from_json_files('docs/constitution')
total = len(source_rules)
logger.info(f"\nSource files total: {total} rules")

logger.info(f"Database total: {db['statistics']['total_rules']} rules")
logger.info(f"Config total: {config.get('total_rules', 'N/A')} rules")

if total == db['statistics']['total_rules'] == config.get('total_rules', 0):
    logger.info("\n[OK] All sources are synchronized")
else:
    logger.error("\n[ERROR] Sources are not synchronized!")
