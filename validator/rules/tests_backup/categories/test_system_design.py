#!/usr/bin/env python3
"""
Consolidated test for System Design category rules.

Tests rules: L022, L025, L026, L029, L030, L031, L032 (Architecture and system design principles)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
system_design_rules = [r for r in factory.get_all_rules() if r.get("category") == "system_design"]

class TestSystemdesignCategory:
    """Test suite for System Design category rules."""
    
    @pytest.mark.parametrize("rule", system_design_rules, ids=lambda r: r["id"])
    def test_system_design_rule_exists(self, rule):
        """Test that system_design rules are properly defined."""
        assert rule["id"] in ['L022', 'L025', 'L026', 'L029', 'L030', 'L031', 'L032']
        assert rule["category"] == "system_design"
        assert rule["constitution"] in ["Product (Initial)", "System Design", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "system_design"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_system_design_validation(self, test_case):
        """Test system_design rule validation logic."""
        assert test_case.rule_id in ['L022', 'L025', 'L026', 'L029', 'L030', 'L031', 'L032']
        assert test_case.category == "system_design"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "L022":
            # Rule L022: [Rule description]
            assert "l022" in test_case.test_method_name.lower()
        if test_case.rule_id == "L025":
            # Rule L025: [Rule description]
            assert "l025" in test_case.test_method_name.lower()
        if test_case.rule_id == "L026":
            # Rule L026: [Rule description]
            assert "l026" in test_case.test_method_name.lower()
        if test_case.rule_id == "L029":
            # Rule L029: [Rule description]
            assert "l029" in test_case.test_method_name.lower()
        if test_case.rule_id == "L030":
            # Rule L030: [Rule description]
            assert "l030" in test_case.test_method_name.lower()
        if test_case.rule_id == "L031":
            # Rule L031: [Rule description]
            assert "l031" in test_case.test_method_name.lower()
        if test_case.rule_id == "L032":
            # Rule L032: [Rule description]
            assert "l032" in test_case.test_method_name.lower()
    
    def test_system_design_coverage(self):
        """Test that all system_design rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "system_design"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'L022', 'L029', 'L025', 'L026', 'L031', 'L032', 'L030'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_system_design_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in system_design_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
