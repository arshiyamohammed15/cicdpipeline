#!/usr/bin/env python3
"""
Synchronization Manager for Constitution Rules Database

This module provides synchronization capabilities between SQLite and JSON
backends to keep both databases in sync.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from .config_manager import ConstitutionRuleManager
from .config_manager_json import ConstitutionRuleManagerJSON
from .backend_factory import get_backend_factory
from .rule_extractor import ConstitutionRuleExtractor

logger = logging.getLogger(__name__)

class ConstitutionSyncManager:
    """
    Manages synchronization between SQLite and JSON backends.
    
    Features:
    - Bidirectional sync between backends
    - Conflict detection and resolution
    - Automatic sync on changes
    - Sync history tracking
    - Data integrity verification
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the sync manager.
        
        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = config_dir
        self.sync_history_path = Path(config_dir) / "sync_history.json"
        self._sync_history = []
        self._load_sync_history()
    
    def _load_sync_history(self):
        """Load sync history from file."""
        try:
            if self.sync_history_path.exists():
                with open(self.sync_history_path, 'r', encoding='utf-8') as f:
                    self._sync_history = json.load(f)
                
                # Validate sync history structure
                if not isinstance(self._sync_history, list):
                    logger.warning("Invalid sync history format, resetting")
                    self._sync_history = []
            else:
                self._sync_history = []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in sync history file: {e}")
            # Create backup and reset
            self._backup_corrupted_sync_history()
            self._sync_history = []
        except Exception as e:
            logger.error(f"Failed to load sync history: {e}")
            self._sync_history = []
    
    def _backup_corrupted_sync_history(self):
        """Backup corrupted sync history file."""
        try:
            if self.sync_history_path.exists():
                backup_path = self.sync_history_path.with_suffix('.corrupted.backup')
                import shutil
                shutil.copy2(self.sync_history_path, backup_path)
                logger.info(f"Corrupted sync history backed up to {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup corrupted sync history: {e}")
    
    def _save_sync_history(self):
        """Save sync history to file."""
        try:
            self.sync_history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.sync_history_path, 'w', encoding='utf-8') as f:
                json.dump(self._sync_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save sync history: {e}")
    
    def _log_sync_operation(self, operation: str, source: str, target: str, 
                           success: bool, details: str = ""):
        """Log a sync operation."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "source": source,
            "target": target,
            "success": success,
            "details": details
        }
        self._sync_history.append(entry)
        
        # Keep only last 100 entries
        if len(self._sync_history) > 100:
            self._sync_history = self._sync_history[-100:]
        
        self._save_sync_history()
    
    def sync_sqlite_to_json(self, force: bool = False) -> Dict[str, Any]:
        """
        Synchronize data from SQLite to JSON backend.
        
        Args:
            force: If True, force sync even if data appears unchanged
            
        Returns:
            Dictionary containing sync results
        """
        try:
            logger.info("Starting SQLite to JSON sync")
            
            # Get managers
            sqlite_manager = ConstitutionRuleManager(config_dir=self.config_dir)
            json_manager = ConstitutionRuleManagerJSON(config_dir=self.config_dir)
            
            # Get all rules from SQLite
            sqlite_rules = sqlite_manager.get_all_rules()
            
            # Check if sync is needed
            if not force and self._is_sync_needed(sqlite_manager, json_manager, "sqlite_to_json"):
                logger.info("Sync not needed - data is already up to date")
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "Data already synchronized"
                }
            
            # Update JSON database
            changes_made = 0
            
            for rule in sqlite_rules:
                rule_number = rule["rule_number"]
                json_rule = json_manager.get_rule_by_number(rule_number)
                
                # Check if rule needs updating
                if not json_rule or self._rules_differ(rule, json_rule):
                    # Update rule in JSON
                    if json_rule:
                        # Update existing rule
                        json_manager.json_manager.data["rules"][str(rule_number)].update({
                            "title": rule["title"],
                            "category": rule["category"],
                            "priority": rule["priority"],
                            "content": rule["content"],
                            "enabled": rule["enabled"],
                            "metadata": {
                                **json_rule.get("metadata", {}),
                                "updated_at": datetime.now().isoformat(),
                                "synced_from": "sqlite"
                            }
                        })
                    else:
                        # Add new rule
                        json_manager.json_manager.data["rules"][str(rule_number)] = {
                            "rule_number": rule["rule_number"],
                            "title": rule["title"],
                            "category": rule["category"],
                            "priority": rule["priority"],
                            "content": rule["content"],
                            "enabled": rule["enabled"],
                            "config": {
                                "default_enabled": True,
                                "notes": "",
                                "disabled_reason": None,
                                "disabled_at": None
                            },
                            "metadata": {
                                "created_at": datetime.now().isoformat(),
                                "updated_at": datetime.now().isoformat(),
                                "usage_count": 0,
                                "last_used": None,
                                "synced_from": "sqlite"
                            }
                        }
                    
                    changes_made += 1
            
            # Update JSON database statistics and save
            json_manager.json_manager._update_statistics()
            json_manager.json_manager._save_database()
            
            # Update JSON configuration
            json_manager._sync_with_database()
            
            # Log successful sync
            self._log_sync_operation(
                "sqlite_to_json", "sqlite", "json", True,
                f"Updated {changes_made} rules"
            )
            
            logger.info(f"SQLite to JSON sync completed successfully. Updated {changes_made} rules.")
            
            return {
                "success": True,
                "changes_made": changes_made,
                "rules_updated": changes_made
            }
            
        except Exception as e:
            logger.error(f"SQLite to JSON sync failed: {e}")
            self._log_sync_operation(
                "sqlite_to_json", "sqlite", "json", False, str(e)
            )
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            try:
                sqlite_manager.close()
                json_manager.close()
            except:
                pass
    
    def sync_json_to_sqlite(self, force: bool = False) -> Dict[str, Any]:
        """
        Synchronize data from JSON to SQLite backend.
        
        Args:
            force: If True, force sync even if data appears unchanged
            
        Returns:
            Dictionary containing sync results
        """
        try:
            logger.info("Starting JSON to SQLite sync")
            
            # Get managers
            json_manager = ConstitutionRuleManagerJSON(config_dir=self.config_dir)
            sqlite_manager = ConstitutionRuleManager(config_dir=self.config_dir)
            
            # Get all rules from JSON
            json_rules = json_manager.get_all_rules()
            
            # Check if sync is needed
            if not force and self._is_sync_needed(json_manager, sqlite_manager, "json_to_sqlite"):
                logger.info("Sync not needed - data is already up to date")
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "Data already synchronized"
                }
            
            # Update SQLite database
            changes_made = 0
            
            for rule in json_rules:
                rule_number = rule["rule_number"]
                sqlite_rule = sqlite_manager.get_rule_by_number(rule_number)
                
                # Check if rule needs updating
                if not sqlite_rule or self._rules_differ(rule, sqlite_rule):
                    # Update rule in SQLite
                    if sqlite_rule:
                        # Update existing rule
                        sqlite_manager.db_manager.update_rule(
                            rule_number,
                            rule["title"],
                            rule["category"],
                            rule["priority"],
                            rule["content"],
                            rule["enabled"]
                        )
                    else:
                        # Add new rule
                        sqlite_manager.db_manager.insert_rule(
                            rule_number,
                            rule["title"],
                            rule["category"],
                            rule["priority"],
                            rule["content"],
                            rule["enabled"]
                        )
                    
                    changes_made += 1
            
            # Log successful sync
            self._log_sync_operation(
                "json_to_sqlite", "json", "sqlite", True,
                f"Updated {changes_made} rules"
            )
            
            logger.info(f"JSON to SQLite sync completed successfully. Updated {changes_made} rules.")
            
            return {
                "success": True,
                "changes_made": changes_made,
                "rules_updated": changes_made
            }
            
        except Exception as e:
            logger.error(f"JSON to SQLite sync failed: {e}")
            self._log_sync_operation(
                "json_to_sqlite", "json", "sqlite", False, str(e)
            )
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            try:
                json_manager.close()
                sqlite_manager.close()
            except:
                pass
    
    def auto_sync(self, force: bool = False) -> Dict[str, Any]:
        """
        Perform automatic bidirectional sync.
        
        Args:
            force: If True, force sync even if data appears unchanged
            
        Returns:
            Dictionary containing sync results
        """
        try:
            logger.info("Starting automatic bidirectional sync")
            
            # Get configuration to determine primary backend
            factory = get_backend_factory()
            config = factory._get_configuration()
            primary_backend = config.get("backend", "sqlite")
            
            results = {
                "success": True,
                "primary_backend": primary_backend,
                "syncs": {}
            }
            
            # Sync from primary to fallback
            if primary_backend == "sqlite":
                results["syncs"]["sqlite_to_json"] = self.sync_sqlite_to_json(force)
            else:
                results["syncs"]["json_to_sqlite"] = self.sync_json_to_sqlite(force)
            
            # Check for conflicts and resolve
            conflicts = self._detect_conflicts()
            if conflicts:
                logger.warning(f"Detected {len(conflicts)} conflicts during sync")
                results["conflicts"] = conflicts
                results["conflicts_resolved"] = self._resolve_conflicts(conflicts, primary_backend)
            
            # Verify sync integrity
            integrity_check = self.verify_sync()
            results["integrity_check"] = integrity_check
            
            if not integrity_check["synchronized"]:
                logger.warning("Sync integrity check failed")
                results["success"] = False
                results["error"] = "Sync integrity check failed"
            
            logger.info("Automatic bidirectional sync completed")
            return results
            
        except Exception as e:
            logger.error(f"Automatic sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_sync_needed(self, source_manager, target_manager, direction: str) -> bool:
        """
        Check if sync is needed between two managers.
        
        Args:
            source_manager: Source manager instance
            target_manager: Target manager instance
            direction: Sync direction for logging
            
        Returns:
            True if sync is needed, False otherwise
        """
        try:
            # Get last update times
            source_info = source_manager.get_backend_info()
            target_info = target_manager.get_backend_info()
            
            source_updated = source_info.get("last_updated")
            target_updated = target_info.get("last_updated")
            
            if not source_updated or not target_updated:
                return True  # Sync if we can't determine timestamps
            
            # Parse timestamps
            source_time = datetime.fromisoformat(source_updated.replace('Z', '+00:00'))
            target_time = datetime.fromisoformat(target_updated.replace('Z', '+00:00'))
            
            # Sync if source is newer than target
            return source_time > target_time
            
        except Exception as e:
            logger.debug(f"Could not determine if sync needed: {e}")
            return True  # Default to sync if we can't determine
    
    def _rules_differ(self, rule1: Dict[str, Any], rule2: Dict[str, Any]) -> bool:
        """
        Check if two rules differ in important fields.
        
        Args:
            rule1: First rule
            rule2: Second rule
            
        Returns:
            True if rules differ, False otherwise
        """
        # Compare important fields
        important_fields = ["title", "category", "priority", "content", "enabled"]
        
        for field in important_fields:
            if rule1.get(field) != rule2.get(field):
                return True
        
        return False
    
    def _detect_conflicts(self) -> List[Dict[str, Any]]:
        """
        Detect conflicts between backends.
        
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        
        try:
            # Get managers
            sqlite_manager = ConstitutionRuleManager(config_dir=self.config_dir)
            json_manager = ConstitutionRuleManagerJSON(config_dir=self.config_dir)
            
            # Get all rules from both backends
            sqlite_rules = {rule["rule_number"]: rule for rule in sqlite_manager.get_all_rules()}
            json_rules = {rule["rule_number"]: rule for rule in json_manager.get_all_rules()}
            
            # Check for conflicts
            all_rule_numbers = set(sqlite_rules.keys()) | set(json_rules.keys())
            
            for rule_number in all_rule_numbers:
                sqlite_rule = sqlite_rules.get(rule_number)
                json_rule = json_rules.get(rule_number)
                
                if sqlite_rule and json_rule:
                    # Both exist - check for differences
                    if self._rules_differ(sqlite_rule, json_rule):
                        conflicts.append({
                            "rule_number": rule_number,
                            "type": "data_conflict",
                            "sqlite_data": sqlite_rule,
                            "json_data": json_rule
                        })
                elif sqlite_rule and not json_rule:
                    # Only in SQLite
                    conflicts.append({
                        "rule_number": rule_number,
                        "type": "missing_in_json",
                        "sqlite_data": sqlite_rule
                    })
                elif json_rule and not sqlite_rule:
                    # Only in JSON
                    conflicts.append({
                        "rule_number": rule_number,
                        "type": "missing_in_sqlite",
                        "json_data": json_rule
                    })
            
        except Exception as e:
            logger.error(f"Failed to detect conflicts: {e}")
        
        finally:
            try:
                sqlite_manager.close()
                json_manager.close()
            except:
                pass
        
        return conflicts
    
    def _resolve_conflicts(self, conflicts: List[Dict[str, Any]], primary_backend: str) -> Dict[str, Any]:
        """
        Resolve conflicts using primary backend as source of truth.
        
        Args:
            conflicts: List of conflicts to resolve
            primary_backend: Primary backend to use for resolution
            
        Returns:
            Dictionary containing resolution results
        """
        resolved = 0
        failed = 0
        
        try:
            for conflict in conflicts:
                try:
                    if primary_backend == "sqlite":
                        # Use SQLite as source of truth
                        if conflict["type"] == "missing_in_json":
                            # Add to JSON
                            self._add_rule_to_json(conflict["sqlite_data"])
                        elif conflict["type"] == "missing_in_sqlite":
                            # Remove from JSON (or update SQLite)
                            self._remove_rule_from_json(conflict["rule_number"])
                        elif conflict["type"] == "data_conflict":
                            # Update JSON with SQLite data
                            self._update_rule_in_json(conflict["sqlite_data"])
                    else:
                        # Use JSON as source of truth
                        if conflict["type"] == "missing_in_sqlite":
                            # Add to SQLite
                            self._add_rule_to_sqlite(conflict["json_data"])
                        elif conflict["type"] == "missing_in_json":
                            # Remove from SQLite (or update JSON)
                            self._remove_rule_from_sqlite(conflict["rule_number"])
                        elif conflict["type"] == "data_conflict":
                            # Update SQLite with JSON data
                            self._update_rule_in_sqlite(conflict["json_data"])
                    
                    resolved += 1
                    
                except Exception as e:
                    logger.error(f"Failed to resolve conflict for rule {conflict['rule_number']}: {e}")
                    failed += 1
            
        except Exception as e:
            logger.error(f"Failed to resolve conflicts: {e}")
        
        return {
            "resolved": resolved,
            "failed": failed,
            "total": len(conflicts)
        }
    
    def _add_rule_to_json(self, rule_data: Dict[str, Any]):
        """Add rule to JSON backend."""
        json_manager = ConstitutionRuleManagerJSON(config_dir=self.config_dir)
        try:
            json_manager.json_manager.data["rules"][str(rule_data["rule_number"])] = rule_data
            json_manager.json_manager._update_statistics()
            json_manager.json_manager._save_database()
        finally:
            json_manager.close()
    
    def _add_rule_to_sqlite(self, rule_data: Dict[str, Any]):
        """Add rule to SQLite backend."""
        sqlite_manager = ConstitutionRuleManager(config_dir=self.config_dir)
        try:
            sqlite_manager.db_manager.insert_rule(
                rule_data["rule_number"],
                rule_data["title"],
                rule_data["category"],
                rule_data["priority"],
                rule_data["content"],
                rule_data["enabled"]
            )
        finally:
            sqlite_manager.close()
    
    def _update_rule_in_json(self, rule_data: Dict[str, Any]):
        """Update rule in JSON backend."""
        json_manager = ConstitutionRuleManagerJSON(config_dir=self.config_dir)
        try:
            rule_number = str(rule_data["rule_number"])
            if rule_number in json_manager.json_manager.data["rules"]:
                json_manager.json_manager.data["rules"][rule_number].update(rule_data)
                json_manager.json_manager._save_database()
        finally:
            json_manager.close()
    
    def _update_rule_in_sqlite(self, rule_data: Dict[str, Any]):
        """Update rule in SQLite backend."""
        sqlite_manager = ConstitutionRuleManager(config_dir=self.config_dir)
        try:
            sqlite_manager.db_manager.update_rule(
                rule_data["rule_number"],
                rule_data["title"],
                rule_data["category"],
                rule_data["priority"],
                rule_data["content"],
                rule_data["enabled"]
            )
        finally:
            sqlite_manager.close()
    
    def _remove_rule_from_json(self, rule_number: int):
        """Remove rule from JSON backend."""
        json_manager = ConstitutionRuleManagerJSON(config_dir=self.config_dir)
        try:
            rule_key = str(rule_number)
            if rule_key in json_manager.json_manager.data["rules"]:
                del json_manager.json_manager.data["rules"][rule_key]
                json_manager.json_manager._update_statistics()
                json_manager.json_manager._save_database()
        finally:
            json_manager.close()
    
    def _remove_rule_from_sqlite(self, rule_number: int):
        """Remove rule from SQLite backend."""
        sqlite_manager = ConstitutionRuleManager(config_dir=self.config_dir)
        try:
            sqlite_manager.db_manager.delete_rule(rule_number)
        finally:
            sqlite_manager.close()
    
    def verify_sync(self) -> Dict[str, Any]:
        """
        Verify that both backends are synchronized.
        
        Returns:
            Dictionary containing verification results
        """
        try:
            # Get managers
            sqlite_manager = ConstitutionRuleManager(config_dir=self.config_dir)
            json_manager = ConstitutionRuleManagerJSON(config_dir=self.config_dir)
            
            # Get all rules from both backends
            sqlite_rules = {rule["rule_number"]: rule for rule in sqlite_manager.get_all_rules()}
            json_rules = {rule["rule_number"]: rule for rule in json_manager.get_all_rules()}
            
            # Check synchronization
            synchronized = True
            differences = []
            
            all_rule_numbers = set(sqlite_rules.keys()) | set(json_rules.keys())
            
            for rule_number in all_rule_numbers:
                sqlite_rule = sqlite_rules.get(rule_number)
                json_rule = json_rules.get(rule_number)
                
                if not sqlite_rule or not json_rule:
                    synchronized = False
                    differences.append({
                        "rule_number": rule_number,
                        "issue": "missing_in_one_backend",
                        "sqlite_exists": sqlite_rule is not None,
                        "json_exists": json_rule is not None
                    })
                elif self._rules_differ(sqlite_rule, json_rule):
                    synchronized = False
                    differences.append({
                        "rule_number": rule_number,
                        "issue": "data_difference",
                        "sqlite_data": sqlite_rule,
                        "json_data": json_rule
                    })
            
            return {
                "synchronized": synchronized,
                "total_rules": len(all_rule_numbers),
                "sqlite_rules": len(sqlite_rules),
                "json_rules": len(json_rules),
                "differences": differences,
                "difference_count": len(differences)
            }
            
        except Exception as e:
            logger.error(f"Failed to verify sync: {e}")
            return {
                "synchronized": False,
                "error": str(e)
            }
        finally:
            try:
                sqlite_manager.close()
                json_manager.close()
            except:
                pass
    
    def get_sync_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get sync history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of sync history entries
        """
        return self._sync_history[-limit:] if limit > 0 else self._sync_history
    
    def clear_sync_history(self):
        """Clear sync history."""
        self._sync_history = []
        self._save_sync_history()
        logger.info("Sync history cleared")

    def verify_consistency_across_sources(self) -> Dict[str, Any]:
        """
        Validate rules consistency across Markdown, SQLite DB, JSON export, and config.

        Returns:
            Summary including per-rule differences and aggregate counts.
        """
        results: Dict[str, Any] = {
            "consistent": True,
            "summary": {},
            "differences": []
        }

        try:
            # Load sources
            # 1) Markdown via extractor
            constitution_file_path = "docs/architecture/ZeroUI2.0_Master_Constitution.md"
            md_extractor = ConstitutionRuleExtractor(constitution_file_path)
            md_rules_list = md_extractor.extract_all_rules()
            md_rules = {r["rule_number"]: r for r in md_rules_list}

            # 2) Database via manager
            sqlite_manager = ConstitutionRuleManager(config_dir=self.config_dir)
            db_rules_list = sqlite_manager.get_all_rules()
            db_rules = {r["rule_number"]: r for r in db_rules_list}

            # 3) JSON export file (supports array export or JSON-DB object)
            json_export_path = Path(self.config_dir) / "constitution_rules.json"
            json_export_rules: Dict[int, Dict[str, Any]] = {}
            if json_export_path.exists():
                with open(json_export_path, 'r', encoding='utf-8') as f:
                    try:
                        parsed = json.load(f)
                        if isinstance(parsed, list):
                            for item in parsed:
                                rn = int(item.get("rule_number")) if item.get("rule_number") is not None else None
                                if rn:
                                    json_export_rules[rn] = item
                        elif isinstance(parsed, dict) and "rules" in parsed:
                            # JSON DB shape: rules is a dict keyed by string rule_number
                            for key, item in parsed.get("rules", {}).items():
                                try:
                                    rn = int(item.get("rule_number") or key)
                                    json_export_rules[rn] = item
                                except Exception:
                                    continue
                        else:
                            # Unknown shape; leave empty but note in summary
                            results.setdefault("warnings", []).append("Unrecognized constitution_rules.json structure")
                    except json.JSONDecodeError:
                        results.setdefault("warnings", []).append("constitution_rules.json is not valid JSON")
            else:
                results.setdefault("warnings", []).append("constitution_rules.json not found")

            # 4) Config enabled states
            config_path = Path(self.config_dir) / "constitution_config.json"
            config_enabled: Dict[int, Optional[bool]] = {}
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                        rules_cfg = cfg.get("rules", {}) or {}
                        for k, v in rules_cfg.items():
                            try:
                                rn = int(k)
                                config_enabled[rn] = v.get("enabled")
                            except Exception:
                                continue
                except Exception:
                    results.setdefault("warnings", []).append("Failed to read constitution_config.json")
            else:
                results.setdefault("warnings", []).append("constitution_config.json not found")

            # Field comparison helpers
            def norm_text(s: Any) -> str:
                # Normalize by stripping, collapsing whitespace, and lowering case
                if s is None:
                    return ""
                text = str(s)
                # Replace multiple whitespace with single space and trim
                import re as _re
                text = _re.sub(r"\s+", " ", text).strip()
                return text

            def collect_fields(src: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "title": src.get("title"),
                    "category": src.get("category"),
                    "priority": src.get("priority"),
                    "content": src.get("content"),
                    "enabled": src.get("enabled") if "enabled" in src else None
                }

            # Build universe of rules
            all_rule_numbers = sorted(set(md_rules.keys()) | set(db_rules.keys()) | set(json_export_rules.keys()) | set(config_enabled.keys()))

            missing_counts = {"markdown": 0, "database": 0, "json_export": 0, "config": 0}
            field_mismatch_count = 0
            enabled_mismatch_count = 0

            for rn in all_rule_numbers:
                md = md_rules.get(rn)
                db = db_rules.get(rn)
                jexp = json_export_rules.get(rn)
                cfg_enabled = config_enabled.get(rn, None)

                present = {
                    "markdown": md is not None,
                    "database": db is not None,
                    "json_export": jexp is not None,
                    "config": cfg_enabled is not None
                }

                for key, is_present in present.items():
                    if not is_present:
                        missing_counts[key] += 1

                # Compare fields when present in multiple sources (require quorum to avoid false positives)
                mismatch_fields: List[str] = []
                ref = None
                # Prefer DB as reference if present, else Markdown
                if db:
                    ref = collect_fields(db)
                elif md:
                    ref = collect_fields(md)

                if ref:
                    candidates = []
                    if md:
                        candidates.append(("markdown", collect_fields(md)))
                    if db:
                        candidates.append(("database", collect_fields(db)))
                    if jexp:
                        candidates.append(("json_export", collect_fields(jexp)))

                    # Only evaluate mismatches if at least two sources provide the field
                    for f in ["title", "category", "priority", "content"]:
                        values = []
                        for _, fields in candidates:
                            val = fields.get(f)
                            if val is not None and str(val).strip() != "":
                                values.append(norm_text(val))
                        # If fewer than 2 values, skip to avoid false positives
                        if len(values) >= 2 and len(set(values)) > 1:
                            if f not in mismatch_fields:
                                mismatch_fields.append(f)

                # Enabled mismatches between DB/JSON export/config
                db_enabled = db.get("enabled") if db else None
                j_enabled = jexp.get("enabled") if jexp else None
                # Some JSON export formats store enabled under config_data or config
                if j_enabled is None and jexp is not None:
                    je_cfg = jexp.get("config_data") or jexp.get("config") or {}
                    if isinstance(je_cfg, dict):
                        j_enabled = je_cfg.get("default_enabled") if "default_enabled" in je_cfg else je_cfg.get("enabled")

                enabled_sources = [("database", db_enabled), ("json_export", j_enabled), ("config", cfg_enabled)]
                enabled_values = [v for (_, v) in enabled_sources if v is not None]
                # Require quorum of at least 2 sources to consider enabled mismatch
                enabled_diff = len(enabled_values) >= 2 and len(set(enabled_values)) > 1

                if mismatch_fields or enabled_diff or not all(present.values()):
                    results["consistent"] = False
                    if mismatch_fields:
                        field_mismatch_count += 1
                    if enabled_diff:
                        enabled_mismatch_count += 1
                    
                    # Capture actual field values for detailed reporting
                    field_details = {}
                    for field in mismatch_fields:
                        field_details[field] = {}
                        if md:
                            field_details[field]["markdown"] = str(md.get(field, ""))[:200]
                        if db:
                            field_details[field]["database"] = str(db.get(field, ""))[:200]
                        if jexp:
                            field_details[field]["json_export"] = str(jexp.get(field, ""))[:200]
                    
                    results["differences"].append({
                        "rule_number": rn,
                        "missing": {k: (not v) for k, v in present.items()},
                        "field_mismatches": mismatch_fields,
                        "field_details": field_details,
                        "enabled": {k: v for (k, v) in enabled_sources}
                    })

            # Build summary
            results["summary"] = {
                "total_rules_observed": len(all_rule_numbers),
                "missing": missing_counts,
                "field_mismatch_rules": field_mismatch_count,
                "enabled_mismatch_rules": enabled_mismatch_count,
                "differences_count": len(results["differences"]) 
            }

            return results
        except Exception as e:
            logger.error(f"Failed to verify consistency across sources: {e}")
            return {"consistent": False, "error": str(e), "differences": []}

# Global sync manager instance
_sync_manager_instance = None

def get_sync_manager() -> ConstitutionSyncManager:
    """
    Get the global sync manager instance.
    
    Returns:
        Sync manager instance
    """
    global _sync_manager_instance
    
    if _sync_manager_instance is None:
        _sync_manager_instance = ConstitutionSyncManager()
    
    return _sync_manager_instance

def sync_backends(force: bool = False) -> Dict[str, Any]:
    """
    Synchronize backends.
    
    Args:
        force: If True, force sync even if data appears unchanged
        
    Returns:
        Dictionary containing sync results
    """
    sync_manager = get_sync_manager()
    return sync_manager.auto_sync(force)

def verify_sync() -> Dict[str, Any]:
    """
    Verify that backends are synchronized.
    
    Returns:
        Dictionary containing verification results
    """
    sync_manager = get_sync_manager()
    return sync_manager.verify_sync()
