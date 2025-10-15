#!/usr/bin/env python3
"""
Rule loader for dynamic rule loading and management.

This module provides functionality to load rules dynamically from configuration
files and manage rule dependencies and conflicts.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum


class RuleStatus(Enum):
    """Status of a rule."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    CONFLICT = "conflict"
    DEPENDENCY_MISSING = "dependency_missing"


@dataclass
class RuleDefinition:
    """Definition of a rule."""
    rule_id: str
    rule_number: int
    name: str
    category: str
    priority: str
    description: str
    severity: str
    patterns: Dict[str, Any]
    dependencies: List[str]
    conflicts: List[str]
    status: RuleStatus = RuleStatus.ENABLED


class RuleLoader:
    """
    Loader for rules with dependency management and conflict resolution.
    
    This loader provides:
    - Dynamic rule loading from configuration files
    - Dependency resolution
    - Conflict detection and resolution
    - Rule status management
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the rule loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.rules: Dict[str, RuleDefinition] = {}
        self.categories: Dict[str, List[str]] = {}
        self.dependencies: Dict[str, Set[str]] = {}
        self.conflicts: Dict[str, Set[str]] = {}
        
        # Load all rules
        self._load_all_rules()
        self._resolve_dependencies()
        self._detect_conflicts()
    
    def _load_all_rules(self):
        """Load all rules from configuration files."""
        # Load base configuration
        base_config_path = self.config_dir / "base_config.json"
        if base_config_path.exists():
            with open(base_config_path, 'r', encoding='utf-8') as f:
                base_config = json.load(f)
        else:
            base_config = {}
        
        # Load rule configurations
        rules_dir = self.config_dir / "rules"
        if rules_dir.exists():
            for config_file in rules_dir.glob("*.json"):
                self._load_rule_config(config_file, base_config)
        
        # Load pattern configurations
        patterns_dir = self.config_dir / "patterns"
        if patterns_dir.exists():
            for pattern_file in patterns_dir.glob("*.json"):
                self._load_pattern_config(pattern_file)
    
    def _load_rule_config(self, config_file: Path, base_config: Dict[str, Any]):
        """Load rule configuration from a file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                rule_config = json.load(f)
            
            category = rule_config.get("category", config_file.stem)
            rules = rule_config.get("rules", [])
            priority = rule_config.get("priority", "unknown")
            description = rule_config.get("description", "")
            
            # Create rule definitions
            for rule_number in rules:
                rule_id = f"rule_{rule_number:03d}"
                
                rule_def = RuleDefinition(
                    rule_id=rule_id,
                    rule_number=rule_number,
                    name=f"Rule {rule_number}",
                    category=category,
                    priority=priority,
                    description=description,
                    severity="warning",  # Default severity
                    patterns={},
                    dependencies=[],
                    conflicts=[]
                )
                
                self.rules[rule_id] = rule_def
                
                # Add to category
                if category not in self.categories:
                    self.categories[category] = []
                self.categories[category].append(rule_id)
        
        except Exception as e:
            print(f"Error loading rule config {config_file}: {e}")
    
    def _load_pattern_config(self, pattern_file: Path):
        """Load pattern configuration from a file."""
        try:
            with open(pattern_file, 'r', encoding='utf-8') as f:
                pattern_config = json.load(f)
            
            category = pattern_config.get("category", pattern_file.stem.replace("_patterns", ""))
            patterns = pattern_config.get("patterns", {})
            
            # Update rules in this category with patterns
            if category in self.categories:
                for rule_id in self.categories[category]:
                    if rule_id in self.rules:
                        self.rules[rule_id].patterns.update(patterns)
        
        except Exception as e:
            print(f"Error loading pattern config {pattern_file}: {e}")
    
    def _resolve_dependencies(self):
        """Resolve rule dependencies."""
        for rule_id, rule_def in self.rules.items():
            # Check for dependencies
            for dep_rule_id in rule_def.dependencies:
                if dep_rule_id not in self.rules:
                    rule_def.status = RuleStatus.DEPENDENCY_MISSING
                    break
            
            # Build dependency graph
            self.dependencies[rule_id] = set(rule_def.dependencies)
    
    def _detect_conflicts(self):
        """Detect rule conflicts."""
        for rule_id, rule_def in self.rules.items():
            # Check for conflicts
            for conflict_rule_id in rule_def.conflicts:
                if conflict_rule_id in self.rules:
                    # Mark both rules as conflicting
                    rule_def.status = RuleStatus.CONFLICT
                    if conflict_rule_id in self.rules:
                        self.rules[conflict_rule_id].status = RuleStatus.CONFLICT
            
            # Build conflict graph
            self.conflicts[rule_id] = set(rule_def.conflicts)
    
    def get_rule(self, rule_id: str) -> Optional[RuleDefinition]:
        """Get a rule definition by ID."""
        return self.rules.get(rule_id)
    
    def get_rules_by_category(self, category: str) -> List[RuleDefinition]:
        """Get all rules in a category."""
        if category not in self.categories:
            return []
        
        return [self.rules[rule_id] for rule_id in self.categories[category] 
                if rule_id in self.rules]
    
    def get_enabled_rules(self) -> List[RuleDefinition]:
        """Get all enabled rules."""
        return [rule for rule in self.rules.values() 
                if rule.status == RuleStatus.ENABLED]
    
    def get_disabled_rules(self) -> List[RuleDefinition]:
        """Get all disabled rules."""
        return [rule for rule in self.rules.values() 
                if rule.status == RuleStatus.DISABLED]
    
    def get_conflicting_rules(self) -> List[RuleDefinition]:
        """Get all rules with conflicts."""
        return [rule for rule in self.rules.values() 
                if rule.status == RuleStatus.CONFLICT]
    
    def enable_rule(self, rule_id: str) -> bool:
        """
        Enable a rule.
        
        Args:
            rule_id: ID of the rule to enable
            
        Returns:
            True if rule was enabled successfully
        """
        if rule_id not in self.rules:
            return False
        
        rule = self.rules[rule_id]
        
        # Check dependencies
        for dep_rule_id in rule.dependencies:
            if dep_rule_id not in self.rules or self.rules[dep_rule_id].status != RuleStatus.ENABLED:
                return False
        
        # Check conflicts
        for conflict_rule_id in rule.conflicts:
            if conflict_rule_id in self.rules and self.rules[conflict_rule_id].status == RuleStatus.ENABLED:
                return False
        
        rule.status = RuleStatus.ENABLED
        return True
    
    def disable_rule(self, rule_id: str) -> bool:
        """
        Disable a rule.
        
        Args:
            rule_id: ID of the rule to disable
            
        Returns:
            True if rule was disabled successfully
        """
        if rule_id not in self.rules:
            return False
        
        rule = self.rules[rule_id]
        rule.status = RuleStatus.DISABLED
        
        # Disable dependent rules
        for other_rule_id, other_rule in self.rules.items():
            if rule_id in other_rule.dependencies:
                other_rule.status = RuleStatus.DEPENDENCY_MISSING
        
        return True
    
    def resolve_conflicts(self, preferred_rules: List[str]) -> Dict[str, bool]:
        """
        Resolve rule conflicts by preferring certain rules.
        
        Args:
            preferred_rules: List of rule IDs to prefer in conflicts
            
        Returns:
            Dictionary mapping rule IDs to their new status
        """
        results = {}
        
        for rule_id, rule in self.rules.items():
            if rule.status == RuleStatus.CONFLICT:
                # Check if this rule is preferred
                if rule_id in preferred_rules:
                    rule.status = RuleStatus.ENABLED
                    results[rule_id] = True
                else:
                    rule.status = RuleStatus.DISABLED
                    results[rule_id] = False
        
        return results
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded rules."""
        stats = {
            "total_rules": len(self.rules),
            "enabled_rules": len(self.get_enabled_rules()),
            "disabled_rules": len(self.get_disabled_rules()),
            "conflicting_rules": len(self.get_conflicting_rules()),
            "categories": len(self.categories),
            "rules_by_category": {},
            "rules_by_priority": {},
            "rules_by_status": {}
        }
        
        # Count by category
        for category, rule_ids in self.categories.items():
            stats["rules_by_category"][category] = len(rule_ids)
        
        # Count by priority
        for rule in self.rules.values():
            priority = rule.priority
            stats["rules_by_priority"][priority] = stats["rules_by_priority"].get(priority, 0) + 1
        
        # Count by status
        for rule in self.rules.values():
            status = rule.status.value
            stats["rules_by_status"][status] = stats["rules_by_status"].get(status, 0) + 1
        
        return stats
    
    def export_configuration(self, output_path: str):
        """
        Export current rule configuration to a file.
        
        Args:
            output_path: Path to export configuration to
        """
        config = {
            "rules": {},
            "categories": self.categories,
            "statistics": self.get_rule_statistics()
        }
        
        for rule_id, rule in self.rules.items():
            config["rules"][rule_id] = {
                "rule_number": rule.rule_number,
                "name": rule.name,
                "category": rule.category,
                "priority": rule.priority,
                "description": rule.description,
                "severity": rule.severity,
                "status": rule.status.value,
                "dependencies": rule.dependencies,
                "conflicts": rule.conflicts
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    def reload_configuration(self):
        """Reload all configuration files."""
        self.rules.clear()
        self.categories.clear()
        self.dependencies.clear()
        self.conflicts.clear()
        
        self._load_all_rules()
        self._resolve_dependencies()
        self._detect_conflicts()
