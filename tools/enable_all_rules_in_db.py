#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enable all rules in SQLite database"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.constitution.database import ConstitutionRulesDB

db = ConstitutionRulesDB()

with db.get_connection() as conn:
    cursor = conn.cursor()

    # Get all rules
    cursor.execute("SELECT rule_number FROM constitution_rules")
    rule_numbers = [row[0] for row in cursor.fetchall()]

    # Enable all rules
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
    print(f"[OK] Enabled all {len(rule_numbers)} rules in SQLite database")

db.close()
