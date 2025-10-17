#!/usr/bin/env python3
"""
JSON-based Constitution Rules Database for ZeroUI 2.0

This module provides a JSON file-based system to store and manage all 180
constitution rules with configuration management.
"""

import json
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConstitutionRulesJSON:
    """
    JSON-based constitution rules database.
    
    Features:
    - Store all rules in JSON format
    - Enable/disable rules via configuration
    - Query rules by category, priority, or status
    - Track rule usage and validation history
    - Maintain same structure as SQLite for consistency
    """
    
    def __init__(self, json_path: str = "config/constitution_rules.json"):
        """
        Initialize the JSON-based constitution rules database.
        
        Args:
            json_path: Path to JSON database file
        """
        self.json_path = Path(json_path)
        self.data = {}
        self._initialized = False
        self._lock_file = None
    
    def _init_database(self):
        """Initialize JSON database."""
        try:
            # Ensure directory exists
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.json_path.exists():
                self._load_database()
            else:
                self._create_database()
            
            self._initialized = True
            logger.info(f"JSON database initialized at {self.json_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize JSON database: {e}")
            raise
    
    def _load_database(self):
        """Load database from JSON file."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            # Validate database structure
            self._validate_database_structure()
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in database file: {e}")
            # Create backup and recreate database
            self._backup_corrupted_file()
            self._create_database()
        except Exception as e:
            logger.error(f"Failed to load JSON database: {e}")
            raise
    
    def _save_database(self):
        """Save database to JSON file."""
        try:
            # Validate data before saving
            self._validate_data_before_save()
            
            # Update metadata
            self.data["last_updated"] = datetime.now().isoformat()
            self.data["database_info"]["last_updated"] = datetime.now().isoformat()
            
            # Create temporary file for atomic write
            temp_path = self.json_path.with_suffix('.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            
            # Validate the written file
            self._validate_json_file(temp_path)
            
            # Atomic move
            temp_path.replace(self.json_path)
            
        except Exception as e:
            logger.error(f"Failed to save JSON database: {e}")
            # Clean up temp file if it exists
            if 'temp_path' in locals() and temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            raise
    
    def _validate_data_before_save(self):
        """Validate data structure before saving."""
        if not isinstance(self.data, dict):
            raise ValueError("Data must be a dictionary")
        
        required_keys = ["rules", "database_info", "categories"]
        for key in required_keys:
            if key not in self.data:
                raise ValueError(f"Missing required key: {key}")
        
        if not isinstance(self.data["rules"], dict):
            raise ValueError("Rules must be a dictionary")
        
        if len(self.data["rules"]) != 149:
            raise ValueError(f"Expected 149 rules, found {len(self.data['rules'])}")
    
    def _validate_json_file(self, file_path: Path):
        """Validate JSON file after writing."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Generated JSON file is invalid: {e}")
    
    def repair_corrupted_database(self) -> bool:
        """
        Attempt to repair a corrupted JSON database.
        
        Returns:
            True if repair was successful, False otherwise
        """
        try:
            if not self.json_path.exists():
                logger.info("No database file to repair")
                return True
            
            # Try to load the file
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # If we can load it, validate structure
                if self._validate_data_structure(data):
                    logger.info("Database file is valid, no repair needed")
                    return True
                else:
                    logger.warning("Database structure is invalid, recreating...")
                    self._backup_corrupted_file()
                    self._create_database()
                    return True
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                # Try to extract partial data
                if self._attempt_partial_recovery():
                    logger.info("Partial recovery successful")
                    return True
                else:
                    logger.error("Partial recovery failed, recreating database")
                    self._backup_corrupted_file()
                    self._create_database()
                    return True
                    
        except Exception as e:
            logger.error(f"Error during database repair: {e}")
            return False
    
    def _validate_data_structure(self, data: dict) -> bool:
        """Validate data structure without raising exceptions."""
        try:
            if not isinstance(data, dict):
                return False
            
            required_keys = ["rules", "database_info", "categories"]
            for key in required_keys:
                if key not in data:
                    return False
            
            if not isinstance(data["rules"], dict):
                return False
            
            if len(data["rules"]) != 149:
                return False
            
            return True
        except:
            return False
    
    def _attempt_partial_recovery(self) -> bool:
        """Attempt to recover partial data from corrupted file."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to find valid JSON sections
            # This is a basic attempt - in practice, you might need more sophisticated recovery
            if '"rules"' in content and '"database_info"' in content:
                logger.info("Found partial data, attempting to recreate database")
                self._backup_corrupted_file()
                self._create_database()
                return True
            
            return False
        except Exception as e:
            logger.error(f"Partial recovery failed: {e}")
            return False
    
    def _validate_database_structure(self):
        """Validate that the database has the expected structure."""
        required_keys = ["constitution_version", "total_rules", "rules", "categories", "statistics"]
        
        for key in required_keys:
            if key not in self.data:
                logger.warning(f"Missing required key '{key}' in database, recreating...")
                self._create_database()
                return
        
        # Validate rules count
        if len(self.data["rules"]) != 149:
            logger.warning(f"Expected 149 rules, found {len(self.data['rules'])}, recreating...")
            self._create_database()
    
    def _backup_corrupted_file(self):
        """Create backup of corrupted file."""
        if self.json_path.exists():
            # Create unique backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.json_path.with_suffix(f'.corrupted.backup.{timestamp}')
            
            # If the backup already exists, try with a counter
            counter = 1
            while backup_path.exists():
                backup_path = self.json_path.with_suffix(f'.corrupted.backup.{timestamp}.{counter}')
                counter += 1
            
            try:
                import shutil
                shutil.copy2(self.json_path, backup_path)
                logger.info(f"Corrupted database backed up to {backup_path}")
            except Exception as e:
                logger.error(f"Failed to backup corrupted file: {e}")
                # Try to remove the corrupted file if backup fails
                try:
                    self.json_path.unlink()
                    logger.info("Removed corrupted database file")
                except Exception as e2:
                    logger.error(f"Failed to remove corrupted file: {e2}")
    
    def _create_database(self):
        """Create new JSON database with all 180 rules."""
        try:
            from .rule_extractor import ConstitutionRuleExtractor
            
            extractor = ConstitutionRuleExtractor()
            rules_data = extractor.extract_all_rules()
            
            # Initialize database structure
            self.data = {
                "constitution_version": "2.0",
                "total_rules": 180,
                "last_updated": datetime.now().isoformat(),
                "database_info": {
                    "format": "json",
                    "schema_version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                },
                "categories": {},
                "rules": {},
                "statistics": {
                    "total_rules": 180,
                    "enabled_rules": 180,
                    "disabled_rules": 0,
                    "enabled_percentage": 100.0,
                    "category_counts": {},
                    "priority_counts": {}
                },
                "usage_history": [],
                "validation_history": []
            }
            
            # Add categories
            categories = self._get_categories_data()
            for category_data in categories:
                self.data["categories"][category_data["name"]] = {
                    "description": category_data["description"],
                    "priority": category_data["priority"],
                    "rule_count": category_data["rule_count"],
                    "rules": []
                }
            
            # Add rules
            for rule_data in rules_data:
                rule_number = str(rule_data['rule_number'])
                
                self.data["rules"][rule_number] = {
                    "rule_number": rule_data['rule_number'],
                    "title": rule_data['title'],
                    "category": rule_data['category'],
                    "priority": rule_data['priority'],
                    "content": rule_data['content'],
                    "enabled": True,  # All rules enabled by default
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
                        "last_used": None
                    }
                }
                
                # Add to category
                if rule_data['category'] in self.data["categories"]:
                    self.data["categories"][rule_data['category']]["rules"].append(rule_data['rule_number'])
            
            # Update statistics
            self._update_statistics()
            
            # Save database
            self._save_database()
            
            logger.info("Created new JSON database with all 180 rules")
            
        except Exception as e:
            logger.error(f"Failed to create JSON database: {e}")
            raise
    
    def _get_categories_data(self) -> List[Dict[str, Any]]:
        """Get category metadata."""
        return [
            {"name": "basic_work", "description": "Core principles for all development work", "priority": "critical", "rule_count": 18},
            {"name": "system_design", "description": "System architecture and design principles", "priority": "critical", "rule_count": 12},
            {"name": "problem_solving", "description": "Problem-solving methodologies and approaches", "priority": "critical", "rule_count": 9},
            {"name": "platform", "description": "Platform-specific rules and guidelines", "priority": "critical", "rule_count": 10},
            {"name": "teamwork", "description": "Collaboration and team dynamics", "priority": "critical", "rule_count": 26},
            {"name": "code_review", "description": "Code review processes and standards", "priority": "critical", "rule_count": 9},
            {"name": "coding_standards", "description": "Technical coding standards and best practices", "priority": "critical", "rule_count": 13},
            {"name": "comments", "description": "Documentation and commenting standards", "priority": "critical", "rule_count": 6},
            {"name": "api_contracts", "description": "API design, contracts, and governance", "priority": "critical", "rule_count": 11},
            {"name": "logging", "description": "Logging and troubleshooting standards", "priority": "critical", "rule_count": 17},
            {"name": "exception_handling", "description": "Exception handling, timeouts, retries, and error recovery", "priority": "critical", "rule_count": 31},
            {"name": "other", "description": "Miscellaneous rules", "priority": "important", "rule_count": 0}
        ]
    
    def _update_statistics(self):
        """Update database statistics."""
        total_rules = len(self.data["rules"])
        enabled_rules = sum(1 for rule in self.data["rules"].values() if rule["enabled"])
        disabled_rules = total_rules - enabled_rules
        
        # Category counts
        category_counts = {}
        for category_name, category_data in self.data["categories"].items():
            category_counts[category_name] = len(category_data["rules"])
        
        # Priority counts
        priority_counts = {}
        for rule in self.data["rules"].values():
            priority = rule["priority"]
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        self.data["statistics"] = {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "disabled_rules": disabled_rules,
            "enabled_percentage": (enabled_rules / total_rules * 100) if total_rules > 0 else 0,
            "category_counts": category_counts,
            "priority_counts": priority_counts
        }
    
    def get_all_rules(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """Get all rules from the database."""
        if not self._initialized:
            self._init_database()
        
        rules = []
        for rule_data in self.data["rules"].values():
            if not enabled_only or rule_data["enabled"]:
                rules.append(rule_data)
        
        return sorted(rules, key=lambda x: x["rule_number"])
    
    def get_rule_by_number(self, rule_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific rule by its number."""
        if not self._initialized:
            self._init_database()
        
        return self.data["rules"].get(str(rule_number))
    
    def get_rules_by_category(self, category: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """Get rules by category."""
        if not self._initialized:
            self._init_database()
        
        rules = []
        for rule_data in self.data["rules"].values():
            if rule_data["category"] == category and (not enabled_only or rule_data["enabled"]):
                rules.append(rule_data)
        
        return sorted(rules, key=lambda x: x["rule_number"])
    
    def enable_rule(self, rule_number: int, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """Enable a rule."""
        if not self._initialized:
            self._init_database()
        
        rule_key = str(rule_number)
        if rule_key in self.data["rules"]:
            self.data["rules"][rule_key]["enabled"] = True
            
            # Update config
            if config_data:
                self.data["rules"][rule_key]["config"].update(config_data)
            
            # Clear disable info
            self.data["rules"][rule_key]["config"]["disabled_reason"] = None
            self.data["rules"][rule_key]["config"]["disabled_at"] = None
            
            # Update metadata
            self.data["rules"][rule_key]["metadata"]["updated_at"] = datetime.now().isoformat()
            
            # Update statistics
            self._update_statistics()
            
            # Save database
            self._save_database()
            
            # Log usage
            self._log_usage(rule_number, "enabled", f"Config: {config_data}")
            
            return True
        return False
    
    def disable_rule(self, rule_number: int, reason: str = "") -> bool:
        """Disable a rule."""
        if not self._initialized:
            self._init_database()
        
        rule_key = str(rule_number)
        if rule_key in self.data["rules"]:
            self.data["rules"][rule_key]["enabled"] = False
            self.data["rules"][rule_key]["config"]["disabled_reason"] = reason
            self.data["rules"][rule_key]["config"]["disabled_at"] = datetime.now().isoformat()
            self.data["rules"][rule_key]["metadata"]["updated_at"] = datetime.now().isoformat()
            
            # Update statistics
            self._update_statistics()
            
            # Save database
            self._save_database()
            
            # Log usage
            self._log_usage(rule_number, "disabled", f"Reason: {reason}")
            
            return True
        return False
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about rules in the database."""
        if not self._initialized:
            self._init_database()
        
        return self.data["statistics"]
    
    def _log_usage(self, rule_number: int, action: str, context: str = ""):
        """Log rule usage for tracking."""
        usage_entry = {
            "rule_number": rule_number,
            "action": action,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        self.data["usage_history"].append(usage_entry)
        
        # Update rule usage count
        rule_key = str(rule_number)
        if rule_key in self.data["rules"]:
            self.data["rules"][rule_key]["metadata"]["usage_count"] += 1
            self.data["rules"][rule_key]["metadata"]["last_used"] = datetime.now().isoformat()
    
    def export_rules_to_json(self, enabled_only: bool = False) -> str:
        """Export rules to JSON format."""
        if not self._initialized:
            self._init_database()
        
        rules = self.get_all_rules(enabled_only=enabled_only)
        return json.dumps(rules, indent=2, ensure_ascii=False)
    
    def search_rules(self, search_term: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """Search rules by title or content."""
        if not self._initialized:
            self._init_database()
        
        results = []
        search_lower = search_term.lower()
        
        for rule_data in self.data["rules"].values():
            if enabled_only and not rule_data["enabled"]:
                continue
                
            if (search_lower in rule_data["title"].lower() or 
                search_lower in rule_data["content"].lower()):
                results.append(rule_data)
        
        return sorted(results, key=lambda x: x["rule_number"])
    
    def get_categories(self) -> Dict[str, Any]:
        """Get all categories."""
        if not self._initialized:
            self._init_database()
        
        return self.data["categories"]
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            if not self._initialized:
                self._init_database()
            
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup."""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            # Validate restored data
            self._validate_database_structure()
            
            # Save restored database
            self._save_database()
            
            logger.info(f"Database restored from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the database."""
        try:
            if not self._initialized:
                self._init_database()
            
            # Check file existence and readability
            file_exists = self.json_path.exists()
            file_readable = False
            file_writable = False
            
            if file_exists:
                try:
                    with open(self.json_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    file_readable = True
                except:
                    pass
                
                try:
                    with open(self.json_path, 'w', encoding='utf-8') as f:
                        pass
                    file_writable = True
                except:
                    pass
            
            # Check data integrity
            data_valid = True
            try:
                self._validate_database_structure()
            except:
                data_valid = False
            
            # Check rule count
            expected_rules = 149
            actual_rules = len(self.data.get("rules", {}))
            rules_count_valid = actual_rules == expected_rules
            
            healthy = file_exists and file_readable and file_writable and data_valid and rules_count_valid
            
            return {
                "healthy": healthy,
                "file_exists": file_exists,
                "file_readable": file_readable,
                "file_writable": file_writable,
                "data_valid": data_valid,
                "rules_count_valid": rules_count_valid,
                "expected_rules": expected_rules,
                "actual_rules": actual_rules,
                "last_updated": self.data.get("last_updated"),
                "database_version": self.data.get("constitution_version")
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get backend-specific information."""
        if not self._initialized:
            self._init_database()
        
        return {
            "backend_type": "json",
            "file_path": str(self.json_path),
            "file_size": self.json_path.stat().st_size if self.json_path.exists() else 0,
            "last_updated": self.data.get("last_updated"),
            "database_version": self.data.get("constitution_version"),
            "schema_version": self.data.get("database_info", {}).get("schema_version"),
            "created_at": self.data.get("database_info", {}).get("created_at")
        }
    
    def close(self):
        """Close the database connection."""
        # JSON doesn't need explicit closing, but we can clean up
        self._initialized = False
        logger.info("JSON database connection closed")
    
    # Context manager support
    def __enter__(self):
        """Enter context manager."""
        if not self._initialized:
            self._init_database()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.close()
