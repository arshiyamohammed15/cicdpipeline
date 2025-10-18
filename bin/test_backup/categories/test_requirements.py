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

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
requirements_rules = [r for r in factory.get_all_rules() if r.get("category") == "requirements"]

class TestRequirementsCategory:
    """Test suite for Requirements category rules."""
    
    @pytest.mark.parametrize("rule", requirements_rules, ids=lambda r: r["id"])
    def test_requirements_rule_exists(self, rule):
        """Test that requirements rules are properly defined."""
        assert rule["id"] in ["L001", "L002"]
        assert rule["category"] == "requirements"
        assert rule["constitution"] == "Product (Initial)"
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "requirements"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_requirements_validation(self, test_case):
        """Test requirements rule validation logic."""
        assert test_case.rule_id in ["L001", "L002"]
        assert test_case.category == "requirements"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "L001":
            # Rule L001: Do exactly what's asked
            assert "incomplete" in test_case.test_method_name.lower() or "todo" in test_case.test_method_name.lower()
        elif test_case.rule_id == "L002":
            # Rule L002: Only use information you're given
            assert "assumption" in test_case.test_method_name.lower() or "magic" in test_case.test_method_name.lower()
    
    def test_requirements_coverage(self):
        """Test that all requirements rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "requirements"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {"L001", "L002"}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_requirements_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in requirements_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
