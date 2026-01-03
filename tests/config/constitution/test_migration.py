from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from config.constitution import migration


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def migration_instance(tmp_config_dir):
    """Create migration instance."""
    return migration.ConstitutionMigration(config_dir=str(tmp_config_dir))


def test_migration_initialization(migration_instance, tmp_config_dir):
    """Test migration initialization."""
    assert migration_instance.config_dir == str(tmp_config_dir)
    assert migration_instance.migration_history_path == tmp_config_dir / "migration_history.json"


def test_load_migration_history_existing(migration_instance, tmp_config_dir):
    """Test loading existing migration history."""
    history = [{"timestamp": "2024-01-01T00:00:00", "migration_type": "test"}]
    migration_instance.migration_history_path.write_text(json.dumps(history), encoding="utf-8")
    
    migration_instance._load_migration_history()
    assert len(migration_instance._migration_history) == 1


def test_load_migration_history_corrupted(migration_instance, tmp_config_dir):
    """Test loading corrupted migration history."""
    migration_instance.migration_history_path.write_text("invalid json{", encoding="utf-8")
    
    migration_instance._load_migration_history()
    assert isinstance(migration_instance._migration_history, list)


def test_log_migration(migration_instance):
    """Test logging migration operation."""
    migration_instance._log_migration("test", "source", "target", True, "details")
    
    assert len(migration_instance._migration_history) == 1
    assert migration_instance._migration_history[0]["migration_type"] == "test"


def test_log_migration_history_limit(migration_instance):
    """Test that migration history is limited."""
    for i in range(60):
        migration_instance._log_migration("test", "src", "tgt", True, str(i))
    
    assert len(migration_instance._migration_history) == 50


def test_migrate_sqlite_to_json(migration_instance, tmp_config_dir, monkeypatch):
    """Test migrating from SQLite to JSON."""
    # Mock managers
    sqlite_mgr = Mock()
    sqlite_mgr.get_all_rules.return_value = [
        {"rule_number": 1, "title": "Rule 1", "category": "basic_work",
         "priority": "critical", "content": "Content", "enabled": True}
    ]
    sqlite_mgr.get_rule_statistics.return_value = {"total_rules": 1}
    sqlite_mgr.close = Mock()
    
    json_mgr = Mock()
    json_mgr.json_manager = Mock()
    json_mgr.json_manager.data = {"rules": {}}
    json_mgr.json_manager._create_database = Mock()
    json_mgr.json_manager._update_statistics = Mock()
    json_mgr.json_manager._save_database = Mock()
    json_mgr.get_all_rules.return_value = [
        {"rule_number": 1, "title": "Rule 1", "category": "basic_work",
         "priority": "critical", "content": "Content", "enabled": True}
    ]
    json_mgr._sync_with_database = Mock()
    json_mgr.close = Mock()
    
    monkeypatch.setattr(migration, "ConstitutionRuleManager", lambda *a, **k: sqlite_mgr)
    monkeypatch.setattr(migration, "ConstitutionRuleManagerJSON", lambda *a, **k: json_mgr)
    
    result = migration_instance.migrate_sqlite_to_json(create_backup=True)
    
    assert result["success"] is True
    assert "rules_migrated" in result


def test_migrate_json_to_sqlite(migration_instance, tmp_config_dir, monkeypatch):
    """Test migrating from JSON to SQLite."""
    # Mock managers
    json_mgr = Mock()
    json_mgr.get_all_rules.return_value = [
        {"rule_number": 1, "title": "Rule 1", "category": "basic_work",
         "priority": "critical", "content": "Content", "enabled": True}
    ]
    json_mgr.get_rule_statistics.return_value = {"total_rules": 1}
    json_mgr.close = Mock()
    
    sqlite_mgr = Mock()
    sqlite_mgr.db_manager = Mock()
    sqlite_mgr.db_manager._init_database = Mock()
    sqlite_mgr.db_manager.insert_rule = Mock()
    sqlite_mgr.get_all_rules.return_value = [
        {"rule_number": 1, "title": "Rule 1", "category": "basic_work",
         "priority": "critical", "content": "Content", "enabled": True}
    ]
    sqlite_mgr.close = Mock()
    
    monkeypatch.setattr(migration, "ConstitutionRuleManagerJSON", lambda *a, **k: json_mgr)
    monkeypatch.setattr(migration, "ConstitutionRuleManager", lambda *a, **k: sqlite_mgr)
    
    result = migration_instance.migrate_json_to_sqlite(create_backup=True)
    
    assert result["success"] is True
    assert "rules_migrated" in result


def test_verify_migration_success(migration_instance):
    """Test verifying successful migration."""
    source_rules = [
        {"rule_number": 1, "title": "Rule 1", "category": "cat1", "priority": "high", "content": "Content", "enabled": True}
    ]
    target_rules = [
        {"rule_number": 1, "title": "Rule 1", "category": "cat1", "priority": "high", "content": "Content", "enabled": True}
    ]
    
    result = migration_instance._verify_migration(source_rules, target_rules)
    
    assert result["success"] is True
    assert result["source_count"] == 1
    assert result["target_count"] == 1


