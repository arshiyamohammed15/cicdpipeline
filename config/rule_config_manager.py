from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class RuleConfigManager:
    """Lightweight rule configuration manager used by tests.

    This implementation treats all rules as enabled by default and provides
    category lookups from rules_config.json when available.
    """

    def __init__(self, config_manager: Optional[object] = None, config_path: str = "rules_config.json") -> None:
        self._config_manager = config_manager
        self._config_path = Path(config_path)
        self._config: Dict = {}
        self._load()

    def _load(self) -> None:
        if self._config_path.exists():
            try:
                self._config = json.loads(self._config_path.read_text(encoding="utf-8"))
            except Exception:
                self._config = {}
        else:
            self._config = {}

    def is_rule_enabled(self, rule_id: str, file_path: Optional[str] = None) -> bool:
        """Return True for all rules by default."""
        return True

    def get_rule_status_report(self) -> Dict[str, str]:
        """Return a simple status map indicating all rules are enabled."""
        report: Dict[str, str] = {}
        # If we have explicit rules, report them; else return empty map
        rules = self._config.get("rules", [])
        if isinstance(rules, list):
            for rule in rules:
                rid = rule.get("id") or rule.get("rule_id")
                if rid:
                    report[rid] = "enabled"
        return report

    def get_enabled_rules(self, category: Optional[str] = None) -> List[int]:
        """Return enabled rule numbers for a category if available; otherwise empty list.

        The core validator uses this to early-exit category checks when empty.
        """
        if not category:
            return []
        categories = self._config.get("categories", {})
        if not isinstance(categories, dict):
            return []
        cat = categories.get(category)
        if not isinstance(cat, dict):
            return []
        rules = cat.get("rules", [])
        return [int(r) for r in rules if isinstance(r, int) or (isinstance(r, str) and r.isdigit())]


