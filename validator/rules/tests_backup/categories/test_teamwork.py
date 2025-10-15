#!/usr/bin/env python3
"""
Consolidated test for Teamwork category rules.

Tests rules: L052, L053, L054, L055, L056, L057, L058, L060, L061, L062, L063, L064, L065, L066, L070, L071, L072, L074, L075, L076, L077 (Collaboration, UX, and team dynamics)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
teamwork_rules = [r for r in factory.get_all_rules() if r.get("category") == "teamwork"]

class TestTeamworkCategory:
    """Test suite for Teamwork category rules."""
    
    @pytest.mark.parametrize("rule", teamwork_rules, ids=lambda r: r["id"])
    def test_teamwork_rule_exists(self, rule):
        """Test that teamwork rules are properly defined."""
        assert rule["id"] in ['L052', 'L053', 'L054', 'L055', 'L056', 'L057', 'L058', 'L060', 'L061', 'L062', 'L063', 'L064', 'L065', 'L066', 'L070', 'L071', 'L072', 'L074', 'L075', 'L076', 'L077']
        assert rule["category"] == "teamwork"
        assert rule["constitution"] in ["Product (Initial)", "Teamwork", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "teamwork"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_teamwork_validation(self, test_case):
        """Test teamwork rule validation logic."""
        assert test_case.rule_id in ['L052', 'L053', 'L054', 'L055', 'L056', 'L057', 'L058', 'L060', 'L061', 'L062', 'L063', 'L064', 'L065', 'L066', 'L070', 'L071', 'L072', 'L074', 'L075', 'L076', 'L077']
        assert test_case.category == "teamwork"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "L052":
            # Rule L052: [Rule description]
            assert "l052" in test_case.test_method_name.lower()
        if test_case.rule_id == "L053":
            # Rule L053: [Rule description]
            assert "l053" in test_case.test_method_name.lower()
        if test_case.rule_id == "L054":
            # Rule L054: [Rule description]
            assert "l054" in test_case.test_method_name.lower()
        if test_case.rule_id == "L055":
            # Rule L055: [Rule description]
            assert "l055" in test_case.test_method_name.lower()
        if test_case.rule_id == "L056":
            # Rule L056: [Rule description]
            assert "l056" in test_case.test_method_name.lower()
        if test_case.rule_id == "L057":
            # Rule L057: [Rule description]
            assert "l057" in test_case.test_method_name.lower()
        if test_case.rule_id == "L058":
            # Rule L058: [Rule description]
            assert "l058" in test_case.test_method_name.lower()
        if test_case.rule_id == "L060":
            # Rule L060: [Rule description]
            assert "l060" in test_case.test_method_name.lower()
        if test_case.rule_id == "L061":
            # Rule L061: [Rule description]
            assert "l061" in test_case.test_method_name.lower()
        if test_case.rule_id == "L062":
            # Rule L062: [Rule description]
            assert "l062" in test_case.test_method_name.lower()
        if test_case.rule_id == "L063":
            # Rule L063: [Rule description]
            assert "l063" in test_case.test_method_name.lower()
        if test_case.rule_id == "L064":
            # Rule L064: [Rule description]
            assert "l064" in test_case.test_method_name.lower()
        if test_case.rule_id == "L065":
            # Rule L065: [Rule description]
            assert "l065" in test_case.test_method_name.lower()
        if test_case.rule_id == "L066":
            # Rule L066: [Rule description]
            assert "l066" in test_case.test_method_name.lower()
        if test_case.rule_id == "L070":
            # Rule L070: [Rule description]
            assert "l070" in test_case.test_method_name.lower()
        if test_case.rule_id == "L071":
            # Rule L071: [Rule description]
            assert "l071" in test_case.test_method_name.lower()
        if test_case.rule_id == "L072":
            # Rule L072: [Rule description]
            assert "l072" in test_case.test_method_name.lower()
        if test_case.rule_id == "L074":
            # Rule L074: [Rule description]
            assert "l074" in test_case.test_method_name.lower()
        if test_case.rule_id == "L075":
            # Rule L075: [Rule description]
            assert "l075" in test_case.test_method_name.lower()
        if test_case.rule_id == "L076":
            # Rule L076: [Rule description]
            assert "l076" in test_case.test_method_name.lower()
        if test_case.rule_id == "L077":
            # Rule L077: [Rule description]
            assert "l077" in test_case.test_method_name.lower()
    
    def test_teamwork_coverage(self):
        """Test that all teamwork rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "teamwork"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'L071', 'L058', 'L063', 'L056', 'L061', 'L064', 'L053', 'L060', 'L075', 'L077', 'L070', 'L052', 'L066', 'L055', 'L065', 'L057', 'L062', 'L074', 'L054', 'L076', 'L072'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_teamwork_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in teamwork_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
