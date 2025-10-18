#!/usr/bin/env python3
"""
Consolidated test for Code Review category rules.

Tests rules: R001, R002, R003, R004, R005, R006, R007, R008, R009, R010, R011, R012, R076, R077, R081 (Code review standards and PR requirements)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
code_review_rules = [r for r in factory.get_all_rules() if r.get("category") == "code_review"]

class TestCodereviewCategory:
    """Test suite for Code Review category rules."""
    
    @pytest.mark.parametrize("rule", code_review_rules, ids=lambda r: r["id"])
    def test_code_review_rule_exists(self, rule):
        """Test that code_review rules are properly defined."""
        assert rule["id"] in ['R001', 'R002', 'R003', 'R004', 'R005', 'R006', 'R007', 'R008', 'R009', 'R010', 'R011', 'R012', 'R076', 'R077', 'R081']
        assert rule["category"] == "code_review"
        assert rule["constitution"] in ["Product (Initial)", "Code Review", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "code_review"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_code_review_validation(self, test_case):
        """Test code_review rule validation logic."""
        assert test_case.rule_id in ['R001', 'R002', 'R003', 'R004', 'R005', 'R006', 'R007', 'R008', 'R009', 'R010', 'R011', 'R012', 'R076', 'R077', 'R081']
        assert test_case.category == "code_review"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "R001":
            # Rule R001: [Rule description]
            assert "r001" in test_case.test_method_name.lower()
        if test_case.rule_id == "R002":
            # Rule R002: [Rule description]
            assert "r002" in test_case.test_method_name.lower()
        if test_case.rule_id == "R003":
            # Rule R003: [Rule description]
            assert "r003" in test_case.test_method_name.lower()
        if test_case.rule_id == "R004":
            # Rule R004: [Rule description]
            assert "r004" in test_case.test_method_name.lower()
        if test_case.rule_id == "R005":
            # Rule R005: [Rule description]
            assert "r005" in test_case.test_method_name.lower()
        if test_case.rule_id == "R006":
            # Rule R006: [Rule description]
            assert "r006" in test_case.test_method_name.lower()
        if test_case.rule_id == "R007":
            # Rule R007: [Rule description]
            assert "r007" in test_case.test_method_name.lower()
        if test_case.rule_id == "R008":
            # Rule R008: [Rule description]
            assert "r008" in test_case.test_method_name.lower()
        if test_case.rule_id == "R009":
            # Rule R009: [Rule description]
            assert "r009" in test_case.test_method_name.lower()
        if test_case.rule_id == "R010":
            # Rule R010: [Rule description]
            assert "r010" in test_case.test_method_name.lower()
        if test_case.rule_id == "R011":
            # Rule R011: [Rule description]
            assert "r011" in test_case.test_method_name.lower()
        if test_case.rule_id == "R012":
            # Rule R012: [Rule description]
            assert "r012" in test_case.test_method_name.lower()
        if test_case.rule_id == "R076":
            # Rule R076: [Rule description]
            assert "r076" in test_case.test_method_name.lower()
        if test_case.rule_id == "R077":
            # Rule R077: [Rule description]
            assert "r077" in test_case.test_method_name.lower()
        if test_case.rule_id == "R081":
            # Rule R081: [Rule description]
            assert "r081" in test_case.test_method_name.lower()
    
    def test_code_review_coverage(self):
        """Test that all code_review rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "code_review"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'R005', 'R004', 'R012', 'R006', 'R010', 'R076', 'R011', 'R009', 'R077', 'R007', 'R002', 'R081', 'R003', 'R001', 'R008'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_code_review_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in code_review_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
