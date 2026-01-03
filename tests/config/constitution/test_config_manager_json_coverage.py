"""Additional tests for config_manager_json to achieve 100% coverage."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from config.constitution import config_manager_json


class FakeConstitutionRulesJSON:
    def __init__(self, json_path: str = "", healthy: bool = True):
        self.json_path = json_path
        self.rules = [
            {"rule_number": 1, "enabled": True, "category": "cat-a"},
            {"rule_number": 2, "enabled": False, "category": "cat-b"},
        ]
        self.data = {"rules": {str(i): r for i, r in enumerate(self.rules, 1)}}
        self._healthy = healthy
        
    def _init_database(self):
        pass
    
    def get_all_rules(self, enabled_only=False):
        if enabled_only:
            return [r for r in self.rules if r["enabled"]]
        return list(self.rules)
    
    def get_rule_by_number(self, number):
        return next((r for r in self.rules if r["rule_number"] == number), None)
    
    def enable_rule(self, number, config_data=None):
        rule = self.get_rule_by_number(number)
        if rule:
            rule["enabled"] = True
        return rule is not None
    
    def disable_rule(self, number, reason=""):
        rule = self.get_rule_by_number(number)
        if rule:
            rule["enabled"] = False
        return rule is not None
    
    def get_rules_by_category(self, category, enabled_only=False):
        return [r for r in self.rules if r["category"] == category]
    
    def get_rule_statistics(self):
        return {"total": len(self.rules), "enabled": len([r for r in self.rules if r["enabled"]])}
    
    def search_rules(self, search_term, enabled_only=False):
        return [r for r in self.rules if search_term.lower() in str(r).lower()]
    
    def export_rules_to_json(self, enabled_only=False):
        return json.dumps(self.get_all_rules(enabled_only))
    
    def get_categories(self):
        return {"categories": sorted({r["category"] for r in self.rules})}
    
    def get_backend_info(self):
        return {"backend_type": "json", "json_path": "fake.json"}
    
    def backup_database(self, backup_path):
        Path(backup_path).write_text("backup")
        return True
    
    def restore_database(self, backup_path):
        return Path(backup_path).exists()
    
    def health_check(self):
        return {"healthy": self._healthy}
    
    def close(self):
        pass


@pytest.fixture
def tmp_config_dir(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def manager(tmp_config_dir, monkeypatch):
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", FakeConstitutionRulesJSON)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    return mgr


def test_load_constitution_config_json_error(tmp_config_dir, monkeypatch):
    """Test _load_constitution_config handles JSON decode error."""
    config_file = tmp_config_dir / "constitution_config.json"
    config_file.write_text("invalid json{", encoding="utf-8")
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", FakeConstitutionRulesJSON)
    
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    # Should create default config
    assert mgr._config_data is not None


def test_validate_config_structure_missing_key(tmp_config_dir, monkeypatch):
    """Test _validate_config_structure raises on missing key."""
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", FakeConstitutionRulesJSON)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr._config_data = {"version": "1.0"}  # Missing "rules"
    
    with pytest.raises(ValueError, match="Missing required config key"):
        mgr._validate_config_structure()


def test_repair_config_file(tmp_config_dir, monkeypatch):
    """Test _repair_config_file."""
    config_file = tmp_config_dir / "constitution_config.json"
    config_file.write_text("invalid json{", encoding="utf-8")
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", FakeConstitutionRulesJSON)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    
    result = mgr._repair_config_file()
    # Should attempt repair
    assert isinstance(result, bool)


def test_save_constitution_config_error(tmp_config_dir, monkeypatch):
    """Test _save_constitution_config handles errors."""
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", FakeConstitutionRulesJSON)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    
    with patch('builtins.open', side_effect=PermissionError("Permission denied")):
        # Should not raise
        mgr._save_constitution_config()


def test_initialize_failure(tmp_config_dir, monkeypatch):
    """Test initialize handles failures."""
    fake_json = FakeConstitutionRulesJSON()
    fake_json._init_database = Mock(side_effect=Exception("Init failed"))
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    
    result = mgr.initialize()
    assert result is False


def test_enable_rule_failure(tmp_config_dir, monkeypatch):
    """Test enable_rule handles failures."""
    fake_json = FakeConstitutionRulesJSON()
    fake_json.enable_rule = Mock(return_value=False)
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    
    result = mgr.enable_rule(999)
    assert result is False


def test_enable_rule_exception(tmp_config_dir, monkeypatch):
    """Test enable_rule handles exceptions."""
    fake_json = FakeConstitutionRulesJSON()
    fake_json.enable_rule = Mock(side_effect=Exception("Error"))
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    
    result = mgr.enable_rule(1)
    assert result is False


def test_disable_rule_failure(tmp_config_dir, monkeypatch):
    """Test disable_rule handles failures."""
    fake_json = FakeConstitutionRulesJSON()
    fake_json.disable_rule = Mock(return_value=False)
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    
    result = mgr.disable_rule(999)
    assert result is False


def test_disable_rule_exception(tmp_config_dir, monkeypatch):
    """Test disable_rule handles exceptions."""
    fake_json = FakeConstitutionRulesJSON()
    fake_json.disable_rule = Mock(side_effect=Exception("Error"))
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    
    result = mgr.disable_rule(1)
    assert result is False


def test_get_backend_type(manager):
    """Test get_backend_type."""
    assert manager.get_backend_type() == "json"


def test_get_backend_info(manager):
    """Test get_backend_info."""
    info = manager.get_backend_info()
    assert info["backend_type"] == "json"
    assert "json_path" in info


def test_backup_database_error(tmp_config_dir, monkeypatch):
    """Test backup_database handles errors."""
    fake_json = FakeConstitutionRulesJSON()
    fake_json.backup_database = Mock(return_value=False)
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    
    result = mgr.backup_database("backup.json")
    assert result is False


def test_restore_database_error(tmp_config_dir, monkeypatch):
    """Test restore_database handles errors."""
    fake_json = FakeConstitutionRulesJSON()
    fake_json.restore_database = Mock(return_value=False)
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    
    result = mgr.restore_database("nonexistent.json")
    assert result is False


def test_health_check_exception(tmp_config_dir, monkeypatch):
    """Test health_check handles exceptions."""
    fake_json = FakeConstitutionRulesJSON()
    fake_json.health_check = Mock(side_effect=Exception("Health check failed"))
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    
    health = mgr.health_check()
    assert "healthy" in health
    assert health.get("healthy") is False or "error" in health


def test_sync_with_database(tmp_config_dir, monkeypatch):
    """Test _sync_with_database."""
    fake_json = FakeConstitutionRulesJSON()
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    
    mgr._sync_with_database()
    # Should not raise


def test_get_rule_config(manager):
    """Test get_rule_config."""
    manager._config_data = {"rules": {"1": {"enabled": True}}}
    
    config = manager.get_rule_config(1)
    assert config["enabled"] is True


def test_get_rule_config_not_found(manager):
    """Test get_rule_config for non-existent rule."""
    manager._config_data = {"rules": {}}
    
    config = manager.get_rule_config(999)
    assert config is None


def test_update_rule_config(tmp_config_dir, monkeypatch):
    """Test update_rule_config."""
    fake_json = FakeConstitutionRulesJSON()
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    
    result = mgr.update_rule_config(1, {"test": "value"})
    assert result is True
    
    config = mgr.get_rule_config(1)
    assert config["test"] == "value"


def test_update_rule_config_exception(tmp_config_dir, monkeypatch):
    """Test update_rule_config handles exceptions."""
    fake_json = FakeConstitutionRulesJSON()
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    
    with patch.object(mgr, '_save_constitution_config', side_effect=Exception("Save error")):
        result = mgr.update_rule_config(1, {"test": "value"})
        assert result is False


def test_health_check_config_not_exists(tmp_config_dir, monkeypatch):
    """Test health_check when config file doesn't exist initially."""
    fake_json = FakeConstitutionRulesJSON()
    # health_check is already a method, don't need to mock it
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    mgr._initialized = False  # Prevent auto-initialization
    
    # Remove config file if it was created
    if mgr.constitution_config_path.exists():
        mgr.constitution_config_path.unlink()
    
    # Mock initialize to not create file
    original_init = mgr.initialize
    def mock_init():
        mgr._initialized = True
        return True
    mgr.initialize = mock_init
    
    health = mgr.health_check()
    # After health_check, config should exist (created by health_check's initialize call)
    # But we're testing the path where it doesn't exist initially
    assert "configuration" in health


