from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from config.constitution import config_migration


@pytest.fixture
def tmp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def migration(tmp_config_dir):
    """Create migration instance."""
    return config_migration.ConfigMigration(config_dir=str(tmp_config_dir))


def test_migration_initialization(migration, tmp_config_dir):
    """Test migration initialization."""
    assert migration.config_dir == tmp_config_dir
    assert migration.config_path == tmp_config_dir / "constitution_config.json"
    assert migration.backup_dir == tmp_config_dir / "backups"


def test_migrate_v1_to_v2_no_file(migration):
    """Test migration when no config file exists."""
    result = migration.migrate_v1_to_v2()
    assert result is False


def test_migrate_v1_to_v2_already_v2(migration, tmp_config_dir):
    """Test migration when already v2.0."""
    v2_config = {"version": "2.0", "primary_backend": "sqlite"}
    migration.config_path.write_text(json.dumps(v2_config), encoding="utf-8")
    
    result = migration.migrate_v1_to_v2()
    assert result is True


def test_migrate_v1_to_v2_success(migration, tmp_config_dir):
    """Test successful migration from v1.0 to v2.0."""
    v1_config = {
        "version": "1.0",
        "backend": "sqlite",
        "backends": {
            "sqlite": {"path": "config/constitution_rules.db", "primary": True},
            "json": {"path": "config/constitution_rules.json"}
        },
        "auto_fallback": True,
        "fallback_backend": "json",
        "auto_sync": True,
        "sync_interval": 60,
        "rules": {"1": {"enabled": True}},
        "constitution_version": "2.0",
        "total_rules": 149,
        "default_enabled": True
    }
    migration.config_path.write_text(json.dumps(v1_config), encoding="utf-8")
    
    result = migration.migrate_v1_to_v2(create_backup=True)
    assert result is True
    
    # Verify migrated config
    migrated = json.loads(migration.config_path.read_text(encoding="utf-8"))
    assert migrated["version"] == "2.0"
    assert migrated["primary_backend"] == "sqlite"
    assert "backend_config" in migrated
    assert "fallback" in migrated
    assert "sync" in migrated
    assert migrated["rules"] == v1_config["rules"]


def test_migrate_v1_to_v2_with_backup(migration, tmp_config_dir):
    """Test migration creates backup."""
    v1_config = {"version": "1.0", "backend": "sqlite"}
    migration.config_path.write_text(json.dumps(v1_config), encoding="utf-8")
    
    result = migration.migrate_v1_to_v2(create_backup=True)
    assert result is True
    
    # Check backup was created
    backups = list(migration.backup_dir.glob("constitution_config_v1_backup_*.json"))
    assert len(backups) == 1


def test_migrate_v1_to_v2_no_backup(migration, tmp_config_dir):
    """Test migration without backup."""
    v1_config = {"version": "1.0", "backend": "sqlite"}
    migration.config_path.write_text(json.dumps(v1_config), encoding="utf-8")
    
    result = migration.migrate_v1_to_v2(create_backup=False)
    assert result is True
    
    # Check no backup was created
    backups = list(migration.backup_dir.glob("constitution_config_v1_backup_*.json"))
    assert len(backups) == 0


def test_determine_primary_backend_explicit(migration):
    """Test determining primary backend from explicit setting."""
    config = {"backend": "json"}
    backend = migration._determine_primary_backend(config)
    assert backend == "json"


def test_determine_primary_backend_priority(migration):
    """Test determining primary backend from priority."""
    config = {
        "backends": {
            "sqlite": {"primary": True},
            "json": {"primary": False}
        }
    }
    backend = migration._determine_primary_backend(config)
    assert backend == "sqlite"


def test_determine_primary_backend_enabled(migration):
    """Test determining primary backend from enabled status."""
    config = {
        "backends": {
            "sqlite": {"enabled": False},
            "json": {"enabled": True}
        }
    }
    backend = migration._determine_primary_backend(config)
    assert backend == "json"


def test_determine_primary_backend_default(migration):
    """Test default primary backend."""
    config = {}
    backend = migration._determine_primary_backend(config)
    assert backend == "sqlite"


def test_validate_v2_config_valid(migration):
    """Test validating valid v2.0 config."""
    config = {
        "version": "2.0",
        "primary_backend": "sqlite",
        "backend_config": {
            "sqlite": {"path": "config/constitution_rules.db"}
        },
        "fallback": {
            "enabled": True,
            "fallback_backend": "json"
        },
        "sync": {
            "enabled": True,
            "interval_seconds": 60
        }
    }
    result = migration.validate_v2_config(config)
    assert result is True