def test_verify_migration_count_mismatch(migration_instance):
    """Test verifying migration with count mismatch."""
    source_rules = [
        {"rule_number": 1, "title": "Rule 1", "category": "cat1", "priority": "high", "content": "Content", "enabled": True}
    ]
    target_rules = [
        {"rule_number": 1, "title": "Rule 1", "category": "cat1", "priority": "high", "content": "Content", "enabled": True},
        {"rule_number": 2, "title": "Rule 2", "category": "cat1", "priority": "high", "content": "Content", "enabled": True}
    ]
    
    result = migration_instance._verify_migration(source_rules, target_rules)
    
    assert result["success"] is False
    assert "error" in result


def test_verify_migration_different_rules(migration_instance):
    """Test verifying migration with different rule data."""
    source_rules = [
        {"rule_number": 1, "title": "Rule 1", "category": "cat1", "priority": "high", "content": "Content", "enabled": True}
    ]
    target_rules = [
        {"rule_number": 1, "title": "Rule 1 Modified", "category": "cat1", "priority": "high", "content": "Content", "enabled": True}
    ]
    
    result = migration_instance._verify_migration(source_rules, target_rules)
    
    assert result["success"] is False
    assert len(result["different_rules"]) > 0


def test_create_backup_sqlite(migration_instance, tmp_config_dir):
    """Test creating SQLite backup."""
    # Create source file
    source_file = tmp_config_dir / "constitution_rules.db"
    source_file.write_bytes(b"fake db content")
    
    backup_path = migration_instance._create_backup("sqlite", "test")
    
    assert backup_path is not None
    assert Path(backup_path).exists()


def test_create_backup_json(migration_instance, tmp_config_dir):
    """Test creating JSON backup."""
    # Create source file
    source_file = tmp_config_dir / "constitution_rules.json"
    source_file.write_text(json.dumps({"rules": {}}), encoding="utf-8")
    
    backup_path = migration_instance._create_backup("json", "test")
    
    assert backup_path is not None
    assert Path(backup_path).exists()


def test_create_backup_file_not_exists(migration_instance, tmp_config_dir):
    """Test creating backup when source file doesn't exist."""
    backup_path = migration_instance._create_backup("sqlite", "test")
    
    assert backup_path is None


def test_restore_from_backup(migration_instance, tmp_config_dir, monkeypatch):
    """Test restoring from backup."""
    # Create backup file
    backup_file = tmp_config_dir / "backup.db"
    backup_file.write_bytes(b"backup content")
    
    # Mock manager
    mock_manager = Mock()
    mock_manager.health_check.return_value = {"healthy": True}
    mock_manager.close = Mock()
    
    monkeypatch.setattr(migration, "ConstitutionRuleManager", lambda *a, **k: mock_manager)
    
    result = migration_instance.restore_from_backup(str(backup_file), "sqlite")
    
    assert result["success"] is True
    assert "backup_path" in result


def test_restore_from_backup_not_found(migration_instance, tmp_config_dir):
    """Test restoring from non-existent backup."""
    result = migration_instance.restore_from_backup("nonexistent.db", "sqlite")
    
    assert result["success"] is False
    assert "error" in result


def test_repair_sync(migration_instance, monkeypatch):
    """Test repairing sync."""
    # Mock sync manager
    mock_sync_mgr = Mock()
    mock_sync_mgr._detect_conflicts.return_value = []
    mock_sync_mgr._resolve_conflicts.return_value = {"resolved": 0, "failed": 0}
    mock_sync_mgr.verify_sync.return_value = {"synchronized": True}
    
    monkeypatch.setattr(migration, "get_sync_manager", lambda: mock_sync_mgr)
    # Patch get_backend_factory at the module level
    from config.constitution import backend_factory
    mock_factory = Mock()
    mock_factory._get_configuration.return_value = {"backend": "sqlite", "primary_backend": "sqlite"}
    monkeypatch.setattr(backend_factory, "get_backend_factory", lambda: mock_factory)
    
    result = migration_instance.repair_sync()
    
    assert result["success"] is True
    assert "conflicts_found" in result


def test_get_migration_history(migration_instance):
    """Test getting migration history."""
    migration_instance._log_migration("test1", "src", "tgt", True)
    migration_instance._log_migration("test2", "src", "tgt", True)
    
    history = migration_instance.get_migration_history(limit=1)
    assert len(history) == 1
    
    history_all = migration_instance.get_migration_history(limit=0)
    assert len(history_all) == 2


def test_clear_migration_history(migration_instance):
    """Test clearing migration history."""
    migration_instance._log_migration("test", "src", "tgt", True)
    assert len(migration_instance._migration_history) > 0
    
    migration_instance.clear_migration_history()
    assert len(migration_instance._migration_history) == 0


def test_global_functions(tmp_config_dir, monkeypatch):
    """Test global migration functions."""
    # Reset global instance
    migration._migration_instance = None
    
    # Test get_migration_manager
    mgr1 = migration.get_migration_manager()
    mgr2 = migration.get_migration_manager()
    assert mgr1 is mgr2
    
    # Test migrate_sqlite_to_json
    mgr1.migrate_sqlite_to_json = Mock(return_value={"success": True})
    result = migration.migrate_sqlite_to_json(create_backup=False)
    assert result["success"] is True
    
    # Test migrate_json_to_sqlite
    mgr1.migrate_json_to_sqlite = Mock(return_value={"success": True})
    result = migration.migrate_json_to_sqlite(create_backup=False)
    assert result["success"] is True
    
    # Test repair_sync
    mgr1.repair_sync = Mock(return_value={"success": True})
    result = migration.repair_sync()
    assert result["success"] is True