def test_health_check_config_invalid(tmp_config_dir, monkeypatch):
    """Test health_check when config file is invalid."""
    fake_json = FakeConstitutionRulesJSON()
    # health_check is already a method, don't need to mock it
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    mgr._initialized = True  # Prevent auto-initialization
    
    # Write invalid JSON after initialization to test health_check's validation
    config_file = tmp_config_dir / "constitution_config.json"
    config_file.write_text("invalid json{", encoding="utf-8")
    
    health = mgr.health_check()
    # The config should be detected as invalid
    assert health["configuration"]["config_valid"] is False


def test_health_check_db_unhealthy(tmp_config_dir, monkeypatch):
    """Test health_check when database is unhealthy."""
    fake_json = FakeConstitutionRulesJSON(healthy=False)
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    
    health = mgr.health_check()
    assert health["healthy"] is False


def test_sync_with_database_exception(tmp_config_dir, monkeypatch):
    """Test _sync_with_database handles exceptions."""
    fake_json = FakeConstitutionRulesJSON()
    fake_json.get_all_rules = Mock(side_effect=Exception("Error"))
    
    monkeypatch.setattr(config_manager_json, "ConstitutionRulesJSON", lambda *a, **k: fake_json)
    mgr = config_manager_json.ConstitutionRuleManagerJSON(config_dir=str(tmp_config_dir))
    mgr.json_manager = fake_json
    
    # Should not raise
    mgr._sync_with_database()


def test_get_all_rule_configs(manager):
    """Test get_all_rule_configs."""
    manager._config_data = {"rules": {"1": {"enabled": True}, "2": {"enabled": False}}}
    
    configs = manager.get_all_rule_configs()
    assert len(configs) == 2
    assert "1" in configs
    assert "2" in configs


def test_close(manager):
    """Test close method."""
    manager._initialized = True
    manager.close()
    assert manager._initialized is False

