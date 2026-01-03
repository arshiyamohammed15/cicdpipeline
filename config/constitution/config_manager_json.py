#!/usr/bin/env python3
"""
JSON-based Constitution Rule Configuration Manager for ZeroUI 2.0

This module extends the EnhancedConfigManager to provide JSON-based
constitution rule management functionality.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .base_manager import BaseConstitutionManager
from .constitution_rules_json import ConstitutionRulesJSON
try:
    from ..enhanced_config_manager import EnhancedConfigManager
except ImportError:
    # Fallback for testing environment
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from enhanced_config_manager import EnhancedConfigManager

logger = logging.getLogger(__name__)

class ConstitutionRuleManagerJSON(BaseConstitutionManager):
    """
    JSON-based constitution rule manager.

    This class provides a JSON-based implementation of the constitution
    rule manager, extending the base manager interface.
    """

    def __init__(self, config_dir: str = "config", json_path: str = "config/constitution_rules.json"):
        """
        Initialize the JSON-based constitution rule manager.

        Args:
            config_dir: Configuration directory path
            json_path: Path to JSON database file
        """
        super().__init__(config_dir)
        self.json_path = json_path
        self.json_manager = ConstitutionRulesJSON(json_path)
        self.constitution_config_path = Path(config_dir) / "constitution_config.json"
        self._config_data = {}
        self._load_constitution_config()

    def _load_constitution_config(self):
        """Load constitution configuration from JSON file."""
        try:
            if self.constitution_config_path.exists():
                with open(self.constitution_config_path, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)

                # Validate config structure
                self._validate_config_structure()
            else:
                # Create default configuration
                self._config_data = {
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "rules": {}
                }
                self._save_constitution_config()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            # Try to repair the config file
            if self._repair_config_file():
                self._load_constitution_config()
            else:
                self._config_data = self._create_default_config()
        except Exception as e:
            logger.error(f"Failed to load constitution config: {e}")
            self._config_data = self._create_default_config()

    def _validate_config_structure(self):
        """Validate configuration structure."""
        required_keys = ["version", "rules"]
        for key in required_keys:
            if key not in self._config_data:
                raise ValueError(f"Missing required config key: {key}")

    def _create_default_config(self):
        """Create default configuration."""
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "rules": {}
        }

    def _repair_config_file(self) -> bool:
        """Attempt to repair corrupted config file."""
        try:
            if not self.constitution_config_path.exists():
                return False

            # Create backup
            backup_path = self.constitution_config_path.with_suffix('.corrupted.backup')
            import shutil
            shutil.copy2(self.constitution_config_path, backup_path)

            # Recreate config
            self._config_data = self._create_default_config()
            self._save_constitution_config()

            logger.info(f"Config file repaired, backup created at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to repair config file: {e}")
            return False

    def _save_constitution_config(self):
        """Save constitution configuration to JSON file."""
        try:
            self._config_data["last_updated"] = datetime.now().isoformat()
            with open(self.constitution_config_path, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
                f.write('\n')  # Ensure trailing newline
        except Exception as e:
            logger.error(f"Failed to save constitution config: {e}")

    def initialize(self) -> bool:
        """
        Initialize the constitution rule manager.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize JSON database
            self.json_manager._init_database()

            # Sync with configuration
            self._sync_with_database()

            self._initialized = True
            logger.info("JSON constitution rule manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize JSON constitution rule manager: {e}")
            return False

    def is_rule_enabled(self, rule_number: int) -> bool:
        """
        Check if a specific rule is enabled.

        Args:
            rule_number: The rule number to check

        Returns:
            True if rule is enabled, False otherwise
        """
        if not self._initialized:
            self.initialize()

        # Check configuration first
        rule_config = self._config_data.get("rules", {}).get(str(rule_number))
        if rule_config is not None:
            return rule_config.get("enabled", True)

        # Fall back to database
        rule = self.json_manager.get_rule_by_number(rule_number)
        return rule["enabled"] if rule else True

    def enable_rule(self, rule_number: int, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Enable a specific rule.

        Args:
            rule_number: The rule number to enable
            config_data: Optional configuration data for the rule

        Returns:
            True if rule was enabled successfully, False otherwise
        """
        if not self._initialized:
            self.initialize()

        try:
            # Update database
            success = self.json_manager.enable_rule(rule_number, config_data)

            if success:
                # Update configuration
                if "rules" not in self._config_data:
                    self._config_data["rules"] = {}

                self._config_data["rules"][str(rule_number)] = {
                    "enabled": True,
                    "config": config_data or {},
                    "updated_at": datetime.now().isoformat()
                }

                self._save_constitution_config()

                logger.info(f"Rule {rule_number} enabled successfully")

            return success

        except Exception as e:
            logger.error(f"Failed to enable rule {rule_number}: {e}")
            return False

    def disable_rule(self, rule_number: int, reason: str = "") -> bool:
        """
        Disable a specific rule.

        Args:
            rule_number: The rule number to disable
            reason: Reason for disabling the rule

        Returns:
            True if rule was disabled successfully, False otherwise
        """
        if not self._initialized:
            self.initialize()

        try:
            # Update database
            success = self.json_manager.disable_rule(rule_number, reason)

            if success:
                # Update configuration
                if "rules" not in self._config_data:
                    self._config_data["rules"] = {}

                self._config_data["rules"][str(rule_number)] = {
                    "enabled": False,
                    "disabled_reason": reason,
                    "disabled_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                self._save_constitution_config()

                logger.info(f"Rule {rule_number} disabled successfully")

            return success

        except Exception as e:
            logger.error(f"Failed to disable rule {rule_number}: {e}")
            return False

    def get_all_rules(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all rules from the database.

        Args:
            enabled_only: If True, return only enabled rules

        Returns:
            List of rule dictionaries
        """
        if not self._initialized:
            self.initialize()

        return self.json_manager.get_all_rules(enabled_only)

    def get_rule_by_number(self, rule_number: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific rule by its number.

        Args:
            rule_number: The rule number to retrieve

        Returns:
            Rule dictionary if found, None otherwise
        """
        if not self._initialized:
            self.initialize()

        return self.json_manager.get_rule_by_number(rule_number)

    def get_rules_by_category(self, category: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get rules by category.

        Args:
            category: The category to filter by
            enabled_only: If True, return only enabled rules

        Returns:
            List of rule dictionaries in the specified category
        """
        if not self._initialized:
            self.initialize()

        return self.json_manager.get_rules_by_category(category, enabled_only)

    def get_rule_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about rules in the database.

        Returns:
            Dictionary containing rule statistics
        """
        if not self._initialized:
            self.initialize()

        return self.json_manager.get_rule_statistics()

    def search_rules(self, search_term: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Search rules by title or content.

        Args:
            search_term: The term to search for
            enabled_only: If True, search only enabled rules

        Returns:
            List of matching rule dictionaries
        """
        if not self._initialized:
            self.initialize()

        return self.json_manager.search_rules(search_term, enabled_only)

    def export_rules_to_json(self, enabled_only: bool = False) -> str:
        """
        Export rules to JSON format.

        Args:
            enabled_only: If True, export only enabled rules

        Returns:
            JSON string containing the rules
        """
        if not self._initialized:
            self.initialize()

        return self.json_manager.export_rules_to_json(enabled_only)

    def get_categories(self) -> Dict[str, Any]:
        """
        Get all available categories.

        Returns:
            Dictionary containing category information
        """
        if not self._initialized:
            self.initialize()

        return self.json_manager.get_categories()

    def get_backend_type(self) -> str:
        """
        Get the backend type.

        Returns:
            Backend type string
        """
        return "json"

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get backend-specific information.

        Returns:
            Dictionary containing backend information
        """
        if not self._initialized:
            self.initialize()

        backend_info = self.json_manager.get_backend_info()
        backend_info.update({
            "config_path": str(self.constitution_config_path),
            "config_exists": self.constitution_config_path.exists()
        })
        return backend_info

    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.

        Args:
            backup_path: Path where to save the backup

        Returns:
            True if backup successful, False otherwise
        """
        if not self._initialized:
            self.initialize()

        return self.json_manager.backup_database(backup_path)

    def restore_database(self, backup_path: str) -> bool:
        """
        Restore database from backup.

        Args:
            backup_path: Path to the backup file

        Returns:
            True if restore successful, False otherwise
        """
        if not self._initialized:
            self.initialize()

        success = self.json_manager.restore_database(backup_path)
        if success:
            # Sync configuration after restore
            self._sync_with_database()
        return success

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database.

        Returns:
            Dictionary containing health check results
        """
        if not self._initialized:
            self.initialize()

        try:
            db_health = self.json_manager.health_check()
        except Exception as e:
            db_health = {
                "healthy": False,
                "error": str(e)
            }

        # Add configuration health check
        config_health = {
            "config_file_exists": self.constitution_config_path.exists(),
            "config_readable": False,
            "config_valid": False
        }

        try:
            if self.constitution_config_path.exists():
                with open(self.constitution_config_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                config_health["config_readable"] = True
                config_health["config_valid"] = True
        except Exception:
            pass

        # Overall health
        overall_healthy = db_health.get("healthy", False) and config_health["config_valid"]

        return {
            "healthy": overall_healthy,
            "database": db_health,
            "configuration": config_health,
            "backend_type": "json"
        }

    def close(self):
        """Close the database connection."""
        if hasattr(self, 'json_manager'):
            self.json_manager.close()
        self._initialized = False
        logger.info("JSON constitution rule manager closed")

    def _sync_with_database(self):
        """Sync configuration with database state."""
        try:
            # Get all rules from database
            all_rules = self.json_manager.get_all_rules()

            # Update configuration with current database state
            if "rules" not in self._config_data:
                self._config_data["rules"] = {}

            for rule in all_rules:
                rule_number = str(rule["rule_number"])
                if rule_number not in self._config_data["rules"]:
                    self._config_data["rules"][rule_number] = {
                        "enabled": rule["enabled"],
                        "updated_at": datetime.now().isoformat()
                    }

            self._save_constitution_config()
            logger.info("Configuration synced with database")

        except Exception as e:
            logger.error(f"Failed to sync configuration with database: {e}")

    def get_rule_config(self, rule_number: int) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific rule.

        Args:
            rule_number: The rule number to get config for

        Returns:
            Rule configuration dictionary or None if not found
        """
        if not self._initialized:
            self.initialize()

        return self._config_data.get("rules", {}).get(str(rule_number))

    def get_all_rule_configs(self) -> Dict[str, Any]:
        """
        Get all rule configurations.

        Returns:
            Dictionary containing all rule configurations
        """
        if not self._initialized:
            self.initialize()

        return self._config_data.get("rules", {})

    def update_rule_config(self, rule_number: int, config_data: Dict[str, Any]) -> bool:
        """
        Update configuration for a specific rule.

        Args:
            rule_number: The rule number to update
            config_data: New configuration data

        Returns:
            True if update successful, False otherwise
        """
        if not self._initialized:
            self.initialize()

        try:
            if "rules" not in self._config_data:
                self._config_data["rules"] = {}

            self._config_data["rules"][str(rule_number)] = {
                **self._config_data["rules"].get(str(rule_number), {}),
                **config_data,
                "updated_at": datetime.now().isoformat()
            }

            self._save_constitution_config()
            return True

        except Exception as e:
            logger.error(f"Failed to update rule config for {rule_number}: {e}")
            return False
