"""Additional tests for sync_manager to achieve 100% coverage."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from config.constitution import sync_manager


@pytest.fixture
def tmp_config_dir(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def sync_mgr(tmp_config_dir):
    return sync_manager.ConstitutionSyncManager(config_dir=str(tmp_config_dir))


def test_resolve_conflicts_json_primary(sync_mgr, tmp_config_dir, monkeypatch):
    """Test _resolve_conflicts with JSON as primary backend."""
    conflicts = [
        {
            "rule_number": 1,
            "type": "missing_in_sqlite",
            "json_data": {"rule_number": 1, "title": "Rule 1", "category": "test", "priority": "high", "content": "Content", "enabled": True}
        }
    ]
    
    mock_sqlite = Mock()
    mock_sqlite.db_manager = Mock()
    mock_sqlite.db_manager.insert_rule = Mock()
    mock_sqlite.close = Mock()
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", lambda *a, **k: mock_sqlite)
    
    result = sync_mgr._resolve_conflicts(conflicts, "json")
    assert result["resolved"] == 1


def test_resolve_conflicts_json_missing_in_json(sync_mgr, tmp_config_dir, monkeypatch):
    """Test _resolve_conflicts with JSON primary, missing_in_json type."""
    conflicts = [
        {
            "rule_number": 1,
            "type": "missing_in_json",
            "sqlite_data": {"rule_number": 1}
        }
    ]
    
    mock_json = Mock()
    mock_json.json_manager = Mock()
    mock_json.json_manager.data = {"rules": {}}
    mock_json.json_manager._update_statistics = Mock()
    mock_json.json_manager._save_database = Mock()
    mock_json.close = Mock()
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManagerJSON", lambda *a, **k: mock_json)
    
    result = sync_mgr._resolve_conflicts(conflicts, "json")
    # Should try to remove from SQLite or update JSON
    assert result["total"] == 1


def test_add_rule_to_json_error(sync_mgr, tmp_config_dir, monkeypatch):
    """Test _add_rule_to_json handles errors."""
    rule_data = {"rule_number": 1, "title": "Rule 1", "category": "test", "priority": "high", "content": "Content", "enabled": True}
    
    mock_json = Mock()
    mock_json.json_manager = Mock()
    mock_json.json_manager.data = {"rules": {}}
    mock_json.json_manager._update_statistics = Mock(side_effect=Exception("Error"))
    mock_json.json_manager._save_database = Mock()
    mock_json.close = Mock()
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManagerJSON", lambda *a, **k: mock_json)
    
    # Should not raise, should close manager
    sync_mgr._add_rule_to_json(rule_data)
    mock_json.close.assert_called_once()


def test_add_rule_to_sqlite_error(sync_mgr, tmp_config_dir, monkeypatch):
    """Test _add_rule_to_sqlite handles errors."""
    rule_data = {"rule_number": 1, "title": "Rule 1", "category": "test", "priority": "high", "content": "Content", "enabled": True}
    
    mock_sqlite = Mock()
    mock_sqlite.db_manager = Mock()
    mock_sqlite.db_manager.insert_rule = Mock(side_effect=Exception("Error"))
    mock_sqlite.close = Mock()
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", lambda *a, **k: mock_sqlite)
    
    # Should not raise, should close manager
    sync_mgr._add_rule_to_sqlite(rule_data)
    mock_sqlite.close.assert_called_once()


def test_update_rule_in_json_not_exists(sync_mgr, tmp_config_dir, monkeypatch):
    """Test _update_rule_in_json when rule doesn't exist."""
    rule_data = {"rule_number": 999, "title": "Rule 999"}
    
    mock_json = Mock()
    mock_json.json_manager = Mock()
    mock_json.json_manager.data = {"rules": {}}
    mock_json.json_manager._save_database = Mock()
    mock_json.close = Mock()
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManagerJSON", lambda *a, **k: mock_json)
    
    # Should not raise
    sync_mgr._update_rule_in_json(rule_data)
    mock_json.close.assert_called_once()


def test_update_rule_in_sqlite_error(sync_mgr, tmp_config_dir, monkeypatch):
    """Test _update_rule_in_sqlite handles errors."""
    rule_data = {"rule_number": 1, "title": "Rule 1", "category": "test", "priority": "high", "content": "Content", "enabled": True}
    
    mock_sqlite = Mock()
    mock_sqlite.db_manager = Mock()
    mock_sqlite.db_manager.update_rule = Mock(side_effect=Exception("Error"))
    mock_sqlite.close = Mock()
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", lambda *a, **k: mock_sqlite)
    
    # Should not raise, should close manager
    sync_mgr._update_rule_in_sqlite(rule_data)
    mock_sqlite.close.assert_called_once()


def test_remove_rule_from_json_not_exists(sync_mgr, tmp_config_dir, monkeypatch):
    """Test _remove_rule_from_json when rule doesn't exist."""
    mock_json = Mock()
    mock_json.json_manager = Mock()
    mock_json.json_manager.data = {"rules": {}}
    mock_json.json_manager._update_statistics = Mock()
    mock_json.json_manager._save_database = Mock()
    mock_json.close = Mock()
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManagerJSON", lambda *a, **k: mock_json)
    
    # Should not raise
    sync_mgr._remove_rule_from_json(999)
    mock_json.close.assert_called_once()


def test_remove_rule_from_sqlite_error(sync_mgr, tmp_config_dir, monkeypatch):
    """Test _remove_rule_from_sqlite handles errors."""
    mock_sqlite = Mock()
    mock_sqlite.db_manager = Mock()
    mock_sqlite.db_manager.delete_rule = Mock(side_effect=Exception("Error"))
    mock_sqlite.close = Mock()
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", lambda *a, **k: mock_sqlite)
    
    # Should not raise, should close manager
    sync_mgr._remove_rule_from_sqlite(1)
    mock_sqlite.close.assert_called_once()


def test_verify_sync_exception(sync_mgr, tmp_config_dir, monkeypatch):
    """Test verify_sync handles exceptions."""
    def failing_manager(*a, **k):
        raise Exception("Manager error")
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", failing_manager)
    
    result = sync_mgr.verify_sync()
    assert "synchronized" in result
    assert result.get("synchronized") is False or "error" in result

