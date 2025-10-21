#!/usr/bin/env python3
"""
Migration Utilities for Constitution Rules Database

This module provides migration tools to move data between SQLite and JSON
backends, with data integrity verification and backup capabilities.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from .config_manager import ConstitutionRuleManager
from .config_manager_json import ConstitutionRuleManagerJSON
from .sync_manager import get_sync_manager

logger = logging.getLogger(__name__)

class ConstitutionMigration:
    """
    Migration utilities for moving data between backends.
    
    Features:
    - Full migration between SQLite and JSON
    - Data integrity verification
    - Automatic backup before migration
    - Rollback capabilities
    - Migration history tracking
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the migration utility.
        
        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = config_dir
        self.migration_history_path = Path(config_dir) / "migration_history.json"
        self._migration_history = []
        self._load_migration_history()
    
    def _load_migration_history(self):
        """Load migration history from file."""
        try:
            if self.migration_history_path.exists():
                with open(self.migration_history_path, 'r', encoding='utf-8') as f:
                    self._migration_history = json.load(f)
                
                # Validate migration history structure
                if not isinstance(self._migration_history, list):
                    logger.warning("Invalid migration history format, resetting")
                    self._migration_history = []
            else:
                self._migration_history = []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in migration history file: {e}")
            # Create backup and reset
            self._backup_corrupted_migration_history()
            self._migration_history = []
        except Exception as e:
            logger.error(f"Failed to load migration history: {e}")
            self._migration_history = []
    
    def _backup_corrupted_migration_history(self):
        """Backup corrupted migration history file."""
        try:
            if self.migration_history_path.exists():
                backup_path = self.migration_history_path.with_suffix('.corrupted.backup')
                shutil.copy2(self.migration_history_path, backup_path)
                logger.info(f"Corrupted migration history backed up to {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup corrupted migration history: {e}")
    
    def _save_migration_history(self):
        """Save migration history to file."""
        try:
            self.migration_history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.migration_history_path, 'w', encoding='utf-8') as f:
                json.dump(self._migration_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save migration history: {e}")
    
    def _log_migration(self, migration_type: str, source: str, target: str, 
                      success: bool, details: str = ""):
        """Log a migration operation."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "migration_type": migration_type,
            "source": source,
            "target": target,
            "success": success,
            "details": details
        }
        self._migration_history.append(entry)
        
        # Keep only last 50 entries
        if len(self._migration_history) > 50:
            self._migration_history = self._migration_history[-50:]
        
        self._save_migration_history()
    
    def migrate_sqlite_to_json(self, create_backup: bool = True) -> Dict[str, Any]:
        """
        Migrate all data from SQLite to JSON backend.
        
        Args:
            create_backup: If True, create backup before migration
            
        Returns:
            Dictionary containing migration results
        """
        try:
            logger.info("Starting SQLite to JSON migration")
            
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_path = self._create_backup("json", "pre_migration")
                if not backup_path:
                    logger.warning("Failed to create backup, continuing with migration")
            
            # Get source data from SQLite
            sqlite_manager = ConstitutionRuleManager(config_dir=self.config_dir)
            sqlite_rules = sqlite_manager.get_all_rules()
            sqlite_stats = sqlite_manager.get_rule_statistics()
            
            logger.info(f"Found {len(sqlite_rules)} rules in SQLite database")
            
            # Create new JSON database
            json_manager = ConstitutionRuleManagerJSON(config_dir=self.config_dir)
            
            # Clear existing JSON data and recreate with SQLite data
            json_manager.json_manager._create_database()
            
            # Update JSON database with SQLite data
            rules_migrated = 0
            for rule in sqlite_rules:
                rule_number = str(rule["rule_number"])
                
                # Update rule in JSON
                json_manager.json_manager.data["rules"][rule_number] = {
                    "rule_number": rule["rule_number"],
                    "title": rule["title"],
                    "category": rule["category"],
                    "priority": rule["priority"],
                    "content": rule["content"],
                    "enabled": rule["enabled"],
                    "config": {
                        "default_enabled": rule["enabled"],
                        "notes": "",
                        "disabled_reason": None,
                        "disabled_at": None
                    },
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                        "usage_count": 0,
                        "last_used": None,
                        "migrated_from": "sqlite",
                        "migration_timestamp": datetime.now().isoformat()
                    }
                }
                
                rules_migrated += 1
            
            # Update JSON database statistics and save
            json_manager.json_manager._update_statistics()
            json_manager.json_manager._save_database()
            
            # Update JSON configuration
            json_manager._sync_with_database()
            
            # Verify migration
            verification = self._verify_migration(sqlite_rules, json_manager.get_all_rules())
            
            if verification["success"]:
                # Log successful migration
                self._log_migration(
                    "sqlite_to_json", "sqlite", "json", True,
                    f"Migrated {rules_migrated} rules successfully"
                )
                
                logger.info(f"SQLite to JSON migration completed successfully. Migrated {rules_migrated} rules.")
                
                return {
                    "success": True,
                    "rules_migrated": rules_migrated,
                    "backup_created": backup_path is not None,
                    "backup_path": backup_path,
                    "verification": verification
                }
            else:
                # Migration verification failed
                logger.error("Migration verification failed")
                return {
                    "success": False,
                    "error": "Migration verification failed",
                    "verification": verification,
                    "backup_path": backup_path
                }
            
        except Exception as e:
            logger.error(f"SQLite to JSON migration failed: {e}")
            self._log_migration(
                "sqlite_to_json", "sqlite", "json", False, str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "backup_path": backup_path
            }
        finally:
            try:
                sqlite_manager.close()
                json_manager.close()
            except:
                pass
    
    def migrate_json_to_sqlite(self, create_backup: bool = True) -> Dict[str, Any]:
        """
        Migrate all data from JSON to SQLite backend.
        
        Args:
            create_backup: If True, create backup before migration
            
        Returns:
            Dictionary containing migration results
        """
        try:
            logger.info("Starting JSON to SQLite migration")
            
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_path = self._create_backup("sqlite", "pre_migration")
                if not backup_path:
                    logger.warning("Failed to create backup, continuing with migration")
            
            # Get source data from JSON
            json_manager = ConstitutionRuleManagerJSON(config_dir=self.config_dir)
            json_rules = json_manager.get_all_rules()
            json_stats = json_manager.get_rule_statistics()
            
            logger.info(f"Found {len(json_rules)} rules in JSON database")
            
            # Create new SQLite database
            sqlite_manager = ConstitutionRuleManager(config_dir=self.config_dir)
            
            # Clear existing SQLite data and recreate with JSON data
            sqlite_manager.db_manager._init_database()
            
            # Update SQLite database with JSON data
            rules_migrated = 0
            for rule in json_rules:
                # Insert rule into SQLite
                sqlite_manager.db_manager.insert_rule(
                    rule["rule_number"],
                    rule["title"],
                    rule["category"],
                    rule["priority"],
                    rule["content"],
                    rule["enabled"]
                )
                
                rules_migrated += 1
            
            # Verify migration
            verification = self._verify_migration(json_rules, sqlite_manager.get_all_rules())
            
            if verification["success"]:
                # Log successful migration
                self._log_migration(
                    "json_to_sqlite", "json", "sqlite", True,
                    f"Migrated {rules_migrated} rules successfully"
                )
                
                logger.info(f"JSON to SQLite migration completed successfully. Migrated {rules_migrated} rules.")
                
                return {
                    "success": True,
                    "rules_migrated": rules_migrated,
                    "backup_created": backup_path is not None,
                    "backup_path": backup_path,
                    "verification": verification
                }
            else:
                # Migration verification failed
                logger.error("Migration verification failed")
                return {
                    "success": False,
                    "error": "Migration verification failed",
                    "verification": verification,
                    "backup_path": backup_path
                }
            
        except Exception as e:
            logger.error(f"JSON to SQLite migration failed: {e}")
            self._log_migration(
                "json_to_sqlite", "json", "sqlite", False, str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "backup_path": backup_path
            }
        finally:
            try:
                json_manager.close()
                sqlite_manager.close()
            except:
                pass
    
    def _verify_migration(self, source_rules: List[Dict[str, Any]], 
                         target_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify that migration was successful.
        
        Args:
            source_rules: Rules from source backend
            target_rules: Rules from target backend
            
        Returns:
            Dictionary containing verification results
        """
        try:
            # Check rule count
            source_count = len(source_rules)
            target_count = len(target_rules)
            
            if source_count != target_count:
                return {
                    "success": False,
                    "error": f"Rule count mismatch: source={source_count}, target={target_count}",
                    "source_count": source_count,
                    "target_count": target_count
                }
            
            # Check individual rules
            source_rules_dict = {rule["rule_number"]: rule for rule in source_rules}
            target_rules_dict = {rule["rule_number"]: rule for rule in target_rules}
            
            missing_rules = []
            different_rules = []
            
            for rule_number, source_rule in source_rules_dict.items():
                if rule_number not in target_rules_dict:
                    missing_rules.append(rule_number)
                else:
                    target_rule = target_rules_dict[rule_number]
                    
                    # Compare important fields
                    important_fields = ["title", "category", "priority", "content", "enabled"]
                    for field in important_fields:
                        if source_rule.get(field) != target_rule.get(field):
                            different_rules.append({
                                "rule_number": rule_number,
                                "field": field,
                                "source_value": source_rule.get(field),
                                "target_value": target_rule.get(field)
                            })
                            break
            
            success = len(missing_rules) == 0 and len(different_rules) == 0
            
            return {
                "success": success,
                "source_count": source_count,
                "target_count": target_count,
                "missing_rules": missing_rules,
                "different_rules": different_rules,
                "missing_count": len(missing_rules),
                "different_count": len(different_rules)
            }
            
        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_backup(self, backend: str, suffix: str = "") -> Optional[str]:
        """
        Create a backup of the specified backend.
        
        Args:
            backend: Backend to backup ("sqlite" or "json")
            suffix: Suffix to add to backup filename
            
        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(self.config_dir) / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            if backend == "sqlite":
                source_path = Path(self.config_dir) / "constitution_rules.db"
                backup_filename = f"constitution_rules_{timestamp}_{suffix}.db"
            elif backend == "json":
                source_path = Path(self.config_dir) / "constitution_rules.json"
                backup_filename = f"constitution_rules_{timestamp}_{suffix}.json"
            else:
                raise ValueError(f"Unknown backend: {backend}")
            
            if not source_path.exists():
                logger.warning(f"Source file {source_path} does not exist, skipping backup")
                return None
            
            backup_path = backup_dir / backup_filename
            shutil.copy2(source_path, backup_path)
            
            logger.info(f"Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def restore_from_backup(self, backup_path: str, target_backend: str) -> Dict[str, Any]:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            target_backend: Target backend ("sqlite" or "json")
            
        Returns:
            Dictionary containing restore results
        """
        try:
            logger.info(f"Restoring {target_backend} from backup: {backup_path}")
            
            backup_file = Path(backup_path)
            if not backup_file.exists():
                return {
                    "success": False,
                    "error": f"Backup file not found: {backup_path}"
                }
            
            # Create current backup before restore
            current_backup = self._create_backup(target_backend, "pre_restore")
            
            if target_backend == "sqlite":
                target_path = Path(self.config_dir) / "constitution_rules.db"
            elif target_backend == "json":
                target_path = Path(self.config_dir) / "constitution_rules.json"
            else:
                return {
                    "success": False,
                    "error": f"Unknown target backend: {target_backend}"
                }
            
            # Copy backup to target location
            shutil.copy2(backup_file, target_path)
            
            # Verify restore
            if target_backend == "sqlite":
                manager = ConstitutionRuleManager(config_dir=self.config_dir)
            else:
                manager = ConstitutionRuleManagerJSON(config_dir=self.config_dir)
            
            try:
                health = manager.health_check()
                if health.get("healthy", False):
                    self._log_migration(
                        "restore", "backup", target_backend, True,
                        f"Restored from {backup_path}"
                    )
                    
                    logger.info(f"Successfully restored {target_backend} from backup")
                    return {
                        "success": True,
                        "target_backend": target_backend,
                        "backup_path": backup_path,
                        "current_backup": current_backup,
                        "health_check": health
                    }
                else:
                    return {
                        "success": False,
                        "error": "Health check failed after restore",
                        "health_check": health,
                        "current_backup": current_backup
                    }
            finally:
                manager.close()
            
        except Exception as e:
            logger.error(f"Restore from backup failed: {e}")
            self._log_migration(
                "restore", "backup", target_backend, False, str(e)
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    def repair_sync(self) -> Dict[str, Any]:
        """
        Repair synchronization between backends.
        
        This method detects and fixes inconsistencies between SQLite and JSON backends.
        
        Returns:
            Dictionary containing repair results
        """
        try:
            logger.info("Starting sync repair")
            
            # Get sync manager
            sync_manager = get_sync_manager()
            
            # Detect conflicts
            conflicts = sync_manager._detect_conflicts()
            
            if not conflicts:
                logger.info("No conflicts detected, backends are in sync")
                return {
                    "success": True,
                    "conflicts_found": 0,
                    "conflicts_resolved": 0,
                    "message": "No conflicts detected"
                }
            
            logger.info(f"Found {len(conflicts)} conflicts, attempting to resolve")
            
            # Get configuration to determine primary backend
            from .backend_factory import get_backend_factory
            factory = get_backend_factory()
            config = factory._get_configuration()
            primary_backend = config.get("backend", "sqlite")
            
            # Resolve conflicts
            resolution_results = sync_manager._resolve_conflicts(conflicts, primary_backend)
            
            # Verify repair
            verification = sync_manager.verify_sync()
            
            success = verification.get("synchronized", False)
            
            if success:
                logger.info("Sync repair completed successfully")
                self._log_migration(
                    "repair_sync", "conflicts", "resolved", True,
                    f"Resolved {resolution_results['resolved']} conflicts"
                )
            else:
                logger.warning("Sync repair completed but verification failed")
            
            return {
                "success": success,
                "conflicts_found": len(conflicts),
                "conflicts_resolved": resolution_results.get("resolved", 0),
                "conflicts_failed": resolution_results.get("failed", 0),
                "verification": verification,
                "primary_backend": primary_backend
            }
            
        except Exception as e:
            logger.error(f"Sync repair failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_migration_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get migration history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of migration history entries
        """
        return self._migration_history[-limit:] if limit > 0 else self._migration_history
    
    def clear_migration_history(self):
        """Clear migration history."""
        self._migration_history = []
        self._save_migration_history()
        logger.info("Migration history cleared")

# Global migration instance
_migration_instance = None

def get_migration_manager() -> ConstitutionMigration:
    """
    Get the global migration manager instance.
    
    Returns:
        Migration manager instance
    """
    global _migration_instance
    
    if _migration_instance is None:
        _migration_instance = ConstitutionMigration()
    
    return _migration_instance

def migrate_sqlite_to_json(create_backup: bool = True) -> Dict[str, Any]:
    """
    Migrate from SQLite to JSON backend.
    
    Args:
        create_backup: If True, create backup before migration
        
    Returns:
        Dictionary containing migration results
    """
    migration_manager = get_migration_manager()
    return migration_manager.migrate_sqlite_to_json(create_backup)

def migrate_json_to_sqlite(create_backup: bool = True) -> Dict[str, Any]:
    """
    Migrate from JSON to SQLite backend.
    
    Args:
        create_backup: If True, create backup before migration
        
    Returns:
        Dictionary containing migration results
    """
    migration_manager = get_migration_manager()
    return migration_manager.migrate_json_to_sqlite(create_backup)

def verify_sync() -> Dict[str, Any]:
    """
    Verify that backends are synchronized.
    
    Returns:
        Dictionary containing verification results
    """
    sync_manager = get_sync_manager()
    return sync_manager.verify_sync()

def repair_sync() -> Dict[str, Any]:
    """
    Repair synchronization between backends.
    
    Returns:
        Dictionary containing repair results
    """
    migration_manager = get_migration_manager()
    return migration_manager.repair_sync()
