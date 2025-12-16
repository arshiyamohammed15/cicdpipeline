#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enable all rules in SQLite database"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.utils.db_utils import get_db_connection, get_all_rule_numbers

# Get all rule numbers
rule_numbers = get_all_rule_numbers()

# Enable all rules
with get_db_connection() as conn:
    cursor = conn.cursor()
    for rule_num in rule_numbers:
        cursor.execute("""
            UPDATE rule_configuration
            SET enabled = 1,
                disabled_reason = NULL,
                disabled_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE rule_number = ?
        """, (rule_num,))
    conn.commit()
    logger.info(f"[OK] Enabled all {len(rule_numbers)} rules in SQLite database")
