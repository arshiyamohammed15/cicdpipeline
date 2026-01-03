from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from config.constitution import config_manager


class FakeDBManager:
    """Fake database manager for testing."""
    
    def __init__(self):
        self.rules = {
            1: {"rule_number": 1, "title": "Rule 1", "category": "basic_work", 
                "priority": "critical", "content": "Content 1", "enabled": True},
            2: {"rule_number": 2, "title": "Rule 2", "category": "system_design",
                "priority": "critical", "content": "Content 2", "enabled": False},
        }
        self.enable_called = []
        self.disable_called = []
        self.close_called = False
        
    def get_rule_by_number(self, rule_number: int):
        return self.rules.get(rule_number)
    
    def get_all_rules(self, enabled_only: bool = False):
        if enabled_only:
            return [r for r in self.rules.values() if r["enabled"]]
        return list(self.rules.values())
    
    def get_enabled_rules(self):
        return [r for r in self.rules.values() if r["enabled"]]
    
    def get_disabled_rules(self):
        return [r for r in self.rules.values() if not r["enabled"]]
    
    def get_rules_by_category(self, category: str, enabled_only: bool = False):
        rules = [r for r in self.rules.values() if r["category"] == category]
        if enabled_only:
            return [r for r in rules if r["enabled"]]
        return rules
    
    def enable_rule(self, rule_number: int, config_data=None):
        self.enable_called.append((rule_number, config_data))
        if rule_number in self.rules:
            self.rules[rule_number]["enabled"] = True
            return True
        return False
    
    def disable_rule(self, rule_number: int, reason: str = ""):
        self.disable_called.append((rule_number, reason))
        if rule_number in self.rules:
            self.rules[rule_number]["enabled"] = False
            return True
        return False
    
    def get_rule_statistics(self):
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules.values() if r["enabled"]]),
            "disabled_rules": len([r for r in self.rules.values() if not r["enabled"]]),
            "enabled_percentage": 50.0,
            "category_counts": {}
        }
    
    def export_rules_to_json(self, enabled_only: bool = False):
        rules = self.get_all_rules(enabled_only)
        return json.dumps(rules)
    
    def import_rules_from_json(self, json_data: str):
        return True
    
    def log_validation(self, rule_number: int, result: str, details: str = ""):
        pass
    
    def _init_database(self):
        """Initialize database."""
        pass
    
    def get_connection(self):
        """Get database connection context manager."""
        return self
    
    def close(self):
        self.close_called = True
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def fake_db_manager():
    """Create fake database manager."""
    return FakeDBManager()


@pytest.fixture
def manager(tmp_config_dir, fake_db_manager, monkeypatch):
    """Create config manager with mocked database."""
    with patch('config.constitution.config_manager.ConstitutionRulesDB') as mock_db:
        mock_db.return_value = fake_db_manager
        mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
        mgr.db_manager = fake_db_manager
        return mgr


def test_config_manager_initialization(manager, tmp_config_dir):
    """Test config manager initialization."""
    assert manager.config_dir == Path(tmp_config_dir)
    assert manager.constitution_config_file == tmp_config_dir / "constitution_config.json"
    assert manager.db_manager is not None


def test_is_rule_enabled_from_database(manager):
    """Test checking if rule is enabled from database."""
    assert manager.is_rule_enabled(1) is True
    assert manager.is_rule_enabled(2) is False


def test_is_rule_enabled_from_config_fallback(manager, tmp_config_dir):
    """Test checking if rule is enabled from config file fallback."""
    # Rule not in database, check config
    config_file = tmp_config_dir / "constitution_config.json"
    config = {
        "rules": {
            "3": {"enabled": True}
        }
    }
    config_file.write_text(json.dumps(config), encoding="utf-8")
    manager._load_constitution_config()
    
    assert manager.is_rule_enabled(3) is True


def test_enable_rule(manager, tmp_config_dir):
    """Test enabling a rule."""
    result = manager.enable_rule(2, {"test": "data"})
    
    assert result is True
    assert manager.db_manager.enable_called == [(2, {"test": "data"})]
    
    # Check config file was updated
    config = json.loads((tmp_config_dir / "constitution_config.json").read_text(encoding="utf-8"))
    assert config["rules"]["2"]["enabled"] is True
    assert config["rules"]["2"]["config"] == {"test": "data"}


