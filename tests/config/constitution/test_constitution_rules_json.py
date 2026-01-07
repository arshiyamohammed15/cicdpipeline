from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from config.constitution import constitution_rules_json


@pytest.fixture
def tmp_json_path(tmp_path):
    """Create temporary JSON database path."""
    return tmp_path / "test_rules.json"


@pytest.fixture
def sample_rules_data():
    """Sample rules data for testing."""
    return {
        "rules": {
            "1": {
                "rule_number": 1,
                "title": "Rule 1",
                "category": "basic_work",
                "priority": "critical",
                "content": "Content 1",
                "enabled": True,
                "config": {"default_enabled": True},
                "metadata": {"created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00", "usage_count": 0, "last_used": None}
            },
            "2": {
                "rule_number": 2,
                "title": "Rule 2",
                "category": "system_design",
                "priority": "critical",
                "content": "Content 2",
                "enabled": False,
                "config": {"default_enabled": True, "disabled_reason": "Test"},
                "metadata": {"created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00", "usage_count": 0, "last_used": None}
            }
        },
        "database_info": {
            "version": "2.0",
            "last_updated": "2024-01-01T00:00:00",
            "total_rules": 2
        },
        "categories": {
            "basic_work": {"count": 1},
            "system_design": {"count": 1}
        },
        "constitution_version": "2.0",
        "total_rules": 2,
        "statistics": {
            "total_rules": 2,
            "enabled_rules": 1,
            "disabled_rules": 1
        },
        "usage_history": [],
        "validation_history": []
    }


@pytest.fixture
def json_manager(tmp_json_path, sample_rules_data, monkeypatch):
    """Create JSON manager with sample data."""
    # Mock rule count loader to match the sample data (2 rules)
    def mock_get_rule_count_loader():
        mock_loader = Mock()
        mock_loader.get_total_rules.return_value = 2
        return mock_loader
    
    monkeypatch.setattr(constitution_rules_json, "get_rule_count_loader", mock_get_rule_count_loader)
    
    # Write sample data to file
    tmp_json_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_json_path.write_text(json.dumps(sample_rules_data), encoding="utf-8")
    
    manager = constitution_rules_json.ConstitutionRulesJSON(json_path=str(tmp_json_path))
    manager._initialized = True
    manager.data = sample_rules_data
    return manager


@pytest.mark.constitution
def test_json_manager_initialization(tmp_json_path):
    """Test JSON manager initialization."""
    manager = constitution_rules_json.ConstitutionRulesJSON(json_path=str(tmp_json_path))
    assert manager.json_path == tmp_json_path
    assert manager._initialized is False


@pytest.mark.constitution
def test_init_database_new_file(tmp_json_path, monkeypatch):
    """Test initializing database with new file."""
    # Mock rule count loader to return the current total from the source of truth
    loader = constitution_rules_json.get_rule_count_loader()
    loader.invalidate_cache()
    actual_total_rules = loader.get_total_rules()

    def mock_get_rule_count_loader():
        mock_loader = Mock()
        mock_loader.get_total_rules.return_value = actual_total_rules
        return mock_loader
    
    monkeypatch.setattr(constitution_rules_json, "get_rule_count_loader", mock_get_rule_count_loader)
    
    manager = constitution_rules_json.ConstitutionRulesJSON(json_path=str(tmp_json_path))
    manager._init_database()
    
    assert manager._initialized is True
    assert tmp_json_path.exists()
    
    # Check structure
    data = json.loads(tmp_json_path.read_text(encoding="utf-8"))
    assert "rules" in data
    assert "database_info" in data


@pytest.mark.constitution
def test_init_database_existing_file(tmp_json_path, sample_rules_data, monkeypatch):
    """Test initializing database with existing file."""
    # Mock rule count loader to match the sample data (2 rules)
    def mock_get_rule_count_loader():
        mock_loader = Mock()
        mock_loader.get_total_rules.return_value = 2
        return mock_loader
    
    monkeypatch.setattr(constitution_rules_json, "get_rule_count_loader", mock_get_rule_count_loader)
    
    tmp_json_path.write_text(json.dumps(sample_rules_data), encoding="utf-8")
    
    manager = constitution_rules_json.ConstitutionRulesJSON(json_path=str(tmp_json_path))
    manager._init_database()
    
    assert manager._initialized is True
    assert manager.data["rules"]["1"]["title"] == "Rule 1"


