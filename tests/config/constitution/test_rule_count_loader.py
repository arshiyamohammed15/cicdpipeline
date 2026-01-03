from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from config.constitution import rule_count_loader


@pytest.fixture
def tmp_constitution_dir(tmp_path):
    """Create temporary constitution directory with JSON files."""
    constitution_dir = tmp_path / "constitution"
    constitution_dir.mkdir()
    
    # Create sample JSON files
    file1 = constitution_dir / "basic_work.json"
    file1.write_text(json.dumps({
        "constitution_rules": [
            {"rule_number": 1, "title": "Rule 1", "category": "basic_work", "enabled": True},
            {"rule_number": 2, "title": "Rule 2", "category": "basic_work", "enabled": True}
        ]
    }), encoding="utf-8")
    
    file2 = constitution_dir / "system_design.json"
    file2.write_text(json.dumps({
        "constitution_rules": [
            {"rule_number": 3, "title": "Rule 3", "category": "system_design", "enabled": False}
        ]
    }), encoding="utf-8")
    
    return constitution_dir


@pytest.fixture
def loader(tmp_constitution_dir):
    """Create rule count loader."""
    return rule_count_loader.RuleCountLoader(constitution_dir=str(tmp_constitution_dir))


def test_loader_initialization(loader, tmp_constitution_dir):
    """Test loader initialization."""
    assert loader.constitution_dir == tmp_constitution_dir.resolve()
    assert loader._cache_valid is False


def test_load_rules_from_json_files(loader):
    """Test loading rules from JSON files."""
    total, enabled, disabled, categories = loader._load_rules_from_json_files()
    
    assert total == 3
    assert enabled == 2
    assert disabled == 1
    assert "basic_work" in categories
    assert "system_design" in categories
    assert categories["basic_work"] == 2
    assert categories["system_design"] == 1


def test_load_rules_from_json_files_not_found(tmp_path):
    """Test loading when directory doesn't exist."""
    loader = rule_count_loader.RuleCountLoader(constitution_dir=str(tmp_path / "nonexistent"))
    
    with pytest.raises(FileNotFoundError):
        loader._load_rules_from_json_files()


def test_load_rules_from_json_files_no_files(tmp_path):
    """Test loading when no JSON files exist."""
    constitution_dir = tmp_path / "constitution"
    constitution_dir.mkdir()
    
    loader = rule_count_loader.RuleCountLoader(constitution_dir=str(constitution_dir))
    
    with pytest.raises(FileNotFoundError):
        loader._load_rules_from_json_files()


def test_get_counts(loader):
    """Test getting counts."""
    counts = loader.get_counts()
    
    assert "total_rules" in counts
    assert "enabled_rules" in counts
    assert "disabled_rules" in counts
    assert "category_counts" in counts
    assert counts["total_rules"] == 3  # All rules including disabled
    assert counts["enabled_rules"] == 2
    assert counts["disabled_rules"] == 1


def test_get_counts_cached(loader):
    """Test that counts are cached."""
    counts1 = loader.get_counts()
    counts2 = loader.get_counts()
    
    # Should return same object (cached)
    assert counts1 is counts2


def test_get_counts_force_reload(loader):
    """Test forcing reload of counts."""
    counts1 = loader.get_counts()
    loader._cache_valid = True
    
    counts2 = loader.get_counts(force_reload=True)
    
    # Should reload
    assert loader._cache_valid is True


def test_get_total_rules(loader):
    """Test getting total rule count."""
    total = loader.get_total_rules()
    assert total == 3  # Total rules including disabled


def test_get_enabled_rules(loader):
    """Test getting enabled rule count."""
    enabled = loader.get_enabled_rules()
    assert enabled == 2


def test_get_disabled_rules(loader):
    """Test getting disabled rule count."""
    disabled = loader.get_disabled_rules()
    assert disabled == 1


def test_get_category_counts(loader):
    """Test getting category counts."""
    categories = loader.get_category_counts()
    
    assert isinstance(categories, dict)
    assert "basic_work" in categories
    assert "system_design" in categories
    assert categories["basic_work"] == 2


def test_invalidate_cache(loader):
    """Test invalidating cache."""
    loader.get_counts()  # Populate cache
    assert loader._cache_valid is True
    
    loader.invalidate_cache()
    assert loader._cache_valid is False


def test_global_get_rule_count_loader(tmp_constitution_dir):
    """Test global get_rule_count_loader function."""
    # Reset global instance
    rule_count_loader._rule_count_loader = None
    
    loader1 = rule_count_loader.get_rule_count_loader(str(tmp_constitution_dir))
    loader2 = rule_count_loader.get_rule_count_loader(str(tmp_constitution_dir))
    
    # Should return same instance
    assert loader1 is loader2


def test_global_get_rule_counts(tmp_constitution_dir):
    """Test global get_rule_counts function."""
    counts = rule_count_loader.get_rule_counts(str(tmp_constitution_dir))
    
    assert "total_rules" in counts
    assert "enabled_rules" in counts
    assert "disabled_rules" in counts
    assert "category_counts" in counts


def test_load_rules_with_invalid_json(tmp_path):
    """Test loading rules with invalid JSON file."""
    constitution_dir = tmp_path / "constitution"
    constitution_dir.mkdir()
    
    # Create valid file
    valid_file = constitution_dir / "valid.json"
    valid_file.write_text(json.dumps({
        "constitution_rules": [
            {"rule_number": 1, "enabled": True, "category": "test"}
        ]
    }), encoding="utf-8")
    
    # Create invalid file
    invalid_file = constitution_dir / "invalid.json"
    invalid_file.write_text("invalid json{", encoding="utf-8")
    
    loader = rule_count_loader.RuleCountLoader(constitution_dir=str(constitution_dir))
    
    # Should skip invalid file and load valid one
    total, enabled, disabled, categories = loader._load_rules_from_json_files()
    assert total == 1
    assert enabled == 1


def test_load_rules_with_missing_category(tmp_path):
    """Test loading rules with missing category."""
    constitution_dir = tmp_path / "constitution"
    constitution_dir.mkdir()
    
    file1 = constitution_dir / "test.json"
    file1.write_text(json.dumps({
        "constitution_rules": [
            {"rule_number": 1, "enabled": True}  # No category
        ]
    }), encoding="utf-8")
    
    loader = rule_count_loader.RuleCountLoader(constitution_dir=str(constitution_dir))
    
    total, enabled, disabled, categories = loader._load_rules_from_json_files()
    
    assert total == 1
    assert "UNKNOWN" in categories or len(categories) == 0

