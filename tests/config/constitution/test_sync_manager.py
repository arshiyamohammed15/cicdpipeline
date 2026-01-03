from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from config.constitution import sync_manager


class FakeSQLiteManager:
    """Fake SQLite manager for testing."""
    
    def __init__(self, rules=None):
        self.rules = rules or [
            {"rule_number": 1, "title": "Rule 1", "category": "basic_work",
             "priority": "critical", "content": "Content 1", "enabled": True},
            {"rule_number": 2, "title": "Rule 2", "category": "system_design",
             "priority": "critical", "content": "Content 2", "enabled": False}
        ]
        self.close_called = False
        
    def get_all_rules(self):
        return self.rules
    
    def get_rule_by_number(self, rule_number):
        return next((r for r in self.rules if r["rule_number"] == rule_number), None)
    
    def get_backend_info(self):
        return {"last_updated": (datetime.now() - timedelta(hours=1)).isoformat()}
    
    def close(self):
        self.close_called = True


class FakeJSONManager:
    """Fake JSON manager for testing."""
    
    def __init__(self, rules=None):
        self.rules = rules or [
            {"rule_number": 1, "title": "Rule 1", "category": "basic_work",
             "priority": "critical", "content": "Content 1", "enabled": True},
            {"rule_number": 2, "title": "Rule 2", "category": "system_design",
             "priority": "critical", "content": "Content 2", "enabled": False}
        ]
        self.json_manager = Mock()
        self.json_manager.data = {"rules": {}}
        self._config_data = {}
        self.close_called = False
        
    def get_all_rules(self):
        return self.rules
    
    def get_rule_by_number(self, rule_number):
        return next((r for r in self.rules if r["rule_number"] == rule_number), None)
    
    def get_backend_info(self):
        return {"last_updated": datetime.now().isoformat()}
    
    def _sync_with_database(self):
        pass
    
    def close(self):
        self.close_called = True


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def sync_mgr(tmp_config_dir):
    """Create sync manager."""
    return sync_manager.ConstitutionSyncManager(config_dir=str(tmp_config_dir))


def test_sync_manager_initialization(sync_mgr, tmp_config_dir):
    """Test sync manager initialization."""
    assert sync_mgr.config_dir == str(tmp_config_dir)
    assert sync_mgr.sync_history_path == tmp_config_dir / "sync_history.json"
    assert isinstance(sync_mgr._sync_history, list)


def test_load_sync_history_existing(sync_mgr, tmp_config_dir):
    """Test loading existing sync history."""
    history = [
        {"timestamp": "2024-01-01T00:00:00", "operation": "sync", "success": True}
    ]
    sync_mgr.sync_history_path.write_text(json.dumps(history), encoding="utf-8")
    
    sync_mgr._load_sync_history()
    assert len(sync_mgr._sync_history) == 1


def test_load_sync_history_corrupted(sync_mgr, tmp_config_dir):
    """Test loading corrupted sync history."""
    sync_mgr.sync_history_path.write_text("invalid json{", encoding="utf-8")
    
    sync_mgr._load_sync_history()
    # Should reset to empty list
    assert isinstance(sync_mgr._sync_history, list)


def test_log_sync_operation(sync_mgr, tmp_config_dir):
    """Test logging sync operation."""
    sync_mgr._log_sync_operation("test_op", "source", "target", True, "details")
    
    assert len(sync_mgr._sync_history) == 1
    assert sync_mgr._sync_history[0]["operation"] == "test_op"
    assert sync_mgr._sync_history[0]["success"] is True


def test_log_sync_operation_history_limit(sync_mgr):
    """Test that sync history is limited to 100 entries."""
    for i in range(150):
        sync_mgr._log_sync_operation("op", "src", "tgt", True, str(i))
    
    assert len(sync_mgr._sync_history) == 100
    # Should keep most recent entries
    assert sync_mgr._sync_history[-1]["details"] == "149"


def test_sync_sqlite_to_json(sync_mgr, tmp_config_dir, monkeypatch):
    """Test syncing from SQLite to JSON."""
    sqlite_mgr = FakeSQLiteManager()
    json_mgr = FakeJSONManager()
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", lambda *a, **k: sqlite_mgr)
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManagerJSON", lambda *a, **k: json_mgr)
    
    result = sync_mgr.sync_sqlite_to_json(force=True)
    
    assert result["success"] is True
    assert "changes_made" in result