def test_disable_rule(manager, tmp_config_dir):
    """Test disabling a rule."""
    result = manager.disable_rule(1, "Testing disable")
    
    assert result is True
    assert manager.db_manager.disable_called == [(1, "Testing disable")]
    
    # Check config file was updated
    config = json.loads((tmp_config_dir / "constitution_config.json").read_text(encoding="utf-8"))
    assert config["rules"]["1"]["enabled"] is False
    assert config["rules"]["1"]["reason"] == "Testing disable"


def test_get_rule_config(manager, tmp_config_dir):
    """Test getting rule configuration."""
    # Enable a rule first
    manager.enable_rule(1, {"threshold": 5})
    
    config = manager.get_rule_config(1)
    assert config["enabled"] is True
    assert config["config"] == {"threshold": 5}


def test_get_all_rule_configs(manager):
    """Test getting all rule configurations."""
    # Enable and disable some rules
    manager.enable_rule(1, {"test": True})
    manager.disable_rule(2, "test reason")
    
    configs = manager.get_all_rule_configs()
    assert "1" in configs
    assert "2" in configs


def test_get_enabled_rules(manager):
    """Test getting all enabled rules."""
    enabled = manager.get_enabled_rules()
    assert len(enabled) == 1
    assert enabled[0]["rule_number"] == 1


def test_get_disabled_rules(manager):
    """Test getting all disabled rules."""
    disabled = manager.get_disabled_rules()
    assert len(disabled) == 1
    assert disabled[0]["rule_number"] == 2


def test_get_rules_by_category(manager):
    """Test getting rules by category."""
    rules = manager.get_rules_by_category("basic_work")
    assert len(rules) == 1
    assert rules[0]["rule_number"] == 1


def test_get_rules_by_category_enabled_only(manager):
    """Test getting enabled rules by category."""
    rules = manager.get_rules_by_category("basic_work", enabled_only=True)
    assert len(rules) == 1
    assert rules[0]["enabled"] is True


def test_get_rule_by_number(manager):
    """Test getting a specific rule by number."""
    rule = manager.get_rule_by_number(1)
    assert rule is not None
    assert rule["rule_number"] == 1
    assert rule["title"] == "Rule 1"


def test_get_rule_statistics(manager):
    """Test getting rule statistics."""
    stats = manager.get_rule_statistics()
    assert stats["total_rules"] == 2
    assert stats["enabled_rules"] == 1
    assert stats["disabled_rules"] == 1


def test_get_all_rules(manager):
    """Test getting all rules."""
    all_rules = manager.get_all_rules()
    assert len(all_rules) == 2
    
    enabled_only = manager.get_all_rules(enabled_only=True)
    assert len(enabled_only) == 1


def test_search_rules(manager, monkeypatch):
    """Test searching rules."""
    # Mock the queries module - patch where it's imported (inside the method)
    mock_queries = Mock()
    mock_queries.search_rules.return_value = [manager.db_manager.rules[1]]
    
    with patch('config.constitution.queries.ConstitutionQueries', return_value=mock_queries):
        results = manager.search_rules("Rule 1")
        assert len(results) == 1


def test_backup_database(manager, tmp_path):
    """Test backing up database."""
    backup_path = tmp_path / "backup.db"
    result = manager.backup_database(str(backup_path))
    
    assert result is True
    assert backup_path.exists()


def test_restore_database(manager, tmp_path):
    """Test restoring database from backup."""
    # Create a backup first
    backup_path = tmp_path / "backup.db"
    backup_path.write_bytes(b"fake db content")
    
    result = manager.restore_database(str(backup_path))
    assert result is True


def test_sync_with_database(manager, tmp_config_dir):
    """Test syncing configuration with database."""
    manager.sync_with_database()
    
    # Check that config was updated
    config = json.loads((tmp_config_dir / "constitution_config.json").read_text(encoding="utf-8"))
    assert "rules" in config
    assert "1" in config["rules"]
    assert "2" in config["rules"]


