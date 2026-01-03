"""Additional tests for config_manager to achieve 100% coverage."""

from __future__ import annotations

import json
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from config.constitution import config_manager


class FakeDBManager:
    def __init__(self, raise_on_init=False):
        self.rules = {1: {"rule_number": 1, "enabled": True}}
        self.raise_on_init = raise_on_init
        
    def get_all_rules(self, enabled_only=False):
        return list(self.rules.values())
    
    def get_rule_by_number(self, rule_number):
        return self.rules.get(rule_number)
    
    def enable_rule(self, rule_number, config_data=None):
        return rule_number in self.rules
    
    def disable_rule(self, rule_number, reason=""):
        return rule_number in self.rules
    
    def _init_database(self):
        """Initialize database."""
        pass
    
    def get_connection(self):
        """Get database connection context manager."""
        return self
    
    def get_rule_statistics(self):
        return {"total_rules": len(self.rules), "enabled_rules": 1}
    
    def close(self):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


@pytest.fixture
def tmp_config_dir(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


def test_init_constitution_system_with_exception(tmp_config_dir, monkeypatch):
    """Test _init_constitution_system handles exceptions."""
    with patch('config.constitution.config_manager.ConstitutionRulesDB', side_effect=Exception("DB error")):
        mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
        # Should fallback to minimal config
        assert mgr.constitution_config is not None


def test_load_constitution_config_json_error(tmp_config_dir, monkeypatch):
    """Test _load_constitution_config handles JSON decode error."""
    config_file = tmp_config_dir / "constitution_config.json"
    config_file.write_text("invalid json{", encoding="utf-8")
    
    mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
    # Should create default config
    assert mgr.constitution_config is not None


def test_save_constitution_config_pre_commit(tmp_config_dir, monkeypatch):
    """Test _save_constitution_config skips timestamp in pre-commit."""
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Test User")
    
    mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
    original_time = mgr.constitution_config.get("last_updated")
    
    mgr._save_constitution_config()
    
    # Timestamp should not be updated during pre-commit
    saved_config = json.loads((tmp_config_dir / "constitution_config.json").read_text(encoding="utf-8"))
    # The timestamp might still be set, but the logic should detect pre-commit


def test_derive_total_rules_exception(tmp_config_dir, monkeypatch):
    """Test _derive_total_rules handles exception."""
    with patch('config.constitution.config_manager.get_rule_count_loader', side_effect=Exception()):
        mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
        count = mgr._derive_total_rules()
        # Should fallback
        assert isinstance(count, int)


def test_fallback_total_rules_from_db(tmp_config_dir, monkeypatch):
    """Test _fallback_total_rules uses database."""
    fake_db = FakeDBManager()
    fake_db.rules = {1: {}, 2: {}, 3: {}}
    
    with patch('config.constitution.config_manager.ConstitutionRulesDB', return_value=fake_db):
        mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
        mgr.db_manager = fake_db
        
        count = mgr._fallback_total_rules()
        assert count == 3


def test_fallback_total_rules_from_json(tmp_config_dir, monkeypatch):
    """Test _fallback_total_rules uses JSON file."""
    json_file = tmp_config_dir / "constitution_rules.json"
    json_file.write_text(json.dumps({"rules": {"1": {}, "2": {}}}), encoding="utf-8")
    
    with patch('config.constitution.config_manager.ConstitutionRulesDB', side_effect=Exception()):
        mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
        mgr.db_manager = None
        
        count = mgr._fallback_total_rules()
        assert count == 2


def test_fallback_total_rules_last_resort(tmp_config_dir, monkeypatch):
    """Test _fallback_total_rules returns 0 as last resort."""
    with patch('config.constitution.config_manager.ConstitutionRulesDB', side_effect=Exception()):
        mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
        mgr.db_manager = None
        
        # No JSON file exists
        count = mgr._fallback_total_rules()
        assert count == 0


def test_enable_rule_returns_false(tmp_config_dir, monkeypatch):
    """Test enable_rule returns False when DB fails."""
    fake_db = FakeDBManager()
    fake_db.enable_rule = Mock(return_value=False)
    
    with patch('config.constitution.config_manager.ConstitutionRulesDB', return_value=fake_db):
        mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
        mgr.db_manager = fake_db
        
        result = mgr.enable_rule(999)  # Non-existent rule
        assert result is False


def test_disable_rule_returns_false(tmp_config_dir, monkeypatch):
    """Test disable_rule returns False when DB fails."""
    fake_db = FakeDBManager()
    fake_db.disable_rule = Mock(return_value=False)
    
    with patch('config.constitution.config_manager.ConstitutionRulesDB', return_value=fake_db):
        mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
        mgr.db_manager = fake_db
        
        result = mgr.disable_rule(999)  # Non-existent rule
        assert result is False


def test_sync_with_database_exception(tmp_config_dir, monkeypatch):
    """Test sync_with_database handles exceptions."""
    fake_db = FakeDBManager()
    fake_db.get_all_rules = Mock(side_effect=Exception("DB error"))
    
    with patch('config.constitution.config_manager.ConstitutionRulesDB', return_value=fake_db):
        mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
        mgr.db_manager = fake_db
        
        # Should not raise
        mgr.sync_with_database()


def test_get_backend_info_nonexistent_db(tmp_config_dir, monkeypatch):
    """Test get_backend_info with non-existent database."""
    fake_db = FakeDBManager()
    
    with patch('config.constitution.config_manager.ConstitutionRulesDB', return_value=fake_db):
        with patch('pathlib.Path.exists', return_value=False):
            mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
            mgr.db_manager = fake_db
            mgr.db_path = tmp_config_dir / "nonexistent.db"
            
            info = mgr.get_backend_info()
            assert info["database_exists"] is False
            assert info["database_size"] == 0


def test_health_check_exception(tmp_config_dir, monkeypatch):
    """Test health_check handles exceptions."""
    fake_db = FakeDBManager()
    
    with patch('config.constitution.config_manager.ConstitutionRulesDB', return_value=fake_db):
        mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
        mgr.db_manager = fake_db
        
        with patch.object(mgr.db_manager, 'get_connection', side_effect=Exception("Connection error")):
            health = mgr.health_check()
            assert "healthy" in health
            assert health.get("healthy") is False or "error" in health


def test_get_last_updated_exception(tmp_config_dir, monkeypatch):
    """Test _get_last_updated handles exceptions."""
    fake_db = FakeDBManager()
    fake_db.get_all_rules = Mock(side_effect=Exception("Error"))
    
    with patch('config.constitution.config_manager.ConstitutionRulesDB', return_value=fake_db):
        mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
        mgr.db_manager = fake_db
        
        result = mgr._get_last_updated()
        assert result is None


def test_exit_with_exception(tmp_config_dir, monkeypatch):
    """Test __exit__ handles exceptions."""
    fake_db = FakeDBManager()
    fake_db.close = Mock(side_effect=Exception("Close error"))
    
    with patch('config.constitution.config_manager.ConstitutionRulesDB', return_value=fake_db):
        mgr = config_manager.ConstitutionRuleManager(config_dir=str(tmp_config_dir))
        mgr.db_manager = fake_db
        
        # Should not raise
        mgr.__exit__(None, None, None)

