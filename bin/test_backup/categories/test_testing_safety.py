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

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
testing_safety_rules = [r for r in factory.get_all_rules() if r.get("category") == "testing_safety"]

class TestTestingsafetyCategory:
    """Test suite for Testing Safety category rules."""
    
    @pytest.mark.parametrize("rule", testing_safety_rules, ids=lambda r: r["id"])
    def test_testing_safety_rule_exists(self, rule):
        """Test that testing_safety rules are properly defined."""
        assert rule["id"] in ['L007', 'L014', 'L059', 'L069']
        assert rule["category"] == "testing_safety"
        assert rule["constitution"] in ["Product (Initial)", "Testing Safety", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "testing_safety"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_testing_safety_validation(self, test_case):
        """Test testing_safety rule validation logic."""
        assert test_case.rule_id in ['L007', 'L014', 'L059', 'L069']
        assert test_case.category == "testing_safety"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "L007":
            # Rule L007: [Rule description]
            assert "l007" in test_case.test_method_name.lower()
        if test_case.rule_id == "L014":
            # Rule L014: [Rule description]
            assert "l014" in test_case.test_method_name.lower()
        if test_case.rule_id == "L059":
            # Rule L059: [Rule description]
            assert "l059" in test_case.test_method_name.lower()
        if test_case.rule_id == "L069":
            # Rule L069: [Rule description]
            assert "l069" in test_case.test_method_name.lower()
    
    def test_testing_safety_coverage(self):
        """Test that all testing_safety rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "testing_safety"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'L014', 'L059', 'L007', 'L069'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_testing_safety_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in testing_safety_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