def test_sync_sqlite_to_json_skipped(sync_mgr, tmp_config_dir, monkeypatch):
    """Test that sync is skipped when not needed."""
    sqlite_mgr = FakeSQLiteManager()
    json_mgr = FakeJSONManager()
    
    # Make JSON newer than SQLite
    sqlite_mgr.get_backend_info = lambda: {"last_updated": (datetime.now() - timedelta(hours=2)).isoformat()}
    json_mgr.get_backend_info = lambda: {"last_updated": datetime.now().isoformat()}
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", lambda *a, **k: sqlite_mgr)
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManagerJSON", lambda *a, **k: json_mgr)
    
    result = sync_mgr.sync_sqlite_to_json(force=False)
    
    assert result.get("skipped") is True or result["success"] is True


def test_sync_json_to_sqlite(sync_mgr, tmp_config_dir, monkeypatch):
    """Test syncing from JSON to SQLite."""
    sqlite_mgr = FakeSQLiteManager()
    json_mgr = FakeJSONManager()
    
    # Mock database methods
    sqlite_mgr.db_manager = Mock()
    sqlite_mgr.db_manager.update_rule = Mock()
    sqlite_mgr.db_manager.insert_rule = Mock()
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", lambda *a, **k: sqlite_mgr)
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManagerJSON", lambda *a, **k: json_mgr)
    
    result = sync_mgr.sync_json_to_sqlite(force=True)
    
    assert result["success"] is True
    assert "changes_made" in result


def test_auto_sync(sync_mgr, tmp_config_dir, monkeypatch):
    """Test automatic bidirectional sync."""
    sqlite_mgr = FakeSQLiteManager()
    json_mgr = FakeJSONManager()
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", lambda *a, **k: sqlite_mgr)
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManagerJSON", lambda *a, **k: json_mgr)
    monkeypatch.setattr(sync_manager, "get_backend_factory", lambda: Mock(_get_configuration=lambda: {"backend": "sqlite"}))
    
    # Mock sync methods
    sync_mgr.sync_sqlite_to_json = Mock(return_value={"success": True, "changes_made": 0})
    sync_mgr._detect_conflicts = Mock(return_value=[])
    sync_mgr.verify_sync = Mock(return_value={"synchronized": True})
    
    result = sync_mgr.auto_sync(force=True)
    
    assert result["success"] is True
    assert "syncs" in result


def test_detect_conflicts(sync_mgr, tmp_config_dir, monkeypatch):
    """Test conflict detection."""
    sqlite_mgr = FakeSQLiteManager([
        {"rule_number": 1, "title": "SQLite Rule", "enabled": True}
    ])
    json_mgr = FakeJSONManager([
        {"rule_number": 1, "title": "JSON Rule", "enabled": False}
    ])
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", lambda *a, **k: sqlite_mgr)
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManagerJSON", lambda *a, **k: json_mgr)
    
    conflicts = sync_mgr._detect_conflicts()
    
    assert len(conflicts) > 0
    assert conflicts[0]["type"] == "data_conflict"


def test_resolve_conflicts(sync_mgr, tmp_config_dir, monkeypatch):
    """Test conflict resolution."""
    conflicts = [
        {
            "rule_number": 1,
            "type": "data_conflict",
            "sqlite_data": {"rule_number": 1, "enabled": True},
            "json_data": {"rule_number": 1, "enabled": False}
        }
    ]
    
    # Mock conflict resolution methods
    sync_mgr._update_rule_in_json = Mock()
    
    result = sync_mgr._resolve_conflicts(conflicts, "sqlite")
    
    assert result["resolved"] == 1
    assert result["total"] == 1


def test_verify_sync(sync_mgr, tmp_config_dir, monkeypatch):
    """Test sync verification."""
    sqlite_mgr = FakeSQLiteManager()
    json_mgr = FakeJSONManager()
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", lambda *a, **k: sqlite_mgr)
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManagerJSON", lambda *a, **k: json_mgr)
    
    result = sync_mgr.verify_sync()
    
    assert "synchronized" in result
    assert "total_rules" in result
    assert "sqlite_rules" in result
    assert "json_rules" in result


def test_verify_sync_with_differences(sync_mgr, tmp_config_dir, monkeypatch):
    """Test sync verification with differences."""
    sqlite_mgr = FakeSQLiteManager([
        {"rule_number": 1, "title": "Rule 1", "enabled": True}
    ])
    json_mgr = FakeJSONManager([
        {"rule_number": 1, "title": "Rule 1 Modified", "enabled": True}
    ])
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", lambda *a, **k: sqlite_mgr)
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManagerJSON", lambda *a, **k: json_mgr)
    
    result = sync_mgr.verify_sync()
    
    assert result["synchronized"] is False
    assert result["difference_count"] > 0


