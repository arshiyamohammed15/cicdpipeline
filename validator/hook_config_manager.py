"""
Hook Configuration Manager for Pre-Implementation Hooks

This module provides configuration management for individual pre-implementation hooks,
allowing them to be enabled/disabled through CLI commands.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum


class HookStatus(Enum):
    """Hook status enumeration."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    CONDITIONAL = "conditional"


class HookCategory(Enum):
    """Hook category enumeration."""
    BASIC_WORK = "basic_work"
    CODE_REVIEW = "code_review"
    SECURITY_PRIVACY = "security_privacy"
    LOGGING = "logging"
    ERROR_HANDLING = "error_handling"
    TYPESCRIPT = "typescript"
    STORAGE_GOVERNANCE = "storage_governance"
    GSMD = "gsmd"
    SIMPLE_READABILITY = "simple_readability"


class HookConfigManager:
    """
    Manages configuration for individual pre-implementation hooks.
    
    This allows fine-grained control over which hooks are enabled/disabled
    for different contexts and use cases.
    """
    
    def __init__(self, config_path: str = "config/hook_config.json"):
        """
        Initialize the hook configuration manager.
        
        Args:
            config_path: Path to the hook configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize default hook categories and their rules
        self.hook_categories = {
            HookCategory.BASIC_WORK: {
                'name': 'Basic Work Rules',
                'description': 'Fundamental development practices and principles',
                'rule_range': (1, 75),
                'default_enabled': True,
                'rules': self._generate_rule_list(1, 75)
            },
            HookCategory.CODE_REVIEW: {
                'name': 'Code Review Rules',
                'description': 'Code review and quality assurance practices',
                'rule_range': (76, 99),
                'default_enabled': True,
                'rules': self._generate_rule_list(76, 99)
            },
            HookCategory.SECURITY_PRIVACY: {
                'name': 'Security & Privacy Rules',
                'description': 'Security and privacy protection measures',
                'rule_range': (100, 131),
                'default_enabled': True,
                'rules': self._generate_rule_list(100, 131)
            },
            HookCategory.LOGGING: {
                'name': 'Logging Rules',
                'description': 'Structured logging and observability practices',
                'rule_range': (132, 149),
                'default_enabled': True,
                'rules': self._generate_rule_list(132, 149)
            },
            HookCategory.ERROR_HANDLING: {
                'name': 'Error Handling Rules',
                'description': 'Error handling and recovery patterns',
                'rule_range': (150, 180),
                'default_enabled': True,
                'rules': self._generate_rule_list(150, 180)
            },
            HookCategory.TYPESCRIPT: {
                'name': 'TypeScript Rules',
                'description': 'TypeScript development standards and practices',
                'rule_range': (181, 215),
                'default_enabled': True,
                'rules': self._generate_rule_list(181, 215)
            },
            HookCategory.STORAGE_GOVERNANCE: {
                'name': 'Storage Governance Rules',
                'description': 'Data storage and governance practices',
                'rule_range': (216, 228),
                'default_enabled': True,
                'rules': self._generate_rule_list(216, 228)
            },
            HookCategory.GSMD: {
                'name': 'GSMD Rules',
                'description': 'Governance, Security, and Management of Data rules',
                'rule_range': (232, 252),
                'default_enabled': True,
                'rules': self._generate_rule_list(232, 252)
            },
            HookCategory.SIMPLE_READABILITY: {
                'name': 'Simple Readability Rules',
                'description': 'Code readability and simplicity standards',
                'rule_range': (253, 280),
                'default_enabled': True,
                'rules': self._generate_rule_list(253, 280)
            }
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load hook configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load hook config: {e}")
                return self._create_default_config()
        else:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        return {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'global_settings': {
                'default_status': 'enabled',
                'strict_mode': True,
                'context_aware': True
            },
            'categories': {},
            'individual_rules': {},
            'context_overrides': {
                'file_types': {},
                'task_types': {},
                'environments': {}
            }
        }
    
    def _generate_rule_list(self, start: int, end: int) -> List[Dict[str, Any]]:
        """Generate a list of rules for a given range."""
        rules = []
        for rule_num in range(start, end + 1):
            rules.append({
                'rule_id': rule_num,
                'status': HookStatus.ENABLED.value,
                'enabled_at': datetime.now().isoformat(),
                'disabled_reason': None,
                'context_conditions': []
            })
        return rules
    
    def _save_config(self):
        """Save configuration to file."""
        self.config['updated_at'] = datetime.now().isoformat()
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def enable_category(self, category: HookCategory, reason: str = None) -> bool:
        """
        Enable all rules in a category.
        
        Args:
            category: The hook category to enable
            reason: Optional reason for the change
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if category not in self.hook_categories:
                return False
            
            cat_config = {
                'name': self.hook_categories[category]['name'],
                'description': self.hook_categories[category]['description'],
                'status': HookStatus.ENABLED.value,
                'enabled_at': datetime.now().isoformat(),
                'enabled_reason': reason,
                'rule_count': len(self.hook_categories[category]['rules'])
            }
            
            self.config['categories'][category.value] = cat_config
            
            # Enable all individual rules in the category
            for rule in self.hook_categories[category]['rules']:
                rule_id = str(rule['rule_id'])
                self.config['individual_rules'][rule_id] = {
                    'status': HookStatus.ENABLED.value,
                    'enabled_at': datetime.now().isoformat(),
                    'enabled_reason': reason,
                    'category': category.value
                }
            
            self._save_config()
            return True
            
        except Exception as e:
            print(f"Error enabling category {category.value}: {e}")
            return False
    
    def disable_category(self, category: HookCategory, reason: str = None) -> bool:
        """
        Disable all rules in a category.
        
        Args:
            category: The hook category to disable
            reason: Reason for disabling the category
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if category not in self.hook_categories:
                return False
            
            cat_config = {
                'name': self.hook_categories[category]['name'],
                'description': self.hook_categories[category]['description'],
                'status': HookStatus.DISABLED.value,
                'disabled_at': datetime.now().isoformat(),
                'disabled_reason': reason,
                'rule_count': len(self.hook_categories[category]['rules'])
            }
            
            self.config['categories'][category.value] = cat_config
            
            # Disable all individual rules in the category
            for rule in self.hook_categories[category]['rules']:
                rule_id = str(rule['rule_id'])
                self.config['individual_rules'][rule_id] = {
                    'status': HookStatus.DISABLED.value,
                    'disabled_at': datetime.now().isoformat(),
                    'disabled_reason': reason,
                    'category': category.value
                }
            
            self._save_config()
            return True
            
        except Exception as e:
            print(f"Error disabling category {category.value}: {e}")
            return False
    
    def enable_rule(self, rule_id: int, reason: str = None) -> bool:
        """
        Enable a specific rule.
        
        Args:
            rule_id: The rule ID to enable
            reason: Optional reason for the change
            
        Returns:
            True if successful, False otherwise
        """
        try:
            rule_id_str = str(rule_id)
            category = self._get_rule_category(rule_id)
            
            self.config['individual_rules'][rule_id_str] = {
                'status': HookStatus.ENABLED.value,
                'enabled_at': datetime.now().isoformat(),
                'enabled_reason': reason,
                'category': category.value if category else 'unknown'
            }
            
            self._save_config()
            return True
            
        except Exception as e:
            print(f"Error enabling rule {rule_id}: {e}")
            return False
    
    def disable_rule(self, rule_id: int, reason: str = None) -> bool:
        """
        Disable a specific rule.
        
        Args:
            rule_id: The rule ID to disable
            reason: Reason for disabling the rule
            
        Returns:
            True if successful, False otherwise
        """
        try:
            rule_id_str = str(rule_id)
            category = self._get_rule_category(rule_id)
            
            self.config['individual_rules'][rule_id_str] = {
                'status': HookStatus.DISABLED.value,
                'disabled_at': datetime.now().isoformat(),
                'disabled_reason': reason,
                'category': category.value if category else 'unknown'
            }
            
            self._save_config()
            return True
            
        except Exception as e:
            print(f"Error disabling rule {rule_id}: {e}")
            return False
    
    def _get_rule_category(self, rule_id: int) -> Optional[HookCategory]:
        """Get the category for a specific rule ID."""
        for category, config in self.hook_categories.items():
            start, end = config['rule_range']
            if start <= rule_id <= end:
                return category
        return None
    
    def get_rule_status(self, rule_id: int) -> HookStatus:
        """
        Get the status of a specific rule.
        
        Args:
            rule_id: The rule ID to check
            
        Returns:
            The status of the rule
        """
        rule_id_str = str(rule_id)
        
        # Check individual rule override first
        if rule_id_str in self.config['individual_rules']:
            status = self.config['individual_rules'][rule_id_str]['status']
            return HookStatus(status)
        
        # Check category status
        category = self._get_rule_category(rule_id)
        if category and category.value in self.config['categories']:
            status = self.config['categories'][category.value]['status']
            return HookStatus(status)
        
        # Return default status
        return HookStatus(self.config['global_settings']['default_status'])
    
    def is_rule_enabled(self, rule_id: int) -> bool:
        """
        Check if a specific rule is enabled.
        
        Args:
            rule_id: The rule ID to check
            
        Returns:
            True if the rule is enabled, False otherwise
        """
        return self.get_rule_status(rule_id) == HookStatus.ENABLED
    
    def get_enabled_rules(self) -> List[int]:
        """
        Get list of all enabled rule IDs.
        
        Returns:
            List of enabled rule IDs
        """
        enabled_rules = []
        
        for rule_id_str, rule_config in self.config['individual_rules'].items():
            if rule_config['status'] == HookStatus.ENABLED.value:
                enabled_rules.append(int(rule_id_str))
        
        return sorted(enabled_rules)
    
    def get_disabled_rules(self) -> List[int]:
        """
        Get list of all disabled rule IDs.
        
        Returns:
            List of disabled rule IDs
        """
        disabled_rules = []
        
        for rule_id_str, rule_config in self.config['individual_rules'].items():
            if rule_config['status'] == HookStatus.DISABLED.value:
                disabled_rules.append(int(rule_id_str))
        
        return sorted(disabled_rules)
    
    def get_category_status(self, category: HookCategory) -> Dict[str, Any]:
        """
        Get the status of a category.
        
        Args:
            category: The category to check
            
        Returns:
            Dictionary with category status information
        """
        if category.value in self.config['categories']:
            return self.config['categories'][category.value]
        else:
            return {
                'name': self.hook_categories[category]['name'],
                'status': HookStatus.ENABLED.value,
                'rule_count': len(self.hook_categories[category]['rules']),
                'default': True
            }
    
    def list_all_categories(self) -> Dict[str, Any]:
        """
        List all categories with their status.
        
        Returns:
            Dictionary with all categories and their status
        """
        categories = {}
        
        for category in HookCategory:
            categories[category.value] = self.get_category_status(category)
        
        return categories
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get hook configuration statistics.
        
        Returns:
            Dictionary with configuration statistics
        """
        # Get all rules that have been configured (either explicitly or by category)
        all_configured_rules = set()
        
        # Add rules from individual configuration
        for rule_id_str in self.config['individual_rules'].keys():
            all_configured_rules.add(int(rule_id_str))
        
        # Add rules from category configuration
        for category in HookCategory:
            cat_status = self.get_category_status(category)
            if cat_status['status'] == HookStatus.ENABLED.value:
                # Add all rules in this category
                start, end = self.hook_categories[category]['rule_range']
                for rule_id in range(start, end + 1):
                    all_configured_rules.add(rule_id)
        
        total_rules = len(all_configured_rules)
        enabled_rules = len(self.get_enabled_rules())
        disabled_rules = len(self.get_disabled_rules())
        
        return {
            'total_rules': total_rules,
            'enabled_rules': enabled_rules,
            'disabled_rules': disabled_rules,
            'enabled_percentage': (enabled_rules / total_rules * 100) if total_rules > 0 else 0,
            'categories': {
                'total': len(HookCategory),
                'enabled': len([cat for cat in HookCategory if self.get_category_status(cat)['status'] == HookStatus.ENABLED.value]),
                'disabled': len([cat for cat in HookCategory if self.get_category_status(cat)['status'] == HookStatus.DISABLED.value])
            }
        }
    
    def export_config(self, enabled_only: bool = False) -> Dict[str, Any]:
        """
        Export configuration to a dictionary.
        
        Args:
            enabled_only: If True, only export enabled rules
            
        Returns:
            Dictionary with configuration data
        """
        if enabled_only:
            return {
                'enabled_rules': self.get_enabled_rules(),
                'enabled_categories': [
                    cat.value for cat in HookCategory 
                    if self.get_category_status(cat)['status'] == HookStatus.ENABLED.value
                ],
                'exported_at': datetime.now().isoformat()
            }
        else:
            return self.config.copy()
    
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to defaults.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.config = self._create_default_config()
            self._save_config()
            return True
        except Exception as e:
            print(f"Error resetting to defaults: {e}")
            return False
