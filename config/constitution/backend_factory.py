#!/usr/bin/env python3
"""
Backend Factory for Constitution Rules Database

This module provides a factory pattern for creating constitution rule managers
with different backends (SQLite, JSON) and automatic fallback capabilities.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime
import logging

from .base_manager import BaseConstitutionManager
from .config_manager import ConstitutionRuleManager
from .config_manager_json import ConstitutionRuleManagerJSON
from .config_migration import ConfigMigration

logger = logging.getLogger(__name__)

class ConstitutionBackendFactory:
    """
    Factory for creating constitution rule managers with different backends.

    This factory supports:
    - SQLite backend (primary, high performance)
    - JSON backend (fallback, simple)
    - Auto-selection based on configuration
    - Automatic fallback on failure
    """

    SUPPORTED_BACKENDS = ["sqlite", "json", "auto"]

    def __init__(self, config_dir: str = "config"):
        """
        Initialize the backend factory.

        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = config_dir
        self.config_path = Path(config_dir) / "constitution_config.json"
        self._config_cache = None
        self._last_config_load = 0
        self._migration = ConfigMigration(config_dir)

    def get_constitution_manager(
        self,
        backend: str = "auto",
        **kwargs
    ) -> BaseConstitutionManager:
        """
        Get a constitution rule manager with specified backend.

        Args:
            backend: Backend type ("sqlite", "json", "auto")
            **kwargs: Additional arguments for the manager

        Returns:
            Constitution rule manager instance

        Raises:
            ValueError: If backend is not supported
            RuntimeError: If no backend is available
        """
        if backend not in self.SUPPORTED_BACKENDS:
            raise ValueError(f"Unsupported backend: {backend}. Supported: {self.SUPPORTED_BACKENDS}")

        # Get configuration
        config = self._get_configuration()

        if backend == "auto":
            backend = self._determine_auto_backend(config)

        # Try to create the requested backend
        manager = self._create_manager(backend, config, **kwargs)

        # If auto-fallback is enabled and primary fails, try fallback
        fallback_config = config.get("fallback", {})
        auto_fallback_enabled = fallback_config.get("enabled", config.get("auto_fallback", True))

        if (backend != "json" and
            auto_fallback_enabled and
            not self._is_manager_healthy(manager)):

            # Get fallback backend from v2.0 format
            fallback_backend = fallback_config.get("fallback_backend", config.get("fallback_backend", "json"))
            logger.warning(f"Primary backend {backend} failed, falling back to {fallback_backend}")

            try:
                manager = self._create_manager(fallback_backend, config, **kwargs)
                if self._is_manager_healthy(manager):
                    logger.info(f"Successfully fell back to {fallback_backend} backend")
                else:
                    raise RuntimeError(f"Both primary ({backend}) and fallback ({fallback_backend}) backends failed")
            except Exception as e:
                logger.error(f"Fallback to {fallback_backend} failed: {e}")
                raise RuntimeError(f"All backends failed. Last error: {e}")

        return manager

    def _get_configuration(self) -> Dict[str, Any]:
        """Get configuration with caching and auto-migration."""
        import time

        # Simple cache with 5-second expiry
        current_time = time.time()
        if (self._config_cache is not None and
            current_time - self._last_config_load < 5):
            return self._config_cache

        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Auto-migrate v1.0 to v2.0 if needed
                if config.get("version") != "2.0":
                    logger.info("Auto-migrating configuration from v1.0 to v2.0")
                    if self._migration.migrate_v1_to_v2(create_backup=True):
                        # Reload the migrated configuration
                        with open(self.config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                    else:
                        logger.warning("Migration failed, using default configuration")
                        config = self._create_default_config()
            else:
                # Create default v2.0 configuration
                config = self._create_default_config()
                self._save_configuration(config)

            self._config_cache = config
            self._last_config_load = current_time

            return config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default v2.0 configuration."""
        return {
            "version": "2.0",
            "last_updated": datetime.now().isoformat(),

            # Single source of truth for backend selection
            "primary_backend": "sqlite",

            # Backend-specific settings
            "backend_config": {
                "sqlite": {
                    "path": "config/constitution_rules.db",
                    "timeout": 30,
                    "wal_mode": True,
                    "connection_pool_size": 5
                },
                "json": {
                    "path": "config/constitution_rules.json",
                    "auto_backup": True,
                    "atomic_writes": True,
                    "backup_retention": 5
                }
            },

            # System behavior settings
            "fallback": {
                "enabled": True,
                "fallback_backend": "json"
            },

            "sync": {
                "enabled": True,
                "interval_seconds": 60,
                "auto_sync_on_write": True,
                "conflict_resolution": "primary_wins"
            },

            # Rule configurations
            "rules": {},

            # Legacy fields for compatibility (avoid hardcoded totals)
            "constitution_version": "2.0",
            "default_enabled": True
        }

    def _save_configuration(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def _determine_auto_backend(self, config: Dict[str, Any]) -> str:
        """
        Determine which backend to use for auto mode.

        Priority:
        1. Environment variable
        2. v2.0 primary_backend setting
        3. v1.0 legacy backend setting (for compatibility)
        4. Default (sqlite)
        """
        # Check environment variable
        env_backend = os.environ.get("CONSTITUTION_BACKEND")
        if env_backend and env_backend in ["sqlite", "json"]:
            return env_backend

        # Check v2.0 primary_backend setting
        primary_backend = config.get("primary_backend")
        if primary_backend in ["sqlite", "json"]:
            return primary_backend

        # Check v1.0 legacy backend setting (for compatibility)
        legacy_backend = config.get("backend")
        if legacy_backend in ["sqlite", "json"]:
            return legacy_backend

        # Default to sqlite
        return "sqlite"

    def _create_manager(
        self,
        backend: str,
        config: Dict[str, Any],
        **kwargs
    ) -> BaseConstitutionManager:
        """Create a manager for the specified backend."""
        try:
            if backend == "sqlite":
                return self._create_sqlite_manager(config, **kwargs)
            elif backend == "json":
                return self._create_json_manager(config, **kwargs)
            else:
                raise ValueError(f"Unknown backend: {backend}")

        except Exception as e:
            logger.error(f"Failed to create {backend} manager: {e}")
            raise

    def _create_sqlite_manager(self, config: Dict[str, Any], **kwargs) -> ConstitutionRuleManager:
        """Create SQLite manager."""
        # Get SQLite configuration from v2.0 format
        backend_config = config.get("backend_config", {})
        sqlite_config = backend_config.get("sqlite", {})

        # Fallback to v1.0 format for compatibility
        if not sqlite_config:
            sqlite_config = config.get("backends", {}).get("sqlite", {})

        db_path = sqlite_config.get("path", "config/constitution_rules.db")

        # Remove config_dir from kwargs if present to avoid conflict
        kwargs.pop('config_dir', None)

        return ConstitutionRuleManager(
            config_dir=self.config_dir,
            db_path=db_path,
            **kwargs
        )

    def _create_json_manager(self, config: Dict[str, Any], **kwargs) -> ConstitutionRuleManagerJSON:
        """Create JSON manager."""
        # Get JSON configuration from v2.0 format
        backend_config = config.get("backend_config", {})
        json_config = backend_config.get("json", {})

        # Fallback to v1.0 format for compatibility
        if not json_config:
            json_config = config.get("backends", {}).get("json", {})

        json_path = json_config.get("path", "config/constitution_rules.json")

        # Remove config_dir from kwargs if present to avoid conflict
        kwargs.pop('config_dir', None)

        return ConstitutionRuleManagerJSON(
            config_dir=self.config_dir,
            json_path=json_path,
            **kwargs
        )

    def _is_manager_healthy(self, manager: BaseConstitutionManager) -> bool:
        """Check if a manager is healthy."""
        try:
            health = manager.health_check()
            return health.get("healthy", False)
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False

    def get_available_backends(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about available backends.

        Returns:
            Dictionary containing backend information
        """
        config = self._get_configuration()
        backends = {}

        # Check SQLite backend
        try:
            sqlite_manager = self._create_sqlite_manager(config)
            sqlite_health = sqlite_manager.health_check()

            # Get SQLite config from v2.0 format with v1.0 fallback
            backend_config = config.get("backend_config", {})
            sqlite_config = backend_config.get("sqlite", config.get("backends", {}).get("sqlite", {}))

            backends["sqlite"] = {
                "available": True,
                "healthy": sqlite_health.get("healthy", False),
                "config": sqlite_config,
                "health": sqlite_health
            }
            sqlite_manager.close()
        except Exception as e:
            backend_config = config.get("backend_config", {})
            sqlite_config = backend_config.get("sqlite", config.get("backends", {}).get("sqlite", {}))

            backends["sqlite"] = {
                "available": False,
                "healthy": False,
                "error": str(e),
                "config": sqlite_config
            }

        # Check JSON backend
        try:
            json_manager = self._create_json_manager(config)
            json_health = json_manager.health_check()

            # Get JSON config from v2.0 format with v1.0 fallback
            backend_config = config.get("backend_config", {})
            json_config = backend_config.get("json", config.get("backends", {}).get("json", {}))

            backends["json"] = {
                "available": True,
                "healthy": json_health.get("healthy", False),
                "config": json_config,
                "health": json_health
            }
            json_manager.close()
        except Exception as e:
            backend_config = config.get("backend_config", {})
            json_config = backend_config.get("json", config.get("backends", {}).get("json", {}))

            backends["json"] = {
                "available": False,
                "healthy": False,
                "error": str(e),
                "config": json_config
            }

        return backends

    def get_active_backend_config(self) -> Dict[str, Any]:
        """
        Get configuration for the currently active backend.

        Returns:
            Dictionary containing active backend configuration
        """
        config = self._get_configuration()
        active_backend = config.get("primary_backend", config.get("backend", "sqlite"))

        # Get backend config from v2.0 format with v1.0 fallback
        backend_config = config.get("backend_config", {})
        active_config = backend_config.get(active_backend, {})

        # Fallback to v1.0 format
        if not active_config:
            active_config = config.get("backends", {}).get(active_backend, {})

        return {
            "backend": active_backend,
            "config": active_config,
            "version": config.get("version", "1.0")
        }

    def switch_backend(self, new_backend: str) -> bool:
        """
        Switch the default backend in configuration.

        Args:
            new_backend: New backend to set as default

        Returns:
            True if switch successful, False otherwise
        """
        if new_backend not in ["sqlite", "json"]:
            raise ValueError(f"Invalid backend: {new_backend}")

        try:
            config = self._get_configuration()

            # Update v2.0 primary_backend (single source of truth)
            config["primary_backend"] = new_backend
            config["last_updated"] = datetime.now().isoformat()

            # Keep v1.0 compatibility fields for backward compatibility
            config["backend"] = new_backend

            # Update backend priorities in v1.0 format (for compatibility)
            if "backends" not in config:
                config["backends"] = {}

            for backend_name in ["sqlite", "json"]:
                if backend_name not in config["backends"]:
                    config["backends"][backend_name] = {}
                config["backends"][backend_name]["primary"] = (backend_name == new_backend)
                config["backends"][backend_name]["enabled"] = True

            self._save_configuration(config)
            self._config_cache = None  # Clear cache

            logger.info(f"Switched default backend to {new_backend}")
            return True

        except Exception as e:
            logger.error(f"Failed to switch backend to {new_backend}: {e}")
            return False

    def get_backend_status(self) -> Dict[str, Any]:
        """
        Get status of all backends.

        Returns:
            Dictionary containing backend status information
        """
        config = self._get_configuration()
        backends = self.get_available_backends()

        # Get v2.0 configuration values with v1.0 fallbacks
        fallback_config = config.get("fallback", {})
        sync_config = config.get("sync", {})

        return {
            "version": config.get("version", "1.0"),
            "current_backend": config.get("primary_backend", config.get("backend", "sqlite")),
            "fallback_backend": fallback_config.get("fallback_backend", config.get("fallback_backend", "json")),
            "auto_fallback": fallback_config.get("enabled", config.get("auto_fallback", True)),
            "auto_sync": sync_config.get("enabled", config.get("auto_sync", True)),
            "sync_interval": sync_config.get("interval_seconds", config.get("sync_interval", 60)),
            "backends": backends,
            "configuration_path": str(self.config_path),
            "config_exists": self.config_path.exists(),
            "last_updated": config.get("last_updated")
        }

# Global factory instance
_factory_instance = None

def get_constitution_manager(backend: str = "auto", **kwargs) -> BaseConstitutionManager:
    """
    Get a constitution rule manager with specified backend.

    This is the main entry point for creating constitution rule managers.

    Args:
        backend: Backend type ("sqlite", "json", "auto")
        **kwargs: Additional arguments for the manager

    Returns:
        Constitution rule manager instance
    """
    global _factory_instance

    if _factory_instance is None:
        _factory_instance = ConstitutionBackendFactory()

    return _factory_instance.get_constitution_manager(backend, **kwargs)

def get_backend_factory() -> ConstitutionBackendFactory:
    """
    Get the global backend factory instance.

    Returns:
        Backend factory instance
    """
    global _factory_instance

    if _factory_instance is None:
        _factory_instance = ConstitutionBackendFactory()

    return _factory_instance

def switch_backend(new_backend: str) -> bool:
    """
    Switch the default backend.

    Args:
        new_backend: New backend to set as default

    Returns:
        True if switch successful, False otherwise
    """
    factory = get_backend_factory()
    return factory.switch_backend(new_backend)

def get_backend_status() -> Dict[str, Any]:
    """
    Get status of all backends.

    Returns:
        Dictionary containing backend status information
    """
    factory = get_backend_factory()
    return factory.get_backend_status()

def get_active_backend_config() -> Dict[str, Any]:
    """
    Get configuration for the currently active backend.

    Returns:
        Dictionary containing active backend configuration
    """
    factory = get_backend_factory()
    return factory.get_active_backend_config()

def migrate_configuration(create_backup: bool = True) -> bool:
    """
    Migrate configuration from v1.0 to v2.0.

    Args:
        create_backup: Whether to create a backup

    Returns:
        True if migration successful, False otherwise
    """
    from .config_migration import migrate_configuration as _migrate
    return _migrate(create_backup=create_backup)

def validate_configuration() -> bool:
    """
    Validate v2.0 configuration.

    Returns:
        True if valid, False otherwise
    """
    from .config_migration import validate_configuration as _validate
    return _validate()

def get_migration_info() -> Dict[str, Any]:
    """
    Get migration information.

    Returns:
        Dictionary containing migration information
    """
    from .config_migration import get_migration_info as _get_info
    return _get_info()
