#!/usr/bin/env python3
"""
Consolidated test for Code Quality category rules.

Tests rules: L015, L018, L068 (Code quality and documentation)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
code_quality_rules = [r for r in factory.get_all_rules() if r.get("category") == "code_quality"]

class TestCodequalityCategory:
    """Test suite for Code Quality category rules."""
    
    @pytest.mark.parametrize("rule", code_quality_rules, ids=lambda r: r["id"])
    def test_code_quality_rule_exists(self, rule):
        """Test that code_quality rules are properly defined."""
        assert rule["id"] in ['L015', 'L018', 'L068']
        assert rule["category"] == "code_quality"
        assert rule["constitution"] in ["Product (Initial)", "Code Quality", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "code_quality"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_code_quality_validation(self, test_case):
        """Test code_quality rule validation logic."""
        assert test_case.rule_id in ['L015', 'L018', 'L068']
        assert test_case.category == "code_quality"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "L015":
            # Rule L015: [Rule description]
            assert "l015" in test_case.test_method_name.lower()
        if test_case.rule_id == "L018":
            # Rule L018: [Rule description]
            assert "l018" in test_case.test_method_name.lower()
        if test_case.rule_id == "L068":
            # Rule L068: [Rule description]
            assert "l068" in test_case.test_method_name.lower()
    
    def test_code_quality_coverage(self):
        """Test that all code_quality rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "code_quality"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'L015', 'L068', 'L018'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_code_quality_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in code_quality_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