def test_validate_v2_config_invalid_version(migration):
    """Test validating config with invalid version."""
    config = {"version": "1.0"}
    result = migration.validate_v2_config(config)
    assert result is False


def test_validate_v2_config_invalid_backend(migration):
    """Test validating config with invalid backend."""
    config = {
        "version": "2.0",
        "primary_backend": "invalid"
    }
    result = migration.validate_v2_config(config)
    assert result is False


def test_validate_v2_config_missing_backend_config(migration):
    """Test validating config with missing backend config."""
    config = {
        "version": "2.0",
        "primary_backend": "sqlite"
    }
    result = migration.validate_v2_config(config)
    assert result is False


def test_validate_v2_config_invalid_fallback(migration):
    """Test validating config with invalid fallback."""
    config = {
        "version": "2.0",
        "primary_backend": "sqlite",
        "backend_config": {
            "sqlite": {"path": "config/constitution_rules.db"}
        },
        "fallback": {
            "enabled": True,
            "fallback_backend": "invalid"
        }
    }
    result = migration.validate_v2_config(config)
    assert result is False


def test_validate_v2_config_invalid_sync_interval(migration):
    """Test validating config with invalid sync interval."""
    config = {
        "version": "2.0",
        "primary_backend": "sqlite",
        "backend_config": {
            "sqlite": {"path": "config/constitution_rules.db"}
        },
        "sync": {
            "enabled": True,
            "interval_seconds": 0  # Invalid
        }
    }
    result = migration.validate_v2_config(config)
    assert result is False


def test_get_migration_info_no_config(migration):
    """Test getting migration info when no config exists."""
    info = migration.get_migration_info()
    assert info["config_exists"] is False
    assert info["migration_needed"] is False


def test_get_migration_info_v1_config(migration, tmp_config_dir):
    """Test getting migration info for v1.0 config."""
    v1_config = {"version": "1.0"}
    migration.config_path.write_text(json.dumps(v1_config), encoding="utf-8")
    
    info = migration.get_migration_info()
    assert info["config_exists"] is True
    assert info["current_version"] == "1.0"
    assert info["migration_needed"] is True


def test_get_migration_info_v2_config(migration, tmp_config_dir):
    """Test getting migration info for v2.0 config."""
    v2_config = {"version": "2.0"}
    migration.config_path.write_text(json.dumps(v2_config), encoding="utf-8")
    
    info = migration.get_migration_info()
    assert info["config_exists"] is True
    assert info["current_version"] == "2.0"
    assert info["migration_needed"] is False


def test_get_migration_info_with_backups(migration, tmp_config_dir):
    """Test getting migration info with backups."""
    # Create backup directory and files
    migration.backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = migration.backup_dir / "constitution_config_v1_backup_20240101_120000.json"
    backup_file.write_text(json.dumps({"version": "1.0"}), encoding="utf-8")
    
    info = migration.get_migration_info()
    assert len(info["backups_available"]) == 1


def test_global_migrate_configuration(tmp_config_dir):
    """Test global migrate_configuration function."""
    v1_config = {"version": "1.0", "backend": "sqlite"}
    config_path = tmp_config_dir / "constitution_config.json"
    config_path.write_text(json.dumps(v1_config), encoding="utf-8")
    
    result = config_migration.migrate_configuration(config_dir=str(tmp_config_dir), create_backup=False)
    assert result is True


def test_global_validate_configuration(tmp_config_dir):
    """Test global validate_configuration function."""
    v2_config = {
        "version": "2.0",
        "primary_backend": "sqlite",
        "backend_config": {
            "sqlite": {"path": "config/constitution_rules.db"}
        }
    }
    config_path = tmp_config_dir / "constitution_config.json"
    config_path.write_text(json.dumps(v2_config), encoding="utf-8")
    
    result = config_migration.validate_configuration(config_dir=str(tmp_config_dir))
    assert result is True


def test_global_validate_configuration_no_file(tmp_config_dir):
    """Test global validate_configuration when file doesn't exist."""
    result = config_migration.validate_configuration(config_dir=str(tmp_config_dir))
    assert result is False


def test_global_get_migration_info(tmp_config_dir):
    """Test global get_migration_info function."""
    info = config_migration.get_migration_info(config_dir=str(tmp_config_dir))
    assert "config_exists" in info
    assert "migration_needed" in info
    assert "backups_available" in info

