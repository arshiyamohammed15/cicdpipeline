#!/usr/bin/env python3
"""
Enhanced configuration manager for modular rule system.

This manager loads configurations on-demand and provides caching for better performance.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache

class EnhancedConfigManager:
    """
    Enhanced configuration manager with modular loading and caching.
    
    This manager loads base configuration and rule configurations on-demand,
    providing better performance and maintainability.
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the enhanced configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self._base_config = None
        self._rule_configs = {}
        self._pattern_configs = {}
        self._cache = {}
    
    @property
    def base_config(self) -> Dict[str, Any]:
        """Get the base configuration."""
        if self._base_config is None:
            self._base_config = self._load_base_config()
        return self._base_config
    
    def _load_base_config(self) -> Dict[str, Any]:
        """Load the base configuration file."""
        base_config_path = self.config_dir / "base_config.json"
        if not base_config_path.exists():
            raise FileNotFoundError(f"Base configuration not found: {base_config_path}")
        
        with open(base_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @lru_cache(maxsize=32)
    def get_rule_config(self, category: str) -> Dict[str, Any]:
        """
        Get rule configuration for a specific category.
        
        Args:
            category: Rule category name
            
        Returns:
            Rule configuration dictionary
        """
        if category not in self._rule_configs:
            self._rule_configs[category] = self._load_rule_config(category)
        return self._rule_configs[category]
    
    def _load_rule_config(self, category: str) -> Dict[str, Any]:
        """Load rule configuration for a category."""
        rule_config_path = self.config_dir / "rules" / f"{category}.json"
        if not rule_config_path.exists():
            return {
                "category": category,
                "priority": "unknown",
                "description": f"Configuration for {category}",
                "rules": []
            }
        
        with open(rule_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @lru_cache(maxsize=32)
    def get_pattern_config(self, category: str) -> Dict[str, Any]:
        """
        Get pattern configuration for a specific category.
        
        Args:
            category: Rule category name
            
        Returns:
            Pattern configuration dictionary
        """
        if category not in self._pattern_configs:
            self._pattern_configs[category] = self._load_pattern_config(category)
        return self._pattern_configs[category]
    
    def _load_pattern_config(self, category: str) -> Dict[str, Any]:
        """Load pattern configuration for a category."""
        pattern_config_path = self.config_dir / "patterns" / f"{category}_patterns.json"
        if not pattern_config_path.exists():
            return {
                "category": category,
                "patterns": {}
            }
        
        with open(pattern_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_all_categories(self) -> List[str]:
        """Get list of all available rule categories."""
        rules_dir = self.config_dir / "rules"
        if not rules_dir.exists():
            return []
        
        categories = []
        for config_file in rules_dir.glob("*.json"):
            category = config_file.stem
            categories.append(category)
        
        return sorted(categories)
    
    def get_rules_for_category(self, category: str) -> List[int]:
        """
        Get list of rule numbers for a category.
        
        Args:
            category: Rule category name
            
        Returns:
            List of rule numbers
        """
        rule_config = self.get_rule_config(category)
        return rule_config.get("rules", [])
    
    def get_category_priority(self, category: str) -> str:
        """
        Get priority level for a category.
        
        Args:
            category: Rule category name
            
        Returns:
            Priority level (critical, important, recommended)
        """
        rule_config = self.get_rule_config(category)
        return rule_config.get("priority", "unknown")
    
    def get_enterprise_rules(self, priority: str = "critical") -> List[int]:
        """
        Get enterprise rules by priority.
        
        Args:
            priority: Priority level (critical, important, recommended)
            
        Returns:
            List of rule numbers
        """
        base_config = self.base_config
        key = f"enterprise_{priority}_rules"
        return base_config.get(key, [])
    
    def is_enterprise_rule(self, rule_number: int, priority: str = "critical") -> bool:
        """
        Check if a rule is an enterprise rule.
        
        Args:
            rule_number: Rule number to check
            priority: Priority level to check
            
        Returns:
            True if rule is enterprise rule
        """
        enterprise_rules = self.get_enterprise_rules(priority)
        return rule_number in enterprise_rules
    
    def get_performance_targets(self) -> Dict[str, float]:
        """Get performance targets from base configuration."""
        base_config = self.base_config
        return base_config.get("performance_targets", {})
    
    def get_severity_config(self, severity: str) -> Dict[str, Any]:
        """
        Get configuration for a severity level.
        
        Args:
            severity: Severity level (error, warning, info)
            
        Returns:
            Severity configuration dictionary
        """
        base_config = self.base_config
        severity_levels = base_config.get("severity_levels", {})
        return severity_levels.get(severity, {})
    
    def reload_config(self, category: Optional[str] = None):
        """
        Reload configuration for a category or all categories.
        
        Args:
            category: Specific category to reload, or None for all
        """
        if category is None:
            # Reload all configurations
            self._base_config = None
            self._rule_configs.clear()
            self._pattern_configs.clear()
            self._cache.clear()
            # Clear LRU cache
            self.get_rule_config.cache_clear()
            self.get_pattern_config.cache_clear()
        else:
            # Reload specific category
            if category in self._rule_configs:
                del self._rule_configs[category]
            if category in self._pattern_configs:
                del self._pattern_configs[category]
            # Clear specific cache entries
            self.get_rule_config.cache_clear()
            self.get_pattern_config.cache_clear()
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the entire configuration system.
        
        Returns:
            Validation results dictionary
        """
        results = {
            "valid": True,
            "issues": [],
            "statistics": {}
        }
        
        try:
            # Validate base configuration
            base_config = self.base_config
            if not base_config:
                results["issues"].append("Base configuration is empty")
                results["valid"] = False
            
            # Validate all rule configurations
            categories = self.get_all_categories()
            total_rules = 0
            
            for category in categories:
                try:
                    rule_config = self.get_rule_config(category)
                    rules = rule_config.get("rules", [])
                    total_rules += len(rules)
                    
                    if not rules:
                        results["issues"].append(f"Category '{category}' has no rules")
                    
                    # Check for pattern configuration
                    pattern_config = self.get_pattern_config(category)
                    if not pattern_config.get("patterns"):
                        results["issues"].append(f"Category '{category}' has no patterns")
                
                except Exception as e:
                    results["issues"].append(f"Error loading category '{category}': {e}")
                    results["valid"] = False
            
            results["statistics"] = {
                "total_categories": len(categories),
                "total_rules": total_rules,
                "categories": categories
            }
            
        except Exception as e:
            results["issues"].append(f"Configuration validation failed: {e}")
            results["valid"] = False
        
        return results
    
    def get_constitution_manager(self, backend: str = None):
        """
        Get a constitution rule manager instance with specified backend.
        
        Args:
            backend: Backend type ("sqlite", "json", "auto", or None for config default)
            
        Returns:
            Constitution rule manager instance
        """
        try:
            from .constitution.backend_factory import get_constitution_manager
            return get_constitution_manager(backend or "auto", config_dir=str(self.config_dir))
        except ImportError:
            raise ImportError("Constitution module not available. Please ensure config/constitution/ is properly installed.")
    
    def is_constitution_rule_enabled(self, rule_number: int, backend: str = None) -> bool:
        """
        Check if a constitution rule is enabled.
        
        Args:
            rule_number: Rule number to check
            backend: Backend to use for checking (optional)
            
        Returns:
            True if rule is enabled, False otherwise
        """
        try:
            constitution_manager = self.get_constitution_manager(backend)
            return constitution_manager.is_rule_enabled(rule_number)
        except ImportError:
            # Fallback: assume all rules are enabled if constitution module not available
            return True
    
    def switch_constitution_backend(self, new_backend: str) -> bool:
        """
        Switch the default constitution backend.
        
        Args:
            new_backend: New backend to set as default ("sqlite" or "json")
            
        Returns:
            True if switch successful, False otherwise
        """
        try:
            from .constitution.backend_factory import switch_backend
            return switch_backend(new_backend)
        except ImportError:
            return False
    
    def sync_constitution_backends(self, force: bool = False) -> dict:
        """
        Synchronize constitution backends.
        
        Args:
            force: If True, force sync even if data appears unchanged
            
        Returns:
            Dictionary containing sync results
        """
        try:
            from .constitution.sync_manager import sync_backends
            return sync_backends(force)
        except ImportError:
            return {"success": False, "error": "Constitution module not available"}
    
    def get_constitution_backend_status(self) -> dict:
        """
        Get status of all constitution backends.
        
        Returns:
            Dictionary containing backend status information
        """
        try:
            from .constitution.backend_factory import get_backend_status
            return get_backend_status()
        except ImportError:
            return {"error": "Constitution module not available"}