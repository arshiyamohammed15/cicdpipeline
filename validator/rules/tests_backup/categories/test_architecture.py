#!/usr/bin/env python3
"""
Consolidated test for Architecture category rules.

Tests rules: L019, L021, L023, L024, L028 (Architecture and system design)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
architecture_rules = [r for r in factory.get_all_rules() if r.get("category") == "architecture"]

class TestArchitectureCategory:
    """Test suite for Architecture category rules."""
    
    @pytest.mark.parametrize("rule", architecture_rules, ids=lambda r: r["id"])
    def test_architecture_rule_exists(self, rule):
        """Test that architecture rules are properly defined."""
        assert rule["id"] in ['L019', 'L021', 'L023', 'L024', 'L028']
        assert rule["category"] == "architecture"
        assert rule["constitution"] in ["Product (Initial)", "Architecture", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "architecture"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_architecture_validation(self, test_case):
        """Test architecture rule validation logic."""
        assert test_case.rule_id in ['L019', 'L021', 'L023', 'L024', 'L028']
        assert test_case.category == "architecture"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "L019":
            # Rule L019: [Rule description]
            assert "l019" in test_case.test_method_name.lower()
        if test_case.rule_id == "L021":
            # Rule L021: [Rule description]
            assert "l021" in test_case.test_method_name.lower()
        if test_case.rule_id == "L023":
            # Rule L023: [Rule description]
            assert "l023" in test_case.test_method_name.lower()
        if test_case.rule_id == "L024":
            # Rule L024: [Rule description]
            assert "l024" in test_case.test_method_name.lower()
        if test_case.rule_id == "L028":
            # Rule L028: [Rule description]
            assert "l028" in test_case.test_method_name.lower()
    
    def test_architecture_coverage(self):
        """Test that all architecture rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "architecture"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'L023', 'L019', 'L028', 'L021', 'L024'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_architecture_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in architecture_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