@pytest.mark.constitution
def test_load_database(tmp_json_path, sample_rules_data, monkeypatch):
    """Test loading database from file."""
    # Mock rule count loader to match the sample data (2 rules)
    def mock_get_rule_count_loader():
        mock_loader = Mock()
        mock_loader.get_total_rules.return_value = 2
        return mock_loader
    
    monkeypatch.setattr(constitution_rules_json, "get_rule_count_loader", mock_get_rule_count_loader)
    
    tmp_json_path.write_text(json.dumps(sample_rules_data), encoding="utf-8")
    
    manager = constitution_rules_json.ConstitutionRulesJSON(json_path=str(tmp_json_path))
    manager._load_database()
    
    assert "rules" in manager.data
    assert "1" in manager.data["rules"]


@pytest.mark.constitution
def test_load_database_corrupted_file(tmp_json_path, monkeypatch):
    """Test loading corrupted database file."""
    loader = constitution_rules_json.get_rule_count_loader()
    loader.invalidate_cache()
    actual_total_rules = loader.get_total_rules()

    def mock_get_rule_count_loader():
        mock_loader = Mock()
        mock_loader.get_total_rules.return_value = actual_total_rules
        return mock_loader
    
    monkeypatch.setattr(constitution_rules_json, "get_rule_count_loader", mock_get_rule_count_loader)
    
    tmp_json_path.write_text("invalid json{", encoding="utf-8")
    
    manager = constitution_rules_json.ConstitutionRulesJSON(json_path=str(tmp_json_path))
    
    # Should create backup and recreate database
    manager._load_database()
    assert manager._initialized is False  # Will be set by _init_database


@pytest.mark.constitution
def test_save_database(json_manager, tmp_json_path):
    """Test saving database to file."""
    # Modify data
    json_manager.data["rules"]["1"]["title"] = "Updated Rule 1"
    
    json_manager._save_database()
    
    # Verify file was updated
    data = json.loads(tmp_json_path.read_text(encoding="utf-8"))
    assert data["rules"]["1"]["title"] == "Updated Rule 1"


@pytest.mark.constitution
def test_get_rule_by_number(json_manager):
    """Test getting rule by number."""
    rule = json_manager.get_rule_by_number(1)
    assert rule is not None
    assert rule["rule_number"] == 1
    assert rule["title"] == "Rule 1"


@pytest.mark.constitution
def test_get_rule_by_number_not_found(json_manager):
    """Test getting non-existent rule."""
    rule = json_manager.get_rule_by_number(999)
    assert rule is None


@pytest.mark.constitution
def test_get_rules_by_category(json_manager):
    """Test getting rules by category."""
    rules = json_manager.get_rules_by_category("basic_work")
    assert len(rules) == 1
    assert rules[0]["rule_number"] == 1


@pytest.mark.constitution
def test_get_rules_by_category_enabled_only(json_manager):
    """Test getting enabled rules by category."""
    rules = json_manager.get_rules_by_category("basic_work", enabled_only=True)
    assert len(rules) == 1
    assert all(r["enabled"] for r in rules)


@pytest.mark.constitution
def test_enable_rule(json_manager, tmp_json_path):
    """Test enabling a rule."""
    result = json_manager.enable_rule(2, {"test": "config"})
    
    assert result is True
    assert json_manager.data["rules"]["2"]["enabled"] is True
    
    # Verify saved
    data = json.loads(tmp_json_path.read_text(encoding="utf-8"))
    assert data["rules"]["2"]["enabled"] is True


@pytest.mark.constitution
def test_enable_rule_not_found(json_manager):
    """Test enabling non-existent rule."""
    result = json_manager.enable_rule(999)
    assert result is False


@pytest.mark.constitution
def test_disable_rule(json_manager, tmp_json_path):
    """Test disabling a rule."""
    result = json_manager.disable_rule(1, "Test reason")
    
    assert result is True
    assert json_manager.data["rules"]["1"]["enabled"] is False
    
    # Verify saved
    data = json.loads(tmp_json_path.read_text(encoding="utf-8"))
    assert data["rules"]["1"]["enabled"] is False


@pytest.mark.constitution
def test_disable_rule_not_found(json_manager):
    """Test disabling non-existent rule."""
    result = json_manager.disable_rule(999, "reason")
    assert result is False


@pytest.mark.constitution
def test_get_all_rules(json_manager):
    """Test getting all rules."""
    all_rules = json_manager.get_all_rules()
    assert len(all_rules) == 2


@pytest.mark.constitution
def test_get_all_rules_enabled_only(json_manager):
    """Test getting only enabled rules."""
    enabled_rules = json_manager.get_all_rules(enabled_only=True)
    assert len(enabled_rules) == 1
    assert all(r["enabled"] for r in enabled_rules)


