#!/usr/bin/env python3
"""
Consolidated test for Performance category rules.

Tests rules: L008, L067 (Performance optimization)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
performance_rules = [r for r in factory.get_all_rules() if r.get("category") == "performance"]

class TestPerformanceCategory:
    """Test suite for Performance category rules."""
    
    @pytest.mark.parametrize("rule", performance_rules, ids=lambda r: r["id"])
    def test_performance_rule_exists(self, rule):
        """Test that performance rules are properly defined."""
        assert rule["id"] in ["L008", "L067"]
        assert rule["category"] == "performance"
        assert rule["constitution"] in ["Product (Initial)", "Performance"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "performance"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_performance_validation(self, test_case):
        """Test performance rule validation logic."""
        assert test_case.rule_id in ["L008", "L067"]
        assert test_case.category == "performance"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "L008":
            # Rule L008: Make things fast
            assert "fast" in test_case.test_method_name.lower() or "performance" in test_case.test_method_name.lower()
        elif test_case.rule_id == "L067":
            # Rule L067: Respect people's time
            assert "time" in test_case.test_method_name.lower() or "respect" in test_case.test_method_name.lower()
    
    def test_performance_coverage(self):
        """Test that all performance rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "performance"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {"L008", "L067"}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_performance_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in performance_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
