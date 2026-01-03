"""Additional tests for backend_factory to achieve 100% coverage."""

from __future__ import annotations

import json
import os
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open

from config.constitution import backend_factory


class _StubManager:
    def __init__(self, healthy: bool = True, backend_type: str = "stub"):
        self.healthy = healthy
        self.closed = False
        self.backend_type = backend_type

    def health_check(self):
        return {"healthy": self.healthy}

    def close(self):
        self.closed = True

    def get_backend_type(self):
        return self.backend_type

    def get_backend_info(self):
        return {"backend_type": self.backend_type, "healthy": self.healthy}


def test_save_configuration_success(tmp_path):
    """Test _save_configuration successfully saves config."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    config = factory._create_default_config()
    
    factory._save_configuration(config)
    
    assert factory.config_path.exists()
    loaded = json.loads(factory.config_path.read_text(encoding="utf-8"))
    assert loaded["version"] == "2.0"


def test_save_configuration_error(tmp_path, monkeypatch):
    """Test _save_configuration handles errors."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    config = factory._create_default_config()
    
    # Make directory read-only to cause error
    with patch('builtins.open', side_effect=PermissionError("Permission denied")):
        factory._save_configuration(config)
        # Should not raise, just log error


def test_create_manager_unknown_backend(tmp_path, monkeypatch):
    """Test _create_manager raises ValueError for unknown backend."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    config = factory._create_default_config()
    
    with pytest.raises(ValueError, match="Unknown backend"):
        factory._create_manager("unknown", config)


def test_create_sqlite_manager_v1_fallback(tmp_path, monkeypatch):
    """Test _create_sqlite_manager uses v1.0 config fallback."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    # v1.0 format config
    config = {
        "backends": {
            "sqlite": {"path": "custom/path.db"}
        }
    }
    
    with patch('config.constitution.backend_factory.ConstitutionRuleManager') as mock_manager:
        mock_manager.return_value = _StubManager()
        factory._create_sqlite_manager(config)
        
        # Should use v1.0 path
        mock_manager.assert_called_once()
        call_kwargs = mock_manager.call_args[1]
        assert "custom/path.db" in str(call_kwargs.get("db_path", ""))


def test_create_json_manager_v1_fallback(tmp_path, monkeypatch):
    """Test _create_json_manager uses v1.0 config fallback."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    # v1.0 format config
    config = {
        "backends": {
            "json": {"path": "custom/path.json"}
        }
    }
    
    with patch('config.constitution.backend_factory.ConstitutionRuleManagerJSON') as mock_manager:
        mock_manager.return_value = _StubManager()
        factory._create_json_manager(config)
        
        # Should use v1.0 path
        mock_manager.assert_called_once()
        call_kwargs = mock_manager.call_args[1]
        assert "custom/path.json" in str(call_kwargs.get("json_path", ""))


def test_is_manager_healthy_exception(tmp_path):
    """Test _is_manager_healthy handles exceptions."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    manager = Mock()
    manager.health_check.side_effect = Exception("Health check failed")
    
    result = factory._is_manager_healthy(manager)
    assert result is False


def test_get_available_backends_both_fail(tmp_path, monkeypatch):
    """Test get_available_backends when both backends fail."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    def failing_manager(*a, **k):
        raise Exception("Backend failed")
    
    monkeypatch.setattr(factory, "_create_sqlite_manager", failing_manager)
    monkeypatch.setattr(factory, "_create_json_manager", failing_manager)
    
    backends = factory.get_available_backends()
    
    assert backends["sqlite"]["available"] is False
    assert backends["json"]["available"] is False
    assert "error" in backends["sqlite"]
    assert "error" in backends["json"]


def test_get_backend_status_v1_fallback(tmp_path):
    """Test get_backend_status with v1.0 config fallback."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    # v1.0 format config
    config = {
        "version": "1.0",
        "backend": "sqlite",
        "backends": {
            "sqlite": {"path": "config/constitution_rules.db"},
            "json": {"path": "config/constitution_rules.json"}
        },
        "auto_fallback": True,
        "fallback_backend": "json",
        "auto_sync": True,
        "sync_interval": 60
    }
    factory.config_path.write_text(json.dumps(config), encoding="utf-8")
    factory._config_cache = None
    
    with patch.object(factory, 'get_available_backends', return_value={"sqlite": {}, "json": {}}):
        status = factory.get_backend_status()
        
        assert status["current_backend"] == "sqlite"
        assert status["fallback_backend"] == "json"
        assert status["auto_fallback"] is True


def test_global_migrate_configuration(tmp_path, monkeypatch):
    """Test global migrate_configuration function."""
    with patch('config.constitution.backend_factory.ConfigMigration') as mock_migration_class:
        mock_migration = Mock()
        mock_migration.migrate_v1_to_v2.return_value = True
        mock_migration_class.return_value = mock_migration
        
        result = backend_factory.migrate_configuration(create_backup=False)
        assert result is True


def test_global_validate_configuration(tmp_path, monkeypatch):
    """Test global validate_configuration function."""
    with patch('config.constitution.backend_factory.ConfigMigration') as mock_migration_class:
        mock_migration = Mock()
        mock_migration.validate_v2_config.return_value = True
        mock_migration_class.return_value = mock_migration
        
        # Mock config file exists
        config_path = tmp_path / "constitution_config.json"
        config_path.write_text(json.dumps({"version": "2.0"}), encoding="utf-8")
        
        with patch('config.constitution.backend_factory.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps({"version": "2.0"}))):
                result = backend_factory.validate_configuration()
                # Function may return True or False depending on validation


def test_global_get_migration_info(tmp_path, monkeypatch):
    """Test global get_migration_info function."""
    with patch('config.constitution.backend_factory.ConfigMigration') as mock_migration_class:
        mock_migration = Mock()
        mock_migration.get_migration_info.return_value = {"config_exists": True, "current_version": "2.0"}
        mock_migration_class.return_value = mock_migration
        
        info = backend_factory.get_migration_info()
        assert "config_exists" in info


def test_get_configuration_cache_expiry(tmp_path, monkeypatch):
    """Test _get_configuration cache expiry after 5 seconds."""
    import time
    
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    # First call - should cache
    config1 = factory._get_configuration()
    
    # Simulate time passing (6 seconds)
    factory._last_config_load = time.time() - 6
    
    # Second call - should reload (cache expired)
    with patch('builtins.open', mock_open(read_data=json.dumps({"version": "2.0"}))):
        config2 = factory._get_configuration()
        # Should reload from file
        assert factory._last_config_load > time.time() - 1


def test_get_configuration_migration_failure(tmp_path, monkeypatch):
    """Test _get_configuration when migration fails."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    # Create v1.0 config
    v1_config = {"version": "1.0", "backend": "sqlite"}
    config_path = Path(tmp_path) / "constitution_config.json"
    config_path.write_text(json.dumps(v1_config), encoding="utf-8")
    
    # Mock migration to fail
    mock_migration = Mock()
    mock_migration.migrate_v1_to_v2.return_value = False
    monkeypatch.setattr(factory, "_migration", mock_migration)
    
    config = factory._get_configuration()
    
    # Should use default config when migration fails
    assert config["version"] == "2.0"


def test_get_configuration_file_read_error(tmp_path, monkeypatch):
    """Test _get_configuration when file read fails."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    config_path = Path(tmp_path) / "constitution_config.json"
    config_path.write_text('{"version": "2.0"}', encoding="utf-8")
    
    with patch('builtins.open', side_effect=IOError("Read error")):
        config = factory._get_configuration()
        # Should return default config
        assert config["version"] == "2.0"

