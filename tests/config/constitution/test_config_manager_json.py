from __future__ import annotations

import json
from pathlib import Path
import pytest

from config.constitution import config_manager_json


class FakeConstitutionRulesJSON:
    def __init__(self, json_path: str = "") -> None:
        self.json_path = json_path
        self.rules = [
            {"rule_number": 1, "enabled": True, "category": "cat-a"},
            {"rule_number": 2, "enabled": False, "category": "cat-b"},
        ]
        self.init_called = False
        self.backup_called_with: list[str] = []
        self.restore_called = False

    def _init_database(self) -> None:
        self.init_called = True

    def get_all_rules(self, enabled_only: bool = False):
        if enabled_only:
            return [r for r in self.rules if r["enabled"]]
        return list(self.rules)

    def get_rule_by_number(self, number: int):
        return next((r for r in self.rules if r["rule_number"] == number), None)

    def enable_rule(self, number: int, config_data=None) -> bool:
        rule = self.get_rule_by_number(number)
        if rule:
            rule["enabled"] = True
            if config_data:
                rule["config"] = config_data
        return True

    def disable_rule(self, number: int, reason: str = "") -> bool:
        rule = self.get_rule_by_number(number)
        if rule:
            rule["enabled"] = False
            rule["disabled_reason"] = reason
        return True

    def get_rules_by_category(self, category: str, enabled_only: bool = False):
        return [r for r in self.rules if r["category"] == category and (r["enabled"] or not enabled_only)]

    def get_rule_statistics(self):
        return {"total": len(self.rules), "enabled": len([r for r in self.rules if r["enabled"]])}

    def search_rules(self, search_term: str, enabled_only: bool = False):
        return [r for r in self.rules if search_term.lower() in str(r).lower() and (r["enabled"] or not enabled_only)]

    def export_rules_to_json(self, enabled_only: bool = False) -> str:
        return json.dumps(self.get_all_rules(enabled_only))

    def get_categories(self):
        return {"categories": sorted({r["category"] for r in self.rules})}

    def get_backend_info(self):
        return {"backend": "fake-json"}

    def backup_database(self, backup_path: str) -> bool:
        self.backup_called_with.append(backup_path)
        Path(backup_path).write_text("backup")
        return True

    def restore_database(self, backup_path: str) -> bool:
        self.restore_called = True
        return Path(backup_path).exists()

    def health_check(self):
        return {"healthy": True}

    def close(self):
        pass


def _make_manager(tmp_path, monkeypatch) -> config_manager_json.ConstitutionRuleManagerJSON:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", FakeConstitutionRulesJSON)
    manager = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(config_dir), json_path=str(tmp_path / "rules.json"))
    return manager


@pytest.mark.constitution
def test_initialize_syncs_rules_and_creates_config(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)

    assert manager.initialize() is True
    assert Path(manager.constitution_config_path).exists()
    assert manager.json_manager.init_called is True
    assert manager.get_all_rules(enabled_only=False)
    # sync adds entries to config data
    configs = manager.get_all_rule_configs()
    assert "1" in configs and "2" in configs


@pytest.mark.constitution
def test_enable_disable_and_health_check(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.initialize()

    assert manager.enable_rule(2, {"threshold": 5}) is True
    cfg = manager.get_rule_config(2)
    assert cfg["enabled"] is True
    assert cfg["config"] == {"threshold": 5}

    assert manager.disable_rule(1, reason="temporary") is True
    cfg1 = manager.get_rule_config(1)
    assert cfg1["enabled"] is False
    assert cfg1["disabled_reason"] == "temporary"

    health = manager.health_check()
    assert health["healthy"] is True
    assert health["configuration"]["config_file_exists"] is True
    assert health["configuration"]["config_valid"] is True


@pytest.mark.constitution
def test_backup_and_restore(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.initialize()

    backup_path = tmp_path / "backup.json"
    assert manager.backup_database(str(backup_path)) is True
    assert backup_path.exists()

    assert manager.restore_database(str(backup_path)) is True
    assert manager.json_manager.restore_called is True
