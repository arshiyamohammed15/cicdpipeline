#!/usr/bin/env python3
"""
Constitution Rule Configuration Manager for ZeroUI 2.0

This module extends the EnhancedConfigManager to provide constitution rule
management functionality with database integration.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .database import ConstitutionRulesDB

logger = logging.getLogger(__name__)
from .rule_extractor import ConstitutionRuleExtractor
from .path_utils import resolve_constitution_db_path
from .rule_count_loader import get_rule_count_loader
try:
    from ..enhanced_config_manager import EnhancedConfigManager
except ImportError:
    # Fallback for testing environment
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from enhanced_config_manager import EnhancedConfigManager
from .base_manager import BaseConstitutionManager

class ConstitutionRuleManager(EnhancedConfigManager, BaseConstitutionManager):
    """
    Constitution rule manager that extends EnhancedConfigManager.

    Provides functionality to manage all constitution rules with
    enable/disable capabilities and database integration.
    """

    def __init__(self, config_dir: str = "config", db_path: Optional[str] = None):
        """
        Initialize the constitution rule manager.

        Args:
            config_dir: Configuration directory path
            db_path: Path to SQLite database file
        """
        super().__init__(config_dir)
        self.db_path = resolve_constitution_db_path(db_path)
        self.constitution_config_file = self.config_dir / "constitution_config.json"
        self._init_constitution_system()

    def _init_constitution_system(self):
        """Initialize the constitution system (database and config)."""
        try:
            # Initialize database with improved connection handling
            self.db_manager = ConstitutionRulesDB(self.db_path)

            # Load or create constitution config
            self._load_constitution_config()

            # Sync config with database
            self.sync_with_database()
        except Exception as e:
            print(f"Error initializing constitution system: {e}")
            # Fallback: create a minimal config without database
            self._load_constitution_config()

    def _load_constitution_config(self):
        """Load constitution configuration from file."""
        if self.constitution_config_file.exists():
            try:
                with open(self.constitution_config_file, 'r', encoding='utf-8') as f:
                    self.constitution_config = json.load(f)
            except (json.JSONDecodeError, ValueError) as e:
                # If config file is corrupted, create default config
                logger.warning(f"Failed to load constitution config (corrupted JSON): {e}")
                total_rules = self._derive_total_rules()
                self.constitution_config = {
                    "constitution_version": "2.0",
                    "total_rules": total_rules,
                    "default_enabled": True,
                    "database_path": str(self.db_path),
                    "last_updated": datetime.now().isoformat(),
                    "rules": {}
                }
                self._save_constitution_config()
        else:
            # Create default configuration with dynamic total_rules derived from source of truth if available
            total_rules = self._derive_total_rules()
            self.constitution_config = {
                "constitution_version": "2.0",
                "total_rules": total_rules,
                "default_enabled": True,
                "database_path": str(self.db_path),
                "last_updated": datetime.now().isoformat(),
                "rules": {}
            }
            self._save_constitution_config()

    def _save_constitution_config(self):
        """Save constitution configuration to file."""
        # Skip timestamp update during pre-commit hooks to prevent IDE commit failures
        is_pre_commit = (
            os.environ.get('GIT_AUTHOR_NAME') or
            os.environ.get('GIT_AUTHOR_EMAIL') or
            os.environ.get('GIT_COMMITTER_NAME') or
            os.environ.get('GIT_COMMITTER_EMAIL') or
            'pre-commit' in os.environ.get('PWD', '').lower() or
            any('git' in arg.lower() for arg in os.sys.argv if hasattr(os, 'sys') and hasattr(os.sys, 'argv'))
        )

        if not is_pre_commit:
            self.constitution_config["last_updated"] = datetime.now().isoformat()

        with open(self.constitution_config_file, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(self.constitution_config, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Ensure trailing newline

    def _derive_total_rules(self) -> int:
        """Get total rule count from the single source of truth."""
        try:
            loader = get_rule_count_loader()
            return loader.get_total_rules()
        except Exception:
            return self._fallback_total_rules()

    def _fallback_total_rules(self) -> int:
        """Fallback sources for total rule count when loader is unavailable."""
        try:
            # Fallback: check database
            if hasattr(self, 'db_manager') and self.db_manager is not None:
                rules = self.db_manager.get_all_rules()
                if rules:
                    return len(rules)
        except Exception:
            pass
        # Fallback: check exported JSON file
        json_path = Path(self.config_dir) / "constitution_rules.json"
        try:
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict) and 'rules' in data:
                    return len(data['rules'])
        except Exception:
            pass
        # Last resort: use 0 and let health check compute later
        return 0

    def is_rule_enabled(self, rule_number: int) -> bool:
        """
        Check if a rule is enabled.

        Args:
            rule_number: Rule number to check

        Returns:
            True if rule is enabled, False otherwise
        """
        # Check database first
        rule = self.db_manager.get_rule_by_number(rule_number)
        if rule:
            return rule['enabled']

        # Fallback to config file
        return self.constitution_config.get("rules", {}).get(str(rule_number), {}).get("enabled", True)

    def enable_rule(self, rule_number: int, config_data: Optional[Dict[str, Any]] = None):
        """
        Enable a rule in both database and config file.

        Args:
            rule_number: Rule number to enable
            config_data: Optional configuration data
        """
        # Update database
        success = self.db_manager.enable_rule(rule_number, config_data)

        if success:
            # Update config file
            if "rules" not in self.constitution_config:
                self.constitution_config["rules"] = {}

            self.constitution_config["rules"][str(rule_number)] = {
                "enabled": True,
                "config": config_data or {},
                "updated_at": datetime.now().isoformat()
            }

            self._save_constitution_config()
            return True

        return False

    def disable_rule(self, rule_number: int, reason: str = ""):
        """
        Disable a rule in both database and config file.

        Args:
            rule_number: Rule number to disable
            reason: Reason for disabling
        """
        # Update database
        success = self.db_manager.disable_rule(rule_number, reason)

        if success:
            # Update config file
            if "rules" not in self.constitution_config:
                self.constitution_config["rules"] = {}

            self.constitution_config["rules"][str(rule_number)] = {
                "enabled": False,
                "reason": reason,
                "disabled_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            self._save_constitution_config()
            return True

        return False

    def get_rule_config(self, rule_number: int) -> Dict[str, Any]:
        """
        Get configuration for a specific rule.

        Args:
            rule_number: Rule number

        Returns:
            Rule configuration dictionary
        """
        return self.constitution_config.get("rules", {}).get(str(rule_number), {})

    def get_all_rule_configs(self) -> Dict[str, Any]:
        """Get all rule configurations."""
        return self.constitution_config.get("rules", {})

    def get_enabled_rules(self) -> List[Dict[str, Any]]:
        """
        Get all enabled rules.

        Returns:
            List of enabled rule dictionaries
        """
        return self.db_manager.get_enabled_rules()

    def get_disabled_rules(self) -> List[Dict[str, Any]]:
        """
        Get all disabled rules.

        Returns:
            List of disabled rule dictionaries
        """
        return self.db_manager.get_disabled_rules()

    def get_rules_by_category(self, category: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get rules by category.

        Args:
            category: Category name
            enabled_only: If True, return only enabled rules

        Returns:
            List of rule dictionaries
        """
        return self.db_manager.get_rules_by_category(category, enabled_only)

    def get_rule_by_number(self, rule_number: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific rule by its number.

        Args:
            rule_number: Rule number to retrieve

        Returns:
            Rule dictionary or None if not found
        """
        return self.db_manager.get_rule_by_number(rule_number)

    def get_rule_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about rules in the database.

        Returns:
            Statistics dictionary
        """
        return self.db_manager.get_rule_statistics()

    def get_all_rules(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all rules from the database.

        Args:
            enabled_only: If True, return only enabled rules

        Returns:
            List of rule dictionaries
        """
        return self.db_manager.get_all_rules(enabled_only)

    def search_rules(self, search_term: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Search rules by title or content.

        Args:
            search_term: The term to search for
            enabled_only: If True, search only enabled rules

        Returns:
            List of matching rule dictionaries
        """
        from .queries import ConstitutionQueries
        queries = ConstitutionQueries(self.db_manager)
        return queries.search_rules(search_term)

    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.

        Args:
            backup_path: Path where to save the backup

        Returns:
            True if backup successful, False otherwise
        """
        try:
            import shutil
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception:
            return False

    def restore_database(self, backup_path: str) -> bool:
        """
        Restore database from backup.

        Args:
            backup_path: Path to the backup file

        Returns:
            True if restore successful, False otherwise
        """
        try:
            import shutil
            shutil.copy2(backup_path, self.db_path)
            return True
        except Exception:
            return False

    def sync_with_database(self):
        """Sync configuration file with database state."""
        try:
            if not hasattr(self, 'db_manager') or self.db_manager is None:
                print("Database manager not available, skipping sync")
                return

            all_rules = self.db_manager.get_all_rules()

            if "rules" not in self.constitution_config:
                self.constitution_config["rules"] = {}

            for rule in all_rules:
                rule_number = rule['rule_number']
                enabled = rule['enabled']
                rule_key = str(rule_number)

                if rule_key not in self.constitution_config["rules"]:
                    self.constitution_config["rules"][rule_key] = {}

                # Only update timestamp if the enabled state actually changed
                current_enabled = self.constitution_config["rules"][rule_key].get("enabled", True)
                if current_enabled != enabled:
                    self.constitution_config["rules"][rule_key]["enabled"] = enabled
                    self.constitution_config["rules"][rule_key]["updated_at"] = datetime.now().isoformat()
                elif "enabled" not in self.constitution_config["rules"][rule_key]:
                    # Initialize enabled state if missing, but don't update timestamp
                    self.constitution_config["rules"][rule_key]["enabled"] = enabled

            self._save_constitution_config()
        except Exception as e:
            print(f"Error syncing with database: {e}")
            # Continue without database sync

    def export_rules_to_json(self, enabled_only: bool = False) -> str:
        """
        Export rules to JSON format.

        Args:
            enabled_only: If True, export only enabled rules

        Returns:
            JSON string of rules
        """
        return self.db_manager.export_rules_to_json(enabled_only)

    def import_rules_from_json(self, json_data: str) -> bool:
        """
        Import rules from JSON format.

        Args:
            json_data: JSON string containing rules

        Returns:
            True if successful, False otherwise
        """
        return self.db_manager.import_rules_from_json(json_data)

    def log_validation(self, rule_number: int, result: str, details: str = ""):
        """
        Log validation result for a rule.

        Args:
            rule_number: Rule number
            result: Validation result (passed, failed, warning)
            details: Additional details
        """
        self.db_manager.log_validation(rule_number, result, details)

    def get_categories(self) -> List[str]:
        """
        Get list of all available rule categories.

        Returns:
            List of category names
        """
        extractor = ConstitutionRuleExtractor()
        return list(extractor.get_categories().keys())

    def get_category_info(self, category: str) -> Dict[str, Any]:
        """
        Get information about a specific category.

        Args:
            category: Category name

        Returns:
            Category information dictionary
        """
        extractor = ConstitutionRuleExtractor()
        categories = extractor.get_categories()
        return categories.get(category, {})

    def reset_all_rules_to_enabled(self):
        """Reset all rules to enabled state."""
        all_rules = self.db_manager.get_all_rules()

        for rule in all_rules:
            if not rule['enabled']:
                self.enable_rule(rule['rule_number'], {"reset": True})

    def reset_all_rules_to_disabled(self):
        """Reset all rules to disabled state."""
        all_rules = self.db_manager.get_all_rules()

        for rule in all_rules:
            if rule['enabled']:
                self.disable_rule(rule['rule_number'], "Bulk disable")

    def get_constitution_config(self) -> Dict[str, Any]:
        """
        Get the constitution configuration.

        Returns:
            Constitution configuration dictionary
        """
        return self.constitution_config

    def update_constitution_config(self, config_updates: Dict[str, Any]):
        """
        Update constitution configuration.

        Args:
            config_updates: Configuration updates to apply
        """
        self.constitution_config.update(config_updates)
        self._save_constitution_config()

    def initialize(self) -> bool:
        """
        Initialize the constitution rule manager.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize database
            self.db_manager._init_database()

            # Sync with configuration
            self.sync_with_database()

            return True
        except Exception as e:
            print(f"Failed to initialize constitution rule manager: {e}")
            return False

    def get_backend_type(self) -> str:
        """Get the backend type."""
        return "sqlite"

    def get_backend_info(self) -> Dict[str, Any]:
        """Get backend-specific information."""
        return {
            "backend_type": "sqlite",
            "database_path": str(self.db_path),
            "database_exists": Path(self.db_path).exists(),
            "database_size": Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0,
            "last_updated": self._get_last_updated(),
            "constitution_version": "2.0"
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the database."""
        expected_rules = self._derive_total_rules()
        actual_rules = 0
        try:
            # Check database file existence and accessibility
            db_exists = Path(self.db_path).exists()
            db_readable = False
            db_writable = False

            if db_exists:
                try:
                    # Test database connection
                    with self.db_manager as db:
                        stats = db.get_rule_statistics()
                    db_readable = True
                    db_writable = True
                except Exception:
                    pass

            # Check data integrity
            data_valid = True
            try:
                with self.db_manager as db:
                    rules = db.get_all_rules()
                    actual_rules = len(rules)
                    if expected_rules > 0 and actual_rules != expected_rules:
                        data_valid = False
            except Exception:
                data_valid = False

            healthy = db_exists and db_readable and db_writable and data_valid and expected_rules > 0

            return {
                "healthy": healthy,
                "database_exists": db_exists,
                "database_readable": db_readable,
                "database_writable": db_writable,
                "data_valid": data_valid,
                "expected_rules": expected_rules,
                "actual_rules": actual_rules,
                "last_updated": self._get_last_updated()
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def _get_last_updated(self) -> Optional[str]:
        """Get the last update timestamp."""
        try:
            with self.db_manager as db:
                # Get the most recent update from any rule
                rules = db.get_all_rules()
                if rules:
                    # For now, return current timestamp
                    # In a real implementation, you'd track actual update times
                    return datetime.now().isoformat()
        except Exception:
            pass
        return None

    def close(self):
        """Close database connection."""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.close()
        except Exception as e:
            logger.warning(f"Error closing constitution rule manager: {e}")
            # Don't re-raise - context manager should handle exceptions gracefully


# Convenience function to get a constitution rule manager instance
def get_constitution_manager(config_dir: str = "config") -> ConstitutionRuleManager:
    """
    Get a constitution rule manager instance.

    Args:
        config_dir: Configuration directory path

    Returns:
        ConstitutionRuleManager instance
    """
    return ConstitutionRuleManager(config_dir)




# Example usage
def main():
    """Example usage of the Constitution Rule Manager."""

    with ConstitutionRuleManager() as manager:
        print("Constitution Rule Manager initialized")

        # Get statistics
        stats = manager.get_rule_statistics()
        print(f"\nDatabase Statistics:")
        print(f"Total rules: {stats['total_rules']}")
        print(f"Enabled rules: {stats['enabled_rules']}")
        print(f"Disabled rules: {stats['disabled_rules']}")
        print(f"Enabled percentage: {stats['enabled_percentage']:.1f}%")

        # Get rules by category
        print(f"\nRules by category:")
        for category, count in stats['category_counts'].items():
            print(f"  {category}: {count} rules")

        # Example: Get a specific rule
        rule_1 = manager.get_rule_by_number(1)
        if rule_1:
            print(f"\nRule 1: {rule_1['title']}")
            print(f"Category: {rule_1['category']}")
            print(f"Enabled: {rule_1['enabled']}")

        # Example: Get rules by category
        basic_work_rules = manager.get_rules_by_category("basic_work")
        print(f"\nBasic Work Rules ({len(basic_work_rules)}):")
        for rule in basic_work_rules:
            print(f"  Rule {rule['rule_number']}: {rule['title']} (Enabled: {rule['enabled']})")

        # Example: Disable a rule
        print(f"\nDisabling Rule 1...")
        manager.disable_rule(1, "Testing disable functionality")

        # Check if rule is disabled
        rule_1_updated = manager.get_rule_by_number(1)
        print(f"Rule 1 enabled status: {rule_1_updated['enabled']}")

        # Re-enable the rule
        print(f"Re-enabling Rule 1...")
        manager.enable_rule(1, {"test": True})

        # Final check
        rule_1_final = manager.get_rule_by_number(1)
        print(f"Rule 1 final enabled status: {rule_1_final['enabled']}")


if __name__ == "__main__":
    main()
