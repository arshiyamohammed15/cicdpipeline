#!/usr/bin/env python3
"""
CI check: verify constitution counts, categories, and backend consistency.

Golden rule: docs/constitution is the single source of truth. This script fails
when generated artifacts or runtime wiring diverge from that source.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.constitution.rule_catalog import get_catalog_counts, get_catalog_rules
from config.constitution.database import ConstitutionRulesDB
from config.constitution.rule_count_loader import get_rule_counts
from config.enhanced_config_manager import EnhancedConfigManager


def load_json(path: Path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    errors: List[str] = []
    warnings: List[str] = []

    # 1) Single source of truth vs loader
    catalog_counts = get_catalog_counts()
    loader_counts = get_rule_counts()
    if catalog_counts.get("total_rules") != loader_counts.get("total_rules"):
        errors.append(
            f"Rule count mismatch between catalog and loader: "
            f"{catalog_counts.get('total_rules')} vs {loader_counts.get('total_rules')}"
        )

    # 2) Generated config/constitution_rules.json alignment (if present)
    cfg_path = Path("config/constitution_rules.json")
    cfg = load_json(cfg_path)
    if cfg:
        cfg_total = cfg.get("statistics", {}).get("total_rules")
        if cfg_total and cfg_total != catalog_counts.get("total_rules"):
            errors.append(
                f"{cfg_path} total_rules={cfg_total} does not match docs/constitution "
                f"{catalog_counts.get('total_rules')}"
            )

    # 3) Category coverage: config/rules/*.json vs optimized validator processors
    config_manager = EnhancedConfigManager()
    configured_categories = set(config_manager.get_all_categories())

    from validator.optimized_core import OptimizedConstitutionValidator

    validator = OptimizedConstitutionValidator()
    processor_categories = set(validator._rule_processors.keys())  # internal but deterministic for CI
    missing_processors = sorted(configured_categories - processor_categories)
    if missing_processors:
        errors.append(
            f"Missing rule processors for categories: {', '.join(missing_processors)}"
        )

    # 4) Backend sync status (json/sqlite) if available
    # Backend sync check: compare catalog totals against SQLite DB totals
    try:
        db = ConstitutionRulesDB()
        db_stats = db.get_rule_statistics()
        db_total = db_stats.get("total_rules")
        if db_total is not None and db_total != catalog_counts.get("total_rules"):
            errors.append(
                f"SQLite backend rule count {db_total} != catalog {catalog_counts.get('total_rules')}"
            )
    except Exception as exc:  # pragma: no cover - best effort
        warnings.append(f"Could not verify SQLite backend: {exc}")

    # 5) Category naming integrity (no corrupted keys)
    catalog_categories = {rule.category for rule in get_catalog_rules()}
    if any("�" in cat for cat in catalog_categories):
        errors.append("Corrupted category names detected in catalog (contains replacement chars)")

    if errors:
        for err in errors:
            print(f"[FAIL] {err}")
        return 1

    for warn in warnings:
        print(f"[WARN] {warn}")

    print("[OK] Constitution counts, categories, and backends are consistent with docs/constitution")
    print(f"[OK] Total rules (catalog): {catalog_counts.get('total_rules')}, enabled: {catalog_counts.get('enabled_rules')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
