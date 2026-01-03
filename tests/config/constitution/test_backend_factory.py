from __future__ import annotations

import json
import os
from pathlib import Path
import pytest

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


class _StubMigration:
    def __init__(self, *_args, **_kwargs):
        self.migrated = False

    def migrate_v1_to_v2(self, create_backup: bool = True) -> bool:
        self.migrated = True
        return True


def test_auto_backend_prefers_env_and_fallback(tmp_path, monkeypatch):
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))

    # Write a simple v2 config
    config = factory._create_default_config()
    config["primary_backend"] = "sqlite"
    config_path = Path(tmp_path) / "constitution_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    # Primary unhealthy, fallback healthy
    monkeypatch.setattr(factory, "_create_sqlite_manager", lambda *a, **k: _StubManager(healthy=False))
    monkeypatch.setattr(factory, "_create_json_manager", lambda *a, **k: _StubManager(healthy=True))
    monkeypatch.setattr(factory, "_migration", _StubMigration())

    manager = factory.get_constitution_manager(backend="auto")
    assert isinstance(manager, _StubManager)
    assert manager.healthy is True

    # Env override chooses JSON directly
    monkeypatch.setenv("CONSTITUTION_BACKEND", "json")
    manager2 = factory.get_constitution_manager(backend="auto")
    assert isinstance(manager2, _StubManager)
    assert manager2.healthy is True


def test_switch_backend_updates_config(tmp_path):
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    assert factory.switch_backend("json") is True
    cfg = json.loads((Path(tmp_path) / "constitution_config.json").read_text(encoding="utf-8"))
    assert cfg["primary_backend"] == "json"
    assert cfg["backend"] == "json"


def test_backend_factory_initialization(tmp_path):
    """Test factory initialization with default and custom config dirs."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    assert factory.config_dir == str(tmp_path)
    assert factory.config_path == Path(tmp_path) / "constitution_config.json"
    assert factory._migration is not None


def test_get_constitution_manager_explicit_backend(tmp_path, monkeypatch):
    """Test getting manager with explicit backend selection."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    # Mock managers
    sqlite_manager = _StubManager(healthy=True, backend_type="sqlite")
    json_manager = _StubManager(healthy=True, backend_type="json")
    
    monkeypatch.setattr(factory, "_create_sqlite_manager", lambda *a, **k: sqlite_manager)
    monkeypatch.setattr(factory, "_create_json_manager", lambda *a, **k: json_manager)
    monkeypatch.setattr(factory, "_migration", _StubMigration())
    
    # Test SQLite backend
    manager = factory.get_constitution_manager(backend="sqlite")
    assert manager.backend_type == "sqlite"
    
    # Test JSON backend
    manager = factory.get_constitution_manager(backend="json")
    assert manager.backend_type == "json"


def test_get_constitution_manager_unsupported_backend(tmp_path):
    """Test that unsupported backend raises ValueError."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    with pytest.raises(ValueError, match="Unsupported backend"):
        factory.get_constitution_manager(backend="invalid")


def test_get_constitution_manager_auto_fallback(tmp_path, monkeypatch):
    """Test automatic fallback when primary backend fails."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    config = factory._create_default_config()
    config["primary_backend"] = "sqlite"
    config["fallback"]["enabled"] = True
    config_path = Path(tmp_path) / "constitution_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    
    # Primary unhealthy, fallback healthy
    sqlite_manager = _StubManager(healthy=False)
    json_manager = _StubManager(healthy=True)
    
    monkeypatch.setattr(factory, "_create_sqlite_manager", lambda *a, **k: sqlite_manager)
    monkeypatch.setattr(factory, "_create_json_manager", lambda *a, **k: json_manager)
    monkeypatch.setattr(factory, "_migration", _StubMigration())
    
    manager = factory.get_constitution_manager(backend="auto")
    assert manager.healthy is True
    assert manager == json_manager


def test_get_constitution_manager_all_backends_fail(tmp_path, monkeypatch):
    """Test that RuntimeError is raised when all backends fail."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    config = factory._create_default_config()
    config["primary_backend"] = "sqlite"
    config["fallback"]["enabled"] = True
    config_path = Path(tmp_path) / "constitution_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    
    # Both unhealthy
    sqlite_manager = _StubManager(healthy=False)
    json_manager = _StubManager(healthy=False)
    
    monkeypatch.setattr(factory, "_create_sqlite_manager", lambda *a, **k: sqlite_manager)
    monkeypatch.setattr(factory, "_create_json_manager", lambda *a, **k: json_manager)
    monkeypatch.setattr(factory, "_migration", _StubMigration())
    
    with pytest.raises(RuntimeError, match="All backends failed"):
        factory.get_constitution_manager(backend="auto")


def test_determine_auto_backend_env_override(tmp_path, monkeypatch):
    """Test that environment variable overrides config."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    config = factory._create_default_config()
    config["primary_backend"] = "sqlite"
    config_path = Path(tmp_path) / "constitution_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    
    # Set environment variable
    monkeypatch.setenv("CONSTITUTION_BACKEND", "json")
    
    backend = factory._determine_auto_backend(config)
    assert backend == "json"


