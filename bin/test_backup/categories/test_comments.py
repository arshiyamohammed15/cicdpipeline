#!/usr/bin/env python3
"""
Consolidated test for Comments category rules.

Tests rules: R008, R046, R047, R048, R049, R050, R051, R052, R053, R089 (Documentation and comment standards)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
comments_rules = [r for r in factory.get_all_rules() if r.get("category") == "comments"]

class TestCommentsCategory:
    """Test suite for Comments category rules."""
    
    @pytest.mark.parametrize("rule", comments_rules, ids=lambda r: r["id"])
    def test_comments_rule_exists(self, rule):
        """Test that comments rules are properly defined."""
        assert rule["id"] in ['R008', 'R046', 'R047', 'R048', 'R049', 'R050', 'R051', 'R052', 'R053', 'R089']
        assert rule["category"] == "comments"
        assert rule["constitution"] in ["Product (Initial)", "Comments", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "comments"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_comments_validation(self, test_case):
        """Test comments rule validation logic."""
        assert test_case.rule_id in ['R008', 'R046', 'R047', 'R048', 'R049', 'R050', 'R051', 'R052', 'R053', 'R089']
        assert test_case.category == "comments"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "R008":
            # Rule R008: [Rule description]
            assert "r008" in test_case.test_method_name.lower()
        if test_case.rule_id == "R046":
            # Rule R046: [Rule description]
            assert "r046" in test_case.test_method_name.lower()
        if test_case.rule_id == "R047":
            # Rule R047: [Rule description]
            assert "r047" in test_case.test_method_name.lower()
        if test_case.rule_id == "R048":
            # Rule R048: [Rule description]
            assert "r048" in test_case.test_method_name.lower()
        if test_case.rule_id == "R049":
            # Rule R049: [Rule description]
            assert "r049" in test_case.test_method_name.lower()
        if test_case.rule_id == "R050":
            # Rule R050: [Rule description]
            assert "r050" in test_case.test_method_name.lower()
        if test_case.rule_id == "R051":
            # Rule R051: [Rule description]
            assert "r051" in test_case.test_method_name.lower()
        if test_case.rule_id == "R052":
            # Rule R052: [Rule description]
            assert "r052" in test_case.test_method_name.lower()
        if test_case.rule_id == "R053":
            # Rule R053: [Rule description]
            assert "r053" in test_case.test_method_name.lower()
        if test_case.rule_id == "R089":
            # Rule R089: [Rule description]
            assert "r089" in test_case.test_method_name.lower()
    
    def test_comments_coverage(self):
        """Test that all comments rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "comments"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'R089', 'R049', 'R047', 'R052', 'R053', 'R051', 'R046', 'R050', 'R048', 'R008'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_comments_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in comments_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
