#!/usr/bin/env python3
"""
Consolidated test for Platform category rules.

Tests rules: L042, L043, L044, L045, L046, L047, L048, L049, L050, L051 (Platform features and technical implementation)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
all_rules = factory.get_all_rules()
platform_rules = []
for r in all_rules:
    if r.get("category") == "platform":
        platform_rules.append(r)
    elif "platform" in r.get("categories", []):
        platform_rules.append(r)

class TestPlatformCategory:
    """Test suite for Platform category rules."""
    
    @pytest.mark.parametrize("rule", platform_rules, ids=lambda r: r["id"])
    def test_platform_rule_exists(self, rule):
        """Test that platform rules are properly defined."""
        assert rule["id"] in ['L042', 'L043', 'L044', 'L045', 'L046', 'L047', 'L048', 'L049', 'L050', 'L051']
        # Check if rule belongs to platform category (primary or in categories list)
        is_platform = (rule["category"] == "platform" or 
                           "platform" in rule.get("categories", []))
        assert is_platform, f"Rule {rule['id']} should belong to platform category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_platform_validation(self):
        """Test platform rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in platform_rules:
            is_platform = (rule["category"] == "platform" or 
                           "platform" in rule.get("categories", []))
            assert is_platform, f"Rule {rule['id']} should belong to platform category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_platform_coverage(self):
        """Test that all platform rules are covered."""
        covered_rules = {rule["id"] for rule in platform_rules}
        
        expected_rules = {'L046', 'L050', 'L048', 'L049', 'L051', 'L044', 'L045', 'L042', 'L043', 'L047'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_platform_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in platform_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