@pytest.mark.constitution
def test_get_enabled_rules(json_manager):
    """Test getting enabled rules."""
    enabled = json_manager.get_enabled_rules()
    assert len(enabled) == 1
    assert enabled[0]["rule_number"] == 1


@pytest.mark.constitution
def test_get_disabled_rules(json_manager):
    """Test getting disabled rules."""
    disabled = json_manager.get_disabled_rules()
    assert len(disabled) == 1
    assert disabled[0]["rule_number"] == 2


@pytest.mark.constitution
def test_get_rule_statistics(json_manager):
    """Test getting rule statistics."""
    stats = json_manager.get_rule_statistics()
    assert stats["total_rules"] == 2
    assert stats["enabled_rules"] == 1
    assert stats["disabled_rules"] == 1


@pytest.mark.constitution
def test_search_rules(json_manager):
    """Test searching rules."""
    results = json_manager.search_rules("Rule 1")
    assert len(results) == 1
    assert results[0]["rule_number"] == 1


@pytest.mark.constitution
def test_search_rules_enabled_only(json_manager):
    """Test searching only enabled rules."""
    results = json_manager.search_rules("Rule", enabled_only=True)
    assert len(results) == 1
    assert results[0]["enabled"] is True


@pytest.mark.constitution
def test_get_categories(json_manager):
    """Test getting all categories."""
    categories = json_manager.get_categories()
    assert "basic_work" in categories
    assert "system_design" in categories


@pytest.mark.constitution
def test_get_category_statistics(json_manager):
    """Test getting category statistics."""
    stats = json_manager.get_category_statistics()
    assert "basic_work" in stats
    assert stats["basic_work"]["count"] == 1


@pytest.mark.constitution
def test_export_rules_to_json(json_manager):
    """Test exporting rules to JSON."""
    json_data = json_manager.export_rules_to_json()
    assert isinstance(json_data, str)
    
    parsed = json.loads(json_data)
    assert isinstance(parsed, list)
    assert len(parsed) == 2


@pytest.mark.constitution
def test_export_rules_to_json_enabled_only(json_manager):
    """Test exporting only enabled rules."""
    json_data = json_manager.export_rules_to_json(enabled_only=True)
    parsed = json.loads(json_data)
    assert all(r["enabled"] for r in parsed)


@pytest.mark.constitution
def test_import_rules_from_json(json_manager, tmp_json_path, monkeypatch):
    """Test importing rules from JSON."""
    # Mock rule count loader to match the new count after import (3 rules)
    def mock_get_rule_count_loader():
        mock_loader = Mock()
        mock_loader.get_total_rules.return_value = 3
        return mock_loader
    
    monkeypatch.setattr(constitution_rules_json, "get_rule_count_loader", mock_get_rule_count_loader)
    
    new_rules = [
        {
            "rule_number": 3,
            "title": "Rule 3",
            "category": "problem_solving",
            "priority": "critical",
            "content": "Content 3",
            "enabled": True
        }
    ]
    json_data = json.dumps(new_rules)
    
    result = json_manager.import_rules_from_json(json_data)
    assert result is True
    
    # Verify rule was added
    rule = json_manager.get_rule_by_number(3)
    assert rule is not None
    assert rule["title"] == "Rule 3"


@pytest.mark.constitution
def test_log_usage(json_manager):
    """Test logging rule usage."""
    json_manager._log_usage(1, "enabled", "Test context")
    # Just verify it doesn't raise an exception


@pytest.mark.constitution
def test_update_statistics(json_manager):
    """Test updating statistics."""
    json_manager._update_statistics()
    
    stats = json_manager.data["statistics"]
    assert stats["total_rules"] == 2
    assert stats["enabled_rules"] == 1


@pytest.mark.constitution
def test_validate_database_structure(json_manager):
    """Test validating database structure."""
    # Should not raise for valid structure
    json_manager._validate_database_structure()


@pytest.mark.constitution
def test_validate_database_structure_invalid(json_manager):
    """Test validating invalid database structure."""
    json_manager.data = {"invalid": "structure"}
    
    with pytest.raises(ValueError):
        json_manager._validate_database_structure()


@pytest.mark.constitution
def test_repair_corrupted_database(tmp_json_path, sample_rules_data, monkeypatch):
    """Test repairing corrupted database."""
    # Mock rule count loader to match the sample data (2 rules)
    def mock_get_rule_count_loader():
        mock_loader = Mock()
        mock_loader.get_total_rules.return_value = 2
        return mock_loader
    
    monkeypatch.setattr(constitution_rules_json, "get_rule_count_loader", mock_get_rule_count_loader)
    
    # Create valid file first
    tmp_json_path.write_text(json.dumps(sample_rules_data), encoding="utf-8")
    
    manager = constitution_rules_json.ConstitutionRulesJSON(json_path=str(tmp_json_path))
    result = manager.repair_corrupted_database()
    assert result is True


