#!/usr/bin/env python3
"""
Consolidated test for Testing Safety category rules.

Tests rules: L007, L014, L059, L069 (Testing and safety principles)
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
testing_safety_rules = []
for r in all_rules:
    if r.get("category") == "testing_safety":
        testing_safety_rules.append(r)
    elif "testing_safety" in r.get("categories", []):
        testing_safety_rules.append(r)

class TestTestingsafetyCategory:
    """Test suite for Testing Safety category rules."""
    
    @pytest.mark.parametrize("rule", testing_safety_rules, ids=lambda r: r["id"])
    def test_testing_safety_rule_exists(self, rule):
        """Test that testing_safety rules are properly defined."""
        assert rule["id"] in ['L007', 'L014', 'L059', 'L069']
        # Check if rule belongs to testing_safety category (primary or in categories list)
        is_testing_safety = (rule["category"] == "testing_safety" or 
                           "testing_safety" in rule.get("categories", []))
        assert is_testing_safety, f"Rule {rule['id']} should belong to testing_safety category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_testing_safety_validation(self):
        """Test testing_safety rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in testing_safety_rules:
            is_testing_safety = (rule["category"] == "testing_safety" or 
                           "testing_safety" in rule.get("categories", []))
            assert is_testing_safety, f"Rule {rule['id']} should belong to testing_safety category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_testing_safety_coverage(self):
        """Test that all testing_safety rules are covered."""
        covered_rules = {rule["id"] for rule in testing_safety_rules}
        
        expected_rules = {'L014', 'L059', 'L007', 'L069'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_testing_safety_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in testing_safety_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
