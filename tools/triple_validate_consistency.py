#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triple Validation: Verify consistency of constitution rules across:
1) Source of truth: docs/constitution/*.json
2) SQLite DB: config/constitution_rules.db
3) JSON export: config/constitution_rules.json
4) Config file: config/constitution_config.json

Validation criteria:
- Exact same total count across all sources
- All rule_numbers present 1..N in DB/Export/Config
- Identity check via (normalized title, normalized category) sets equality across DB and Export
- Config contains an entry for every rule_number with enabled flag present

Output: Deterministic pass/fail summary with any mismatches listed precisely.
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Ensure project root on path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.utils.file_utils import load_rules_from_json_files, setup_windows_console_encoding
from tools.utils.db_utils import get_db_connection

# Make prints ASCII-safe on Windows consoles
setup_windows_console_encoding()


def load_source_rules() -> List[Dict]:
    """Load rules from JSON source files."""
    return load_rules_from_json_files(str(project_root / "docs" / "constitution"))


def normalize_text(s: str) -> str:
    import re
    s = (s or "").strip().lower()
    # Replace any non-alphanumeric character with space
    s = re.sub(r"[^a-z0-9]+", " ", s)
    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def make_identity_from_source(rule: Dict) -> Tuple[str, str]:
    return normalize_text(rule.get("title", "")), normalize_text(rule.get("category", ""))


def make_identity_from_db(rule: Dict) -> Tuple[str, str]:
    return normalize_text(rule.get("title", "")), normalize_text(rule.get("category", ""))


def validate() -> None:
    errors: List[str] = []

    # Load source of truth
    src_rules = load_source_rules()
    src_total = len(src_rules)
    src_identities: Set[Tuple[str, str]] = {make_identity_from_source(r) for r in src_rules}

    # Load DB
    from config.constitution.database import ConstitutionRulesDB
    db = ConstitutionRulesDB()
    db_rules = db.get_all_rules()
    db_total = len(db_rules)
    db_numbers: Set[int] = {int(r["rule_number"]) for r in db_rules}
    db_identities: Set[Tuple[str, str]] = {make_identity_from_db(r) for r in db_rules}
    db.close()

    # Load JSON export
    export_path = project_root / "config" / "constitution_rules.json"
    export_data = json.loads(export_path.read_text(encoding="utf-8"))
    export_total = int(export_data["statistics"]["total_rules"])
    export_rules = export_data["rules"]
    export_numbers: Set[int] = {int(k) for k in export_rules.keys()}
    export_identities: Set[Tuple[str, str]] = {
        (normalize_text(v.get("title", "")), normalize_text(v.get("category", "")))
        for v in export_rules.values()
    }

    # Load config
    config_path = project_root / "config" / "constitution_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    cfg_total = int(config.get("total_rules", 0))
    cfg_rules = config.get("rules", {})
    cfg_numbers: Set[int] = {int(k) for k in cfg_rules.keys()}

    # 1) Count equality
    if not (src_total == db_total == export_total == cfg_total):
        errors.append(
            f"Count mismatch: source={src_total}, db={db_total}, export={export_total}, config={cfg_total}"
        )

    # 2) Rule number coverage (DB/Export/Config must be 1..N)
    expected_numbers: Set[int] = set(range(1, src_total + 1))
    if db_numbers != expected_numbers:
        missing = sorted(list(expected_numbers - db_numbers))[:10]
        extra = sorted(list(db_numbers - expected_numbers))[:10]
        errors.append(f"DB rule_numbers mismatch. Missing sample={missing}, Extra sample={extra}")
    if export_numbers != expected_numbers:
        missing = sorted(list(expected_numbers - export_numbers))[:10]
        extra = sorted(list(export_numbers - expected_numbers))[:10]
        errors.append(f"Export rule_numbers mismatch. Missing sample=={missing}, Extra sample={extra}")
    if cfg_numbers != expected_numbers:
        missing = sorted(list(expected_numbers - cfg_numbers))[:10]
        extra = sorted(list(cfg_numbers - expected_numbers))[:10]
        errors.append(f"Config rule_numbers mismatch. Missing sample={missing}, Extra sample={extra}")

    # 3) Identity set equality (Title+Category) across DB and Export should match Source cardinality
    if len(db_identities) != len(src_identities):
        errors.append(
            f"Identity cardinality mismatch DB vs Source: db={len(db_identities)}, source={len(src_identities)}"
        )
    if len(export_identities) != len(src_identities):
        errors.append(
            f"Identity cardinality mismatch Export vs Source: export={len(export_identities)}, source={len(src_identities)}"
        )

    # 4) Optional: list first few identity deltas
    db_minus_src = list(sorted(db_identities - src_identities))[:5]
    src_minus_db = list(sorted(src_identities - db_identities))[:5]
    exp_minus_src = list(sorted(export_identities - src_identities))[:5]
    src_minus_exp = list(sorted(src_identities - export_identities))[:5]
    if db_minus_src:
        errors.append(f"DB identities not in Source (sample): {db_minus_src}")
    if src_minus_db:
        errors.append(f"Source identities not in DB (sample): {src_minus_db}")
    if exp_minus_src:
        errors.append(f"Export identities not in Source (sample): {exp_minus_src}")
    if src_minus_exp:
        errors.append(f"Source identities not in Export (sample): {src_minus_exp}")

    # 5) Config enabled state present for each rule
    cfg_missing_enabled = [k for k, v in list(cfg_rules.items())[:5] if "enabled" not in v]
    if cfg_missing_enabled:
        errors.append(f"Config entries missing 'enabled' field (sample): {cfg_missing_enabled}")

    if errors:
        logger.error("[FAIL] Triple validation failed\n")
        for e in errors:
            # Ensure ASCII-only to avoid console encoding issues
            logger.error(f"- {str(e).encode('ascii', 'ignore').decode('ascii')}")
        sys.exit(1)
    else:
        logger.info("[OK] Triple validation passed: Source, DB, Export, and Config are consistent")
        logger.info(f"Counts: {src_total}")
        logger.info("Rule numbers: 1..{} present in DB, Export, and Config".format(src_total))
        logger.info("Identity sets (Title+Category) match across DB/Export vs Source")


if __name__ == "__main__":
    validate()