@pytest.mark.constitution
def test_repair_corrupted_database_corrupted(tmp_json_path, monkeypatch):
    """Test repairing actually corrupted database."""
    loader = constitution_rules_json.get_rule_count_loader()
    loader.invalidate_cache()
    actual_total_rules = loader.get_total_rules()

    def mock_get_rule_count_loader():
        mock_loader = Mock()
        mock_loader.get_total_rules.return_value = actual_total_rules
        return mock_loader
    
    monkeypatch.setattr(constitution_rules_json, "get_rule_count_loader", mock_get_rule_count_loader)
    
    tmp_json_path.write_text("invalid json{", encoding="utf-8")
    
    manager = constitution_rules_json.ConstitutionRulesJSON(json_path=str(tmp_json_path))
    result = manager.repair_corrupted_database()
    assert result is True  # Should recreate database


@pytest.mark.constitution
def test_backup_database(json_manager, tmp_path):
    """Test backing up database."""
    backup_path = tmp_path / "backup.json"
    result = json_manager.backup_database(str(backup_path))
    
    assert result is True
    assert backup_path.exists()
    
    # Verify backup content
    backup_data = json.loads(backup_path.read_text(encoding="utf-8"))
    assert "rules" in backup_data


@pytest.mark.constitution
def test_restore_database(json_manager, tmp_path):
    """Test restoring database from backup."""
    # Create backup
    backup_path = tmp_path / "backup.json"
    backup_data = json_manager.data.copy()
    backup_path.write_text(json.dumps(backup_data), encoding="utf-8")
    
    # Modify original
    json_manager.data["rules"]["1"]["title"] = "Modified"
    
    # Restore
    result = json_manager.restore_database(str(backup_path))
    assert result is True
    
    # Verify restored
    assert json_manager.data["rules"]["1"]["title"] == "Rule 1"


@pytest.mark.constitution
def test_get_expected_rule_count(json_manager, monkeypatch):
    """Test getting expected rule count from loader."""
    mock_loader = Mock()
    mock_loader.get_total_rules.return_value = 150
    
    with patch('config.constitution.constitution_rules_json.get_rule_count_loader', return_value=mock_loader):
        count = json_manager._get_expected_rule_count()
        assert count == 150


@pytest.mark.constitution
def test_get_expected_rule_count_fallback(json_manager):
    """Test fallback when loader fails."""
    # Remove rules to test fallback
    json_manager.data = {"rules": {"1": {}, "2": {}}}
    
    with patch('config.constitution.constitution_rules_json.get_rule_count_loader', side_effect=Exception()):
        count = json_manager._get_expected_rule_count()
        assert count == 2


@pytest.mark.constitution
def test_validate_data_before_save(json_manager):
    """Test validating data before save."""
    # Should not raise for valid data
    json_manager._validate_data_before_save()


@pytest.mark.constitution
def test_validate_data_before_save_invalid(json_manager):
    """Test validating invalid data before save."""
    json_manager.data = "not a dict"
    
    with pytest.raises(ValueError, match="Data must be a dictionary"):
        json_manager._validate_data_before_save()


@pytest.mark.constitution
def test_validate_data_before_save_missing_keys(json_manager):
    """Test validating data with missing keys."""
    json_manager.data = {"rules": {}}
    
    with pytest.raises(ValueError, match="Missing required key"):
        json_manager._validate_data_before_save()


@pytest.mark.constitution
def test_validate_json_file(tmp_json_path):
    """Test validating JSON file."""
    tmp_json_path.write_text(json.dumps({"valid": "json"}), encoding="utf-8")
    
    manager = constitution_rules_json.ConstitutionRulesJSON(json_path=str(tmp_json_path))
    manager._validate_json_file(tmp_json_path)
    # Should not raise


@pytest.mark.constitution
def test_validate_json_file_invalid(tmp_json_path):
    """Test validating invalid JSON file."""
    tmp_json_path.write_text("invalid json{", encoding="utf-8")
    
    manager = constitution_rules_json.ConstitutionRulesJSON(json_path=str(tmp_json_path))
    
    with pytest.raises(ValueError, match="Generated JSON file is invalid"):
        manager._validate_json_file(tmp_json_path)

