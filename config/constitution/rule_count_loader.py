#!/usr/bin/env python3
"""
Rule Count Loader - Single Source of Truth

This module provides dynamic rule counting from docs/constitution JSON files.
The JSON files in docs/constitution are the ONLY source of truth for rule counts.
No hardcoded counts should exist anywhere in the codebase.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class RuleCountLoader:
    """
    Loads rule counts dynamically from docs/constitution JSON files.

    This is the SINGLE SOURCE OF TRUTH for rule counts.
    All other files should use this class to get rule counts instead of hardcoding.
    """

    def __init__(self, constitution_dir: str = "docs/constitution"):
        """
        Initialize the rule count loader.

        Args:
            constitution_dir: Path to directory containing constitution JSON files
        """
        self.constitution_dir = Path(constitution_dir)
        self._cached_counts: Dict[str, Any] = {}
        self._cache_valid = False

    def _load_rules_from_json_files(self) -> Tuple[int, int, int, Dict[str, int]]:
        """
        Load all rules from JSON files and count them.

        Returns:
            Tuple of (total_rules, enabled_rules, disabled_rules, category_counts)
        """
        if not self.constitution_dir.exists():
            raise FileNotFoundError(f"Constitution directory not found: {self.constitution_dir}")

        json_files = sorted(list(self.constitution_dir.glob("*.json")))

        if not json_files:
            raise FileNotFoundError(f"No JSON files found in {self.constitution_dir}")

        total_rules = 0
        enabled_rules = 0
        disabled_rules = 0
        category_counts: Dict[str, int] = {}

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    rules = data.get('constitution_rules', [])

                    for rule in rules:
                        total_rules += 1
                        if rule.get('enabled', True):
                            enabled_rules += 1
                        else:
                            disabled_rules += 1

                        # Count by category
                        category = rule.get('category', 'UNKNOWN')
                        category_counts[category] = category_counts.get(category, 0) + 1

            except Exception as e:
                logger.warning(f"Could not load rules from {json_file}: {e}")
                continue

        return total_rules, enabled_rules, disabled_rules, category_counts

    def get_counts(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Get rule counts from source of truth (JSON files).

        Args:
            force_reload: Force reload from files instead of using cache

        Returns:
            Dictionary with counts:
            {
                'total_rules': int,
                'enabled_rules': int,
                'disabled_rules': int,
                'category_counts': Dict[str, int]
            }
        """
        if not self._cache_valid or force_reload:
            total, enabled, disabled, categories = self._load_rules_from_json_files()
            self._cached_counts = {
                'total_rules': total,
                'enabled_rules': enabled,
                'disabled_rules': disabled,
                'category_counts': categories
            }
            self._cache_valid = True

        return self._cached_counts.copy()

    def get_total_rules(self) -> int:
        """Get total rule count."""
        return self.get_counts()['total_rules']

    def get_enabled_rules(self) -> int:
        """Get enabled rule count."""
        return self.get_counts()['enabled_rules']

    def get_disabled_rules(self) -> int:
        """Get disabled rule count."""
        return self.get_counts()['disabled_rules']

    def get_category_counts(self) -> Dict[str, int]:
        """Get rule counts by category."""
        return self.get_counts()['category_counts'].copy()

    def invalidate_cache(self):
        """Invalidate cached counts to force reload on next access."""
        self._cache_valid = False


# Global instance for easy access
_rule_count_loader = None


def get_rule_count_loader(constitution_dir: str = "docs/constitution") -> RuleCountLoader:
    """
    Get the global rule count loader instance.

    Args:
        constitution_dir: Path to constitution directory

    Returns:
        RuleCountLoader instance
    """
    global _rule_count_loader
    if _rule_count_loader is None:
        _rule_count_loader = RuleCountLoader(constitution_dir)
    return _rule_count_loader


def get_rule_counts(constitution_dir: str = "docs/constitution") -> Dict[str, Any]:
    """
    Convenience function to get rule counts.

    Args:
        constitution_dir: Path to constitution directory

    Returns:
        Dictionary with rule counts
    """
    loader = get_rule_count_loader(constitution_dir)
    return loader.get_counts()
