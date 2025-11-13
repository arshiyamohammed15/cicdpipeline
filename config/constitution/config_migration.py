#!/usr/bin/env python3
"""
Configuration Migration Utilities

This module handles migration between different configuration versions,
specifically from v1.0 (complex dual-flag system) to v2.0 (simplified single-source system).
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConfigMigration:
    """
    Handles migration between configuration versions.
    """

    def __init__(self, config_dir: str = "config"):
        """
        Initialize the migration utility.

        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = Path(config_dir)
        self.config_path = self.config_dir / "constitution_config.json"
        self.backup_dir = self.config_dir / "backups"

    def migrate_v1_to_v2(self, create_backup: bool = True) -> bool:
        """
        Migrate configuration from v1.0 to v2.0 format.

        Args:
            create_backup: Whether to create a backup of the original config

        Returns:
            True if migration successful, False otherwise
        """
        try:
            # Load current configuration
            if not self.config_path.exists():
                logger.warning("No configuration file found to migrate")
                return False

            with open(self.config_path, 'r', encoding='utf-8') as f:
                old_config = json.load(f)

            # Check if already v2.0
            if old_config.get("version") == "2.0":
                logger.info("Configuration is already v2.0, no migration needed")
                return True

            # Create backup if requested
            if create_backup:
                self._create_backup(old_config)

            # Perform migration
            new_config = self._migrate_config_structure(old_config)

            # Save new configuration
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=2, ensure_ascii=False)

            logger.info("Successfully migrated configuration from v1.0 to v2.0")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def _migrate_config_structure(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate the configuration structure from v1.0 to v2.0.

        Args:
            old_config: Old configuration dictionary

        Returns:
            New configuration dictionary
        """
        # Determine primary backend from old config
        primary_backend = self._determine_primary_backend(old_config)

        # Extract backend configurations
        backends_config = old_config.get("backends", {})
        sqlite_config = backends_config.get("sqlite", {})
        json_config = backends_config.get("json", {})

        # Create new v2.0 configuration
        new_config = {
            "version": "2.0",
            "last_updated": datetime.now().isoformat(),

            # Single source of truth for backend selection
            "primary_backend": primary_backend,

            # Backend-specific settings
            "backend_config": {
                "sqlite": {
                    "path": sqlite_config.get("path", "config/constitution_rules.db"),
                    "timeout": 30,
                    "wal_mode": True,
                    "connection_pool_size": 5
                },
                "json": {
                    "path": json_config.get("path", "config/constitution_rules.json"),
                    "auto_backup": True,
                    "atomic_writes": True,
                    "backup_retention": 5
                }
            },

            # System behavior settings
            "fallback": {
                "enabled": old_config.get("auto_fallback", True),
                "fallback_backend": old_config.get("fallback_backend", "json")
            },

            "sync": {
                "enabled": old_config.get("auto_sync", True),
                "interval_seconds": old_config.get("sync_interval", 60),
                "auto_sync_on_write": True,
                "conflict_resolution": "primary_wins"
            },

            # Preserve rule configurations
            "rules": old_config.get("rules", {}),

            # Preserve other settings
            "constitution_version": old_config.get("constitution_version", "2.0"),
            "total_rules": old_config.get("total_rules", 149),
            "default_enabled": old_config.get("default_enabled", True)
        }

        return new_config

    def _determine_primary_backend(self, old_config: Dict[str, Any]) -> str:
        """
        Determine the primary backend from old configuration.

        Args:
            old_config: Old configuration dictionary

        Returns:
            Primary backend name
        """
        # Check explicit backend setting
        explicit_backend = old_config.get("backend")
        if explicit_backend in ["sqlite", "json"]:
            return explicit_backend

        # Check backend priorities
        backends_config = old_config.get("backends", {})
        for backend_name in ["sqlite", "json"]:
            backend_config = backends_config.get(backend_name, {})
            if backend_config.get("primary", False):
                return backend_name

        # Check enabled status
        for backend_name in ["sqlite", "json"]:
            backend_config = backends_config.get(backend_name, {})
            if backend_config.get("enabled", True):
                return backend_name

        # Default to sqlite
        return "sqlite"

    def _create_backup(self, config: Dict[str, Any]):
        """
        Create a backup of the current configuration.

        Args:
            config: Configuration dictionary to backup
        """
        try:
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"constitution_config_v1_backup_{timestamp}.json"

            # Save backup
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"Created configuration backup: {backup_path}")

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")

    def validate_v2_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate v2.0 configuration structure.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check version
            if config.get("version") != "2.0":
                logger.error("Invalid configuration version")
                return False

            # Check primary backend
            primary_backend = config.get("primary_backend")
            if primary_backend not in ["sqlite", "json"]:
                logger.error(f"Invalid primary_backend: {primary_backend}")
                return False

            # Check backend config exists
            backend_config = config.get("backend_config", {})
            if primary_backend not in backend_config:
                logger.error(f"Missing backend_config for {primary_backend}")
                return False

            # Check required backend config fields
            required_fields = {
                "sqlite": ["path"],
                "json": ["path"]
            }

            for field in required_fields.get(primary_backend, []):
                if field not in backend_config[primary_backend]:
                    logger.error(f"Missing required field {field} for {primary_backend}")
                    return False

            # Check fallback config
            fallback_config = config.get("fallback", {})
            if fallback_config.get("enabled", False):
                fallback_backend = fallback_config.get("fallback_backend")
                if fallback_backend not in ["sqlite", "json"]:
                    logger.error(f"Invalid fallback_backend: {fallback_backend}")
                    return False

            # Check sync config
            sync_config = config.get("sync", {})
            if sync_config.get("enabled", False):
                interval = sync_config.get("interval_seconds", 60)
                if not isinstance(interval, int) or interval < 1:
                    logger.error(f"Invalid sync interval: {interval}")
                    return False

            logger.info("Configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def get_migration_info(self) -> Dict[str, Any]:
        """
        Get information about migration status and available backups.

        Returns:
            Dictionary containing migration information
        """
        info = {
            "config_exists": self.config_path.exists(),
            "current_version": None,
            "backups_available": [],
            "migration_needed": False
        }

        # Check current configuration
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                info["current_version"] = config.get("version", "unknown")
                info["migration_needed"] = config.get("version") != "2.0"
            except Exception as e:
                info["current_version"] = f"error: {e}"

        # Check available backups
        if self.backup_dir.exists():
            backup_files = list(self.backup_dir.glob("constitution_config_v1_backup_*.json"))
            info["backups_available"] = [f.name for f in backup_files]

        return info

def migrate_configuration(config_dir: str = "config", create_backup: bool = True) -> bool:
    """
    Migrate configuration from v1.0 to v2.0.

    Args:
        config_dir: Configuration directory path
        create_backup: Whether to create a backup

    Returns:
        True if migration successful, False otherwise
    """
    migration = ConfigMigration(config_dir)
    return migration.migrate_v1_to_v2(create_backup)

def validate_configuration(config_dir: str = "config") -> bool:
    """
    Validate v2.0 configuration.

    Args:
        config_dir: Configuration directory path

    Returns:
        True if valid, False otherwise
    """
    migration = ConfigMigration(config_dir)
    config_path = migration.config_path

    if not config_path.exists():
        logger.error("Configuration file not found")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return migration.validate_v2_config(config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return False

def get_migration_info(config_dir: str = "config") -> Dict[str, Any]:
    """
    Get migration information.

    Args:
        config_dir: Configuration directory path

    Returns:
        Dictionary containing migration information
    """
    migration = ConfigMigration(config_dir)
    return migration.get_migration_info()