def test_determine_auto_backend_primary_backend(tmp_path):
    """Test that primary_backend setting is used."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    config = factory._create_default_config()
    config["primary_backend"] = "json"
    
    backend = factory._determine_auto_backend(config)
    assert backend == "json"


def test_determine_auto_backend_legacy_backend(tmp_path):
    """Test that legacy backend setting is used for compatibility."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    config = {"backend": "json"}  # Legacy format
    
    backend = factory._determine_auto_backend(config)
    assert backend == "json"


def test_determine_auto_backend_default(tmp_path):
    """Test that default is sqlite when no config."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    config = {}
    
    backend = factory._determine_auto_backend(config)
    assert backend == "sqlite"


def test_get_available_backends(tmp_path, monkeypatch):
    """Test getting information about available backends."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    sqlite_manager = _StubManager(healthy=True)
    json_manager = _StubManager(healthy=True)
    
    monkeypatch.setattr(factory, "_create_sqlite_manager", lambda *a, **k: sqlite_manager)
    monkeypatch.setattr(factory, "_create_json_manager", lambda *a, **k: json_manager)
    
    backends = factory.get_available_backends()
    
    assert "sqlite" in backends
    assert "json" in backends
    assert backends["sqlite"]["available"] is True
    assert backends["json"]["available"] is True


def test_get_available_backends_with_errors(tmp_path, monkeypatch):
    """Test getting backend info when one backend fails."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    def failing_sqlite(*a, **k):
        raise Exception("SQLite failed")
    
    json_manager = _StubManager(healthy=True)
    
    monkeypatch.setattr(factory, "_create_sqlite_manager", failing_sqlite)
    monkeypatch.setattr(factory, "_create_json_manager", lambda *a, **k: json_manager)
    
    backends = factory.get_available_backends()
    
    assert backends["sqlite"]["available"] is False
    assert backends["json"]["available"] is True


def test_get_active_backend_config(tmp_path):
    """Test getting active backend configuration."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    config = factory._create_default_config()
    config["primary_backend"] = "json"
    config_path = Path(tmp_path) / "constitution_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    
    active_config = factory.get_active_backend_config()
    
    assert active_config["backend"] == "json"
    assert "config" in active_config
    assert "version" in active_config


def test_get_backend_status(tmp_path, monkeypatch):
    """Test getting comprehensive backend status."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    sqlite_manager = _StubManager(healthy=True)
    json_manager = _StubManager(healthy=True)
    
    monkeypatch.setattr(factory, "_create_sqlite_manager", lambda *a, **k: sqlite_manager)
    monkeypatch.setattr(factory, "_create_json_manager", lambda *a, **k: json_manager)
    
    status = factory.get_backend_status()
    
    assert "version" in status
    assert "current_backend" in status
    assert "backends" in status
    assert "configuration_path" in status


def test_switch_backend_invalid_backend(tmp_path):
    """Test that switching to invalid backend raises ValueError."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    with pytest.raises(ValueError, match="Invalid backend"):
        factory.switch_backend("invalid")


def test_switch_backend_sqlite(tmp_path):
    """Test switching to SQLite backend."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    result = factory.switch_backend("sqlite")
    assert result is True
    
    cfg = json.loads((Path(tmp_path) / "constitution_config.json").read_text(encoding="utf-8"))
    assert cfg["primary_backend"] == "sqlite"
    assert cfg["backend"] == "sqlite"


def test_create_default_config(tmp_path):
    """Test default configuration creation."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    config = factory._create_default_config()
    
    assert config["version"] == "2.0"
    assert config["primary_backend"] == "sqlite"
    assert "backend_config" in config
    assert "fallback" in config
    assert "sync" in config
    assert config["fallback"]["enabled"] is True
    assert config["fallback"]["fallback_backend"] == "json"


def test_get_configuration_with_cache(tmp_path):
    """Test configuration caching."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    config1 = factory._get_configuration()
    config2 = factory._get_configuration()
    
    # Should return same object due to caching
    assert config1 is config2


def test_get_configuration_auto_migration(tmp_path, monkeypatch):
    """Test automatic migration from v1.0 to v2.0."""
    factory = backend_factory.ConstitutionBackendFactory(config_dir=str(tmp_path))
    
    # Create v1.0 config
    v1_config = {
        "version": "1.0",
        "backend": "sqlite",
        "backends": {
            "sqlite": {"path": "config/constitution_rules.db"},
            "json": {"path": "config/constitution_rules.json"}
        }
    }
    config_path = Path(tmp_path) / "constitution_config.json"
    config_path.write_text(json.dumps(v1_config), encoding="utf-8")
    
    migration = _StubMigration()
    monkeypatch.setattr(factory, "_migration", migration)
    
    config = factory._get_configuration()
    
    # Should trigger migration
    assert migration.migrated is True


def test_global_functions(tmp_path):
    """Test global factory functions."""
    # Reset global instance
    backend_factory._factory_instance = None
    
    # Test get_backend_factory
    factory1 = backend_factory.get_backend_factory()
    factory2 = backend_factory.get_backend_factory()
    
    # Should return same instance
    assert factory1 is factory2
    
    # Test get_backend_status
    status = backend_factory.get_backend_status()
    assert "version" in status
    
    # Test get_active_backend_config
    active_config = backend_factory.get_active_backend_config()
    assert "backend" in active_config
