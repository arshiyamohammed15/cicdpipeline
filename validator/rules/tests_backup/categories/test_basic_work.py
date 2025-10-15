#!/usr/bin/env python3
"""
Consolidated test for Basic Work category rules.

Tests rules: L004, L005, L010, L013, L020 (Core principles for all development work)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
basic_work_rules = [r for r in factory.get_all_rules() if r.get("category") == "basic_work"]

class TestBasicWorkCategory:
    """Test suite for Basic Work category rules."""
    
    @pytest.mark.parametrize("rule", basic_work_rules, ids=lambda r: r["id"])
    def test_basic_work_rule_exists(self, rule):
        """Test that basic work rules are properly defined."""
        assert rule["id"] in ["L004", "L005", "L010", "L013", "L020"]
        assert rule["category"] == "basic_work"
        assert rule["constitution"] in ["Product (Initial)", "Basic Work"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "basic_work"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_basic_work_validation(self, test_case):
        """Test basic work rule validation logic."""
        assert test_case.rule_id in ["L004", "L005", "L010", "L013", "L020"]
        assert test_case.category == "basic_work"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "L004":
            # Rule L004: Use settings files, not hardcoded numbers
            assert "settings" in test_case.test_method_name.lower() or "hardcoded" in test_case.test_method_name.lower()
        elif test_case.rule_id == "L005":
            # Rule L005: Keep good records + keep good logs
            assert "log" in test_case.test_method_name.lower() or "record" in test_case.test_method_name.lower()
        elif test_case.rule_id == "L010":
            # Rule L010: Be honest about AI decisions
            assert "ai" in test_case.test_method_name.lower() or "honest" in test_case.test_method_name.lower()
        elif test_case.rule_id == "L013":
            # Rule L013: Learn from mistakes
            assert "learn" in test_case.test_method_name.lower() or "mistake" in test_case.test_method_name.lower()
        elif test_case.rule_id == "L020":
            # Rule L020: Be fair to everyone
            assert "fair" in test_case.test_method_name.lower() or "accessibility" in test_case.test_method_name.lower()
    
    def test_basic_work_coverage(self):
        """Test that all basic work rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "basic_work"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {"L004", "L005", "L010", "L013", "L020"}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_basic_work_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in basic_work_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