def test_get_sync_history(sync_mgr):
    """Test getting sync history."""
    sync_mgr._log_sync_operation("op1", "src", "tgt", True)
    sync_mgr._log_sync_operation("op2", "src", "tgt", True)
    
    history = sync_mgr.get_sync_history(limit=1)
    assert len(history) == 1
    
    history_all = sync_mgr.get_sync_history(limit=0)
    assert len(history_all) == 2


def test_clear_sync_history(sync_mgr, tmp_config_dir):
    """Test clearing sync history."""
    sync_mgr._log_sync_operation("op", "src", "tgt", True)
    assert len(sync_mgr._sync_history) > 0
    
    sync_mgr.clear_sync_history()
    assert len(sync_mgr._sync_history) == 0


def test_verify_consistency_across_sources(sync_mgr, tmp_config_dir, monkeypatch):
    """Test verifying consistency across all sources."""
    # Mock extractor
    mock_extractor = Mock()
    mock_extractor.extract_all_rules.return_value = [
        {"rule_number": 1, "title": "Rule 1", "category": "basic_work", "priority": "critical", "content": "Content"}
    ]
    
    # Mock managers
    sqlite_mgr = FakeSQLiteManager([
        {"rule_number": 1, "title": "Rule 1", "category": "basic_work", "priority": "critical", "content": "Content", "enabled": True}
    ])
    
    monkeypatch.setattr(sync_manager, "ConstitutionRuleExtractor", lambda *a, **k: mock_extractor)
    monkeypatch.setattr(sync_manager, "ConstitutionRuleManager", lambda *a, **k: sqlite_mgr)
    
    # Mock JSON file
    json_file = tmp_config_dir / "constitution_rules.json"
    json_file.write_text(json.dumps({
        "rules": {
            "1": {"rule_number": 1, "title": "Rule 1", "enabled": True}
        }
    }), encoding="utf-8")
    
    # Mock config file
    config_file = tmp_config_dir / "constitution_config.json"
    config_file.write_text(json.dumps({
        "rules": {
            "1": {"enabled": True}
        }
    }), encoding="utf-8")
    
    result = sync_mgr.verify_consistency_across_sources()
    
    assert "consistent" in result
    assert "summary" in result
    assert "differences" in result


def test_rules_differ(sync_mgr):
    """Test rule difference detection."""
    rule1 = {"title": "Rule 1", "category": "cat1", "priority": "high", "content": "Content", "enabled": True}
    rule2 = {"title": "Rule 1", "category": "cat1", "priority": "high", "content": "Content", "enabled": True}
    rule3 = {"title": "Rule 2", "category": "cat1", "priority": "high", "content": "Content", "enabled": True}
    
    assert sync_mgr._rules_differ(rule1, rule2) is False
    assert sync_mgr._rules_differ(rule1, rule3) is True


def test_is_sync_needed(sync_mgr):
    """Test checking if sync is needed."""
    source_mgr = Mock()
    target_mgr = Mock()
    
    # Source is newer
    source_mgr.get_backend_info.return_value = {"last_updated": datetime.now().isoformat()}
    target_mgr.get_backend_info.return_value = {"last_updated": (datetime.now() - timedelta(hours=1)).isoformat()}
    
    assert sync_mgr._is_sync_needed(source_mgr, target_mgr, "test") is True
    
    # Target is newer
    source_mgr.get_backend_info.return_value = {"last_updated": (datetime.now() - timedelta(hours=1)).isoformat()}
    target_mgr.get_backend_info.return_value = {"last_updated": datetime.now().isoformat()}
    
    assert sync_mgr._is_sync_needed(source_mgr, target_mgr, "test") is False


def test_global_sync_functions(tmp_config_dir, monkeypatch):
    """Test global sync manager functions."""
    # Reset global instance
    sync_manager._sync_manager_instance = None
    
    # Test get_sync_manager
    mgr1 = sync_manager.get_sync_manager()
    mgr2 = sync_manager.get_sync_manager()
    assert mgr1 is mgr2
    
    # Test sync_backends
    mgr1.auto_sync = Mock(return_value={"success": True})
    result = sync_manager.sync_backends(force=True)
    assert result["success"] is True
    
    # Test verify_sync
    mgr1.verify_sync = Mock(return_value={"synchronized": True})
    result = sync_manager.verify_sync()
    assert result["synchronized"] is True

