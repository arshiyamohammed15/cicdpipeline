#!/usr/bin/env python3
"""
Consolidated test for Requirements category rules.

Tests rules: L001, L002 (Do exactly what's asked, Only use information you're given)
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
requirements_rules = []
for r in all_rules:
    if r.get("category") == "requirements":
        requirements_rules.append(r)
    elif "requirements" in r.get("categories", []):
        requirements_rules.append(r)

class TestRequirementsCategory:
    """Test suite for Requirements category rules."""
    
    @pytest.mark.parametrize("rule", requirements_rules, ids=lambda r: r["id"])
    def test_requirements_rule_exists(self, rule):
        """Test that requirements rules are properly defined."""
        assert rule["id"] in ["L001", "L002"]
        # Check if rule belongs to requirements category (primary or in categories list)
        is_requirements = (rule["category"] == "requirements" or 
                           "requirements" in rule.get("categories", []))
        assert is_requirements, f"Rule {rule['id']} should belong to requirements category"
        assert rule["constitution"] == "Product (Initial)"
        assert rule["severity"] in ("error", "warning", "info")
    
    def test_requirements_validation(self):
        """Test requirements rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in requirements_rules:
            is_requirements = (rule["category"] == "requirements" or 
                           "requirements" in rule.get("categories", []))
            assert is_requirements, f"Rule {rule['id']} should belong to requirements category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_requirements_coverage(self):
        """Test that all requirements rules are covered."""
        covered_rules = {rule["id"] for rule in requirements_rules}
        
        expected_rules = {"L001", "L002"}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_requirements_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in requirements_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