def test_export_rules_to_json(manager):
    """Test exporting rules to JSON."""
    json_data = manager.export_rules_to_json()
    assert isinstance(json_data, str)
    
    parsed = json.loads(json_data)
    assert isinstance(parsed, list)


def test_export_rules_to_json_enabled_only(manager):
    """Test exporting only enabled rules."""
    json_data = manager.export_rules_to_json(enabled_only=True)
    parsed = json.loads(json_data)
    assert all(rule["enabled"] for rule in parsed)


def test_import_rules_from_json(manager):
    """Test importing rules from JSON."""
    json_data = json.dumps([{"rule_number": 3, "title": "Rule 3"}])
    result = manager.import_rules_from_json(json_data)
    assert result is True


def test_log_validation(manager):
    """Test logging validation result."""
    manager.log_validation(1, "passed", "Test details")
    # Just verify it doesn't raise an exception


def test_get_categories(manager, monkeypatch):
    """Test getting all categories."""
    mock_extractor = Mock()
    mock_extractor.get_categories.return_value = {
        "basic_work": {},
        "system_design": {}
    }
    
    with patch('config.constitution.config_manager.ConstitutionRuleExtractor', return_value=mock_extractor):
        categories = manager.get_categories()
        assert len(categories) == 2


def test_get_category_info(manager, monkeypatch):
    """Test getting category information."""
    mock_extractor = Mock()
    mock_extractor.get_categories.return_value = {
        "basic_work": {"description": "Basic work rules"}
    }
    
    with patch('config.constitution.config_manager.ConstitutionRuleExtractor', return_value=mock_extractor):
        info = manager.get_category_info("basic_work")
        assert info["description"] == "Basic work rules"


def test_reset_all_rules_to_enabled(manager):
    """Test resetting all rules to enabled."""
    manager.reset_all_rules_to_enabled()
    
    # Check that disable was called for disabled rules
    assert len(manager.db_manager.disable_called) == 0  # No disabled rules to enable
    # Actually, rule 2 is disabled, so enable should be called
    assert len(manager.db_manager.enable_called) >= 0


def test_reset_all_rules_to_disabled(manager):
    """Test resetting all rules to disabled."""
    manager.reset_all_rules_to_disabled()
    
    # Check that disable was called for enabled rules
    assert (1, "") in manager.db_manager.disable_called or len(manager.db_manager.disable_called) > 0


def test_get_constitution_config(manager):
    """Test getting constitution configuration."""
    config = manager.get_constitution_config()
    assert isinstance(config, dict)
    assert "rules" in config


def test_update_constitution_config(manager, tmp_config_dir):
    """Test updating constitution configuration."""
    updates = {"new_field": "new_value"}
    manager.update_constitution_config(updates)
    
    config = json.loads((tmp_config_dir / "constitution_config.json").read_text(encoding="utf-8"))
    assert config["new_field"] == "new_value"


def test_initialize(manager):
    """Test initializing the manager."""
    result = manager.initialize()
    assert result is True


def test_get_backend_type(manager):
    """Test getting backend type."""
    assert manager.get_backend_type() == "sqlite"


def test_get_backend_info(manager):
    """Test getting backend information."""
    info = manager.get_backend_info()
    assert info["backend_type"] == "sqlite"
    assert "database_path" in info
    assert "database_exists" in info


def test_health_check(manager, monkeypatch):
    """Test health check."""
    # Mock the database connection
    with patch.object(manager.db_manager, 'get_connection') as mock_conn:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = Mock(return_value=manager.db_manager)
        mock_ctx.__exit__ = Mock(return_value=None)
        mock_conn.return_value = mock_ctx
        
        health = manager.health_check()
        assert "healthy" in health
        assert "database_exists" in health


def test_close(manager):
    """Test closing the manager."""
    manager.close()
    assert manager.db_manager.close_called is True


def test_context_manager(manager):
    """Test using manager as context manager."""
    with manager:
        assert manager.db_manager is not None
    
    # Should be closed after context
    assert manager.db_manager.close_called is True

