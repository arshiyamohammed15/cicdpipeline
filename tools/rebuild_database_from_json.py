#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rebuild Constitution Database from JSON Source Files

This script loads all rules from docs/constitution/*.json files (the single source of truth)
and regenerates both the SQLite database and JSON export to match.

Usage:
    python tools/rebuild_database_from_json.py
"""

import json
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

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

from tools.utils.file_utils import setup_windows_console_encoding
from config.constitution.database import ConstitutionRulesDB
from config.constitution.constitution_rules_json import ConstitutionRulesJSON

# Fix Windows console encoding
setup_windows_console_encoding()


def load_rules_from_json_files(constitution_dir: str = "docs/constitution") -> List[Dict[str, Any]]:
    """
    Load all rules from JSON source files (single source of truth).

    Args:
        constitution_dir: Path to directory containing constitution JSON files

    Returns:
        List of rule dictionaries
    """
    constitution_path = Path(constitution_dir)
    if not constitution_path.exists():
        raise FileNotFoundError(f"Constitution directory not found: {constitution_path}")

    json_files = sorted(list(constitution_path.glob("*.json")))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {constitution_path}")

    all_rules = []
    rule_counter = 1  # Sequential rule numbering

    for json_file in json_files:
        logger.info(f"Loading rules from {json_file.name}...")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                rules = data.get('constitution_rules', [])

                for rule in rules:
                    # Extract rule data
                    rule_id = rule.get('rule_id', '')
                    title = rule.get('title', '')
                    category = rule.get('category', 'other')
                    enabled = rule.get('enabled', True)
                    severity = rule.get('severity_level', 'Major')
                    description = rule.get('description', '')
                    requirements = rule.get('requirements', [])

                    # Determine priority from severity
                    priority_map = {
                        'Blocker': 'critical',
                        'Major': 'critical',
                        'Minor': 'important',
                        'Info': 'recommended'
                    }
                    priority = priority_map.get(severity, 'important')

                    # Build content from description and requirements
                    content_parts = [description]
                    if requirements:
                        content_parts.append("\n\nRequirements:")
                        for req in requirements:
                            content_parts.append(f"- {req}")
                    content = "\n".join(content_parts)

                    # Create rule data structure
                    rule_data = {
                        'rule_number': rule_counter,
                        'title': title,
                        'category': category.lower().replace(' ', '_'),
                        'priority': priority,
                        'content': content,
                        'enabled': enabled,
                        'rule_id': rule_id,
                        'severity': severity,
                        'description': description,
                        'requirements': requirements,
                        'version': rule.get('version', '1.0.0'),
                        'effective_date': rule.get('effective_date', '2024-01-01'),
                        'last_updated': rule.get('last_updated', datetime.now().isoformat()),
                        'policy_linkage': rule.get('policy_linkage', {}),
                        'validation': rule.get('validation', ''),
                        'error_condition': rule.get('error_condition', '')
                    }

                    all_rules.append(rule_data)
                    rule_counter += 1

        except Exception as e:
            logger.error(f"Error loading {json_file.name}: {e}", exc_info=True)
            continue

    logger.info(f"\nLoaded {len(all_rules)} rules from {len(json_files)} files")
    return all_rules


def rebuild_sqlite_database(rules: List[Dict[str, Any]], db_path: Optional[str] = None):
    """
    Rebuild SQLite database with rules from JSON source files.

    Args:
        rules: List of rule dictionaries
        db_path: Path to SQLite database file. If None, uses default external storage location
                 (resolved via resolve_constitution_db_path to ensure it's outside the repository).
    """
    from config.constitution.path_utils import resolve_constitution_db_path
    
    # Resolve path to external storage location (outside repository)
    resolved_db_path = resolve_constitution_db_path(db_path)
    
    logger.info(f"\n{'='*70}")
    logger.info("REBUILDING SQLITE DATABASE")
    logger.info(f"{'='*70}")

    # Backup existing database
    db_file = resolved_db_path
    if db_file.exists():
        backup_path = db_file.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        import shutil
        shutil.copy2(db_file, backup_path)
        logger.info(f"Backed up existing database to {backup_path.name}")

    # Remove existing database
    if db_file.exists():
        db_file.unlink()
        logger.info("Removed existing database")

    # Create new database (ConstitutionRulesDB will resolve path again, but we pass resolved path for consistency)
    db = ConstitutionRulesDB(str(resolved_db_path))

    # Clear existing rules
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM constitution_rules")
        cursor.execute("DELETE FROM rule_configuration")
        cursor.execute("DELETE FROM rule_categories")
        conn.commit()
        logger.info("Cleared existing rules")

    # Insert all rules
    with db.get_connection() as conn:
        cursor = conn.cursor()

        for rule_data in rules:
            # Insert rule
            cursor.execute("""
                INSERT INTO constitution_rules (rule_number, title, category, priority, content, json_metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rule_data['rule_number'],
                rule_data['title'],
                rule_data['category'],
                rule_data['priority'],
                rule_data['content'],
                json.dumps(rule_data)
            ))

            # Insert configuration
            cursor.execute("""
                INSERT INTO rule_configuration (rule_number, enabled, config_data)
                VALUES (?, ?, ?)
            """, (
                rule_data['rule_number'],
                1 if rule_data.get('enabled', True) else 0,
                json.dumps({
                    "default_enabled": rule_data.get('enabled', True),
                    "notes": "",
                    "disabled_reason": None,
                    "disabled_at": None,
                    "maintenance_complete": True
                })
            ))

        # Update categories
        category_counts = {}
        for rule in rules:
            cat = rule['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1

        for category, count in category_counts.items():
            cursor.execute("""
                INSERT OR REPLACE INTO rule_categories (name, description, priority, rule_count)
                VALUES (?, ?, ?, ?)
            """, (
                category,
                f"Rules for {category}",
                "critical",
                count
            ))

        conn.commit()
        logger.info(f"Inserted {len(rules)} rules into SQLite database")

    db.close()
    logger.info("[OK] SQLite database rebuilt successfully")


def rebuild_json_export(rules: List[Dict[str, Any]], json_path: str = "config/constitution_rules.json"):
    """
    Rebuild JSON export with rules from JSON source files.

    Args:
        rules: List of rule dictionaries
        json_path: Path to JSON export file
    """
    logger.info(f"\n{'='*70}")
    logger.info("REBUILDING JSON EXPORT")
    logger.info(f"{'='*70}")

    # Backup existing export
    json_file = Path(json_path)
    if json_file.exists():
        backup_path = json_file.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        import shutil
        shutil.copy2(json_file, backup_path)
        logger.info(f"Backed up existing export to {backup_path.name}")

    # Calculate statistics
    enabled_count = sum(1 for r in rules if r.get('enabled', True))
    disabled_count = len(rules) - enabled_count

    # Count by category
    category_counts = {}
    category_rules = {}
    for rule in rules:
        cat = rule['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if cat not in category_rules:
            category_rules[cat] = []
        category_rules[cat].append(rule['rule_number'])

    # Build export structure
    export_data = {
        "version": "2.0",
        "database": "constitution_rules",
        "last_updated": datetime.now().isoformat(),
        "statistics": {
            "total_rules": len(rules),
            "enabled_rules": enabled_count,
            "disabled_rules": disabled_count,
            "categories": category_counts
        },
        "categories": {
            cat: {
                "name": cat,
                "description": f"Rules for {cat}",
                "priority": "critical",
                "rule_count": count
            }
            for cat, count in category_counts.items()
        },
        "rules": {
            str(rule['rule_number']): {
                "rule_number": rule['rule_number'],
                "title": rule['title'],
                "category": rule['category'],
                "priority": rule['priority'],
                "content": rule['content'],
                "enabled": rule.get('enabled', True),
                "config": {
                    "default_enabled": rule.get('enabled', True),
                    "notes": "",
                    "disabled_reason": None,
                    "disabled_at": None,
                    "maintenance_complete": True
                },
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "usage_count": 0,
                    "last_used": None,
                    "source": "json_rebuild"
                }
            }
            for rule in rules
        }
    }

    # Write export file
    json_file.parent.mkdir(parents=True, exist_ok=True)
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    logger.info(f"[OK] JSON export rebuilt with {len(rules)} rules")
    logger.info(f"  - Enabled: {enabled_count}")
    logger.info(f"  - Disabled: {disabled_count}")


def update_configuration_file(rules: List[Dict[str, Any]], config_path: str = "config/constitution_config.json"):
    """
    Update configuration file with correct rule count.

    Args:
        rules: List of rule dictionaries
        config_path: Path to configuration file
    """
    logger.info(f"\n{'='*70}")
    logger.info("UPDATING CONFIGURATION FILE")
    logger.info(f"{'='*70}")

    config_file = Path(config_path)

    # Load existing config to preserve settings
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {
            "version": "2.0",
            "last_updated": datetime.now().isoformat(),
            "primary_backend": "sqlite",
            "backend_config": {
                "sqlite": {
                    "_note": "path is a reference only; actual database is stored externally (outside repository) via resolve_constitution_db_path. Set to null to use default external storage location.",
                    "path": None,
                    "timeout": 30,
                    "wal_mode": True,
                    "connection_pool_size": 5
                },
                "json": {
                    "path": "config/constitution_rules.json",
                    "auto_backup": True,
                    "atomic_writes": True,
                    "backup_retention": 5
                }
            },
            "fallback": {
                "enabled": False,
                "fallback_backend": "json"
            },
            "sync": {
                "enabled": True,
                "interval_seconds": 60,
                "auto_sync_on_write": True,
                "conflict_resolution": "primary_wins"
            },
            "rules": {}
        }

    # Update total rules count
    config["total_rules"] = len(rules)
    config["last_updated"] = datetime.now().isoformat()

    # Update or create rule entries (preserve existing enabled/disabled states)
    enabled_count = 0
    for rule in rules:
        rule_num = str(rule['rule_number'])
        if rule_num not in config.get("rules", {}):
            # New rule - default to enabled
            config.setdefault("rules", {})[rule_num] = {
                "enabled": rule.get('enabled', True),
                "config": {
                    "maintenance_complete": True
                },
                "updated_at": datetime.now().isoformat()
            }
        else:
            # Existing rule - preserve enabled state
            config["rules"][rule_num]["updated_at"] = datetime.now().isoformat()
            if config["rules"][rule_num].get("enabled", True):
                enabled_count += 1
        if rule.get('enabled', True) and rule_num not in config.get("rules", {}):
            enabled_count += 1

    # Save updated config
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    logger.info(f"[OK] Configuration file updated")
    logger.info(f"  - Total rules: {len(rules)}")
    logger.info(f"  - Enabled rules: {enabled_count}")


def main():
    """Main function to rebuild database from JSON source files."""
    logger.info("="*70)
    logger.info("REBUILDING CONSTITUTION DATABASE FROM JSON SOURCE FILES")
    logger.info("="*70)
    logger.info(f"Source of Truth: docs/constitution/*.json")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("="*70)

    try:
        # Step 1: Load rules from JSON source files
        logger.info("\n[1/4] Loading rules from JSON source files...")
        rules = load_rules_from_json_files()

        if not rules:
            logger.error("ERROR: No rules loaded from source files!")
            return 1

        logger.info(f"[OK] Loaded {len(rules)} rules")

        # Step 2: Rebuild SQLite database
        logger.info("\n[2/4] Rebuilding SQLite database...")
        rebuild_sqlite_database(rules)

        # Step 3: Rebuild JSON export
        logger.info("\n[3/4] Rebuilding JSON export...")
        rebuild_json_export(rules)

        # Step 4: Update configuration file
        logger.info("\n[4/4] Updating configuration file...")
        update_configuration_file(rules)

        # Verification
        logger.info(f"\n{'='*70}")
        logger.info("VERIFICATION")
        logger.info(f"{'='*70}")

        # Verify SQLite
        db = ConstitutionRulesDB()
        db_rules = db.get_all_rules()
        logger.info(f"SQLite database: {len(db_rules)} rules")
        db.close()

        # Verify JSON export
        with open("config/constitution_rules.json", 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        logger.info(f"JSON export: {json_data['statistics']['total_rules']} rules")

        # Verify config
        with open("config/constitution_config.json", 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        logger.info(f"Configuration: {config_data.get('total_rules', 'N/A')} rules")

        logger.info(f"\n{'='*70}")
        logger.info("[OK] DATABASE REBUILD COMPLETE")
        logger.info(f"{'='*70}")
        logger.info(f"Total rules: {len(rules)}")
        logger.info(f"All sources synchronized with docs/constitution/*.json")

        return 0

    except Exception as e:
        logger.error(f"\nERROR: {e}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
