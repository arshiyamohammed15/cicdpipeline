#!/usr/bin/env python3
"""
Rebuild constitution artifacts from docs/constitution (single source of truth).

Generates:
- config/constitution_rules.json
- config/constitution_rules.db (SQLite)

This bypasses the markdown extractor and relies solely on docs/constitution/*.json.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.constitution.database import ConstitutionRulesDB
from config.constitution.rule_catalog import _find_constitution_dir  # type: ignore


def _load_raw_rules() -> List[Dict[str, Any]]:
    """Load raw rules directly from constitution JSON files (preserve enabled flags)."""
    source_dir = _find_constitution_dir()
    raw_rules: List[Dict[str, Any]] = []
    for json_file in sorted(source_dir.glob("*.json")):
        data = json.load(open(json_file, encoding="utf-8"))
        raw_rules.extend(data.get("constitution_rules", []))
    return raw_rules


def build_json_payload() -> Dict[str, Any]:
    """Construct constitution_rules.json payload with deterministic numbering."""
    raw_rules = _load_raw_rules()

    category_counts: Dict[str, int] = {}
    rules_dict: Dict[str, Dict[str, Any]] = {}

    for idx, rule in enumerate(raw_rules, start=1):
        category = rule.get("category", "UNKNOWN")
        category_counts[category] = category_counts.get(category, 0) + 1
        rules_dict[str(idx)] = {
            "rule_number": idx,
            "title": rule.get("title", f"Rule {idx}"),
            "category": category,
            "priority": str(rule.get("priority") or rule.get("severity_level") or "unknown").lower(),
            "content": rule.get("description", ""),
            "enabled": rule.get("enabled", True),
            "config": {
                "default_enabled": True,
                "notes": "",
                "disabled_reason": None,
                "disabled_at": None,
                "maintenance_complete": True,
            },
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "usage_count": 0,
                "last_used": None,
                "source": "docs/constitution",
                "doc_rule_id": rule.get("rule_id"),
            },
        }

    total_rules = len(rules_dict)
    enabled_rules = sum(1 for r in rules_dict.values() if r["enabled"])

    payload = {
        "version": "2.0",
        "database": "constitution_rules",
        "last_updated": datetime.now().isoformat(),
        "statistics": {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "disabled_rules": total_rules - enabled_rules,
            "categories": category_counts,
        },
        "rules": rules_dict,
    }
    return payload


def write_json(payload: Dict[str, Any], dest: Path):
    """Write constitution_rules.json payload to disk."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def rebuild_sqlite(rules: List[Dict[str, Any]], db_path: Path):
    """Rebuild SQLite database using the raw rules list."""
    if db_path.exists():
        db_path.unlink()

    db = ConstitutionRulesDB(str(db_path))

    # ConstitutionRulesDB.import_rules_from_json expects JSON string of list[dict]
    db.import_rules_from_json(json.dumps(rules))


def main() -> int:
    payload = build_json_payload()
    json_path = REPO_ROOT / "config" / "constitution_rules.json"
    write_json(payload, json_path)

    # Prepare rules list for SQLite (flatten)
    rules_for_db = []
    for rule_number, data in payload["rules"].items():
        rules_for_db.append({
            "rule_number": data["rule_number"],
            "title": data["title"],
            "category": data["category"],
            "priority": data["priority"],
            "content": data["content"],
            "enabled": data.get("enabled", True),
        })

    sqlite_path = REPO_ROOT / "config" / "constitution_rules.db"
    rebuild_sqlite(rules_for_db, sqlite_path)

    totals = payload["statistics"]
    print(f"[OK] Rebuilt constitution_rules.json and SQLite with {totals.get('total_rules')} rules")
    print(f"[OK] Paths:\n  - {json_path}\n  - {sqlite_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
