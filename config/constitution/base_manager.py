#!/usr/bin/env python3
"""
Abstract base class for Constitution Rule Managers.

This module defines the standard interface that all constitution rule managers
(SQLite, JSON, etc.) must implement for consistency across backends.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

class BaseConstitutionManager(ABC):
    """
    Abstract base class for constitution rule managers.
    
    This class defines the standard interface that all constitution rule
    managers must implement, ensuring consistency across different backends
    (SQLite, JSON, etc.).
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the constitution rule manager.
        
        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = config_dir
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the constitution rule manager.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_rule_enabled(self, rule_number: int) -> bool:
        """
        Check if a specific rule is enabled.
        
        Args:
            rule_number: The rule number to check
            
        Returns:
            True if rule is enabled, False otherwise
        """
        pass
    
    @abstractmethod
    def enable_rule(self, rule_number: int, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Enable a specific rule.
        
        Args:
            rule_number: The rule number to enable
            config_data: Optional configuration data for the rule
            
        Returns:
            True if rule was enabled successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def disable_rule(self, rule_number: int, reason: str = "") -> bool:
        """
        Disable a specific rule.
        
        Args:
            rule_number: The rule number to disable
            reason: Reason for disabling the rule
            
        Returns:
            True if rule was disabled successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_all_rules(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all rules from the database.
        
        Args:
            enabled_only: If True, return only enabled rules
            
        Returns:
            List of rule dictionaries
        """
        pass
    
    @abstractmethod
    def get_rule_by_number(self, rule_number: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific rule by its number.
        
        Args:
            rule_number: The rule number to retrieve
            
        Returns:
            Rule dictionary if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_rules_by_category(self, category: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get rules by category.
        
        Args:
            category: The category to filter by
            enabled_only: If True, return only enabled rules
            
        Returns:
            List of rule dictionaries in the specified category
        """
        pass
    
    @abstractmethod
    def get_rule_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about rules in the database.
        
        Returns:
            Dictionary containing rule statistics
        """
        pass
    
    @abstractmethod
    def search_rules(self, search_term: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Search rules by title or content.
        
        Args:
            search_term: The term to search for
            enabled_only: If True, search only enabled rules
            
        Returns:
            List of matching rule dictionaries
        """
        pass
    
    @abstractmethod
    def export_rules_to_json(self, enabled_only: bool = False) -> str:
        """
        Export rules to JSON format.
        
        Args:
            enabled_only: If True, export only enabled rules
            
        Returns:
            JSON string containing the rules
        """
        pass
    
    @abstractmethod
    def get_categories(self) -> Dict[str, Any]:
        """
        Get all available categories.
        
        Returns:
            Dictionary containing category information
        """
        pass
    
    @abstractmethod
    def get_backend_type(self) -> str:
        """
        Get the backend type (e.g., 'sqlite', 'json').
        
        Returns:
            Backend type string
        """
        pass
    
    @abstractmethod
    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get backend-specific information.
        
        Returns:
            Dictionary containing backend information
        """
        pass
    
    @abstractmethod
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path where to save the backup
            
        Returns:
            True if backup successful, False otherwise
        """
        pass
    
    @abstractmethod
    def restore_database(self, backup_path: str) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if restore successful, False otherwise
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database.
        
        Returns:
            Dictionary containing health check results
        """
        pass
    
    # Context manager support
    def __enter__(self):
        """Enter context manager."""
        if not self._initialized:
            self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.close()
    
    @abstractmethod
    def close(self):
        """Close the database connection."""
        pass
    
    # Utility methods
    def validate_rule_number(self, rule_number: int) -> bool:
        """
        Validate that a rule number is within valid range.
        
        Args:
            rule_number: The rule number to validate
            
        Returns:
            True if valid, False otherwise
        """
        return 1 <= rule_number <= 149
    
    def get_rule_summary(self, rule_number: int) -> Optional[Dict[str, Any]]:
        """
        Get a summary of a specific rule.
        
        Args:
            rule_number: The rule number to summarize
            
        Returns:
            Dictionary containing rule summary or None if not found
        """
        rule = self.get_rule_by_number(rule_number)
        if not rule:
            return None
        
        return {
            "rule_number": rule["rule_number"],
            "title": rule["title"],
            "category": rule["category"],
            "priority": rule["priority"],
            "enabled": rule.get("enabled", True),
            "content_preview": rule["content"][:100] + "..." if len(rule["content"]) > 100 else rule["content"]
        }
    
    def get_enabled_rules_count(self) -> int:
        """
        Get the count of enabled rules.
        
        Returns:
            Number of enabled rules
        """
        stats = self.get_rule_statistics()
        return stats.get("enabled_rules", 0)
    
    def get_disabled_rules_count(self) -> int:
        """
        Get the count of disabled rules.
        
        Returns:
            Number of disabled rules
        """
        stats = self.get_rule_statistics()
        return stats.get("disabled_rules", 0)
    
    def is_healthy(self) -> bool:
        """
        Check if the database is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            health = self.health_check()
            return health.get("healthy", False)
        except Exception:
            return False
    
    def get_last_updated(self) -> Optional[datetime]:
        """
        Get the last update timestamp.
        
        Returns:
            Last update datetime or None if not available
        """
        try:
            backend_info = self.get_backend_info()
            last_updated_str = backend_info.get("last_updated")
            if last_updated_str:
                return datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
        except Exception:
            pass
        return None
