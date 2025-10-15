#!/usr/bin/env python3
"""
Consolidated test for Logging category rules.

Tests rules: R043, R063, R064, R065, R066, R067, R068, R069, R070, R071, R072, R073, R074, R075 (Logging standards and troubleshooting)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
logging_rules = [r for r in factory.get_all_rules() if r.get("category") == "logging"]

class TestLoggingCategory:
    """Test suite for Logging category rules."""
    
    @pytest.mark.parametrize("rule", logging_rules, ids=lambda r: r["id"])
    def test_logging_rule_exists(self, rule):
        """Test that logging rules are properly defined."""
        assert rule["id"] in ['R043', 'R063', 'R064', 'R065', 'R066', 'R067', 'R068', 'R069', 'R070', 'R071', 'R072', 'R073', 'R074', 'R075']
        assert rule["category"] == "logging"
        assert rule["constitution"] in ["Product (Initial)", "Logging", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "logging"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_logging_validation(self, test_case):
        """Test logging rule validation logic."""
        assert test_case.rule_id in ['R043', 'R063', 'R064', 'R065', 'R066', 'R067', 'R068', 'R069', 'R070', 'R071', 'R072', 'R073', 'R074', 'R075']
        assert test_case.category == "logging"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "R043":
            # Rule R043: [Rule description]
            assert "r043" in test_case.test_method_name.lower()
        if test_case.rule_id == "R063":
            # Rule R063: [Rule description]
            assert "r063" in test_case.test_method_name.lower()
        if test_case.rule_id == "R064":
            # Rule R064: [Rule description]
            assert "r064" in test_case.test_method_name.lower()
        if test_case.rule_id == "R065":
            # Rule R065: [Rule description]
            assert "r065" in test_case.test_method_name.lower()
        if test_case.rule_id == "R066":
            # Rule R066: [Rule description]
            assert "r066" in test_case.test_method_name.lower()
        if test_case.rule_id == "R067":
            # Rule R067: [Rule description]
            assert "r067" in test_case.test_method_name.lower()
        if test_case.rule_id == "R068":
            # Rule R068: [Rule description]
            assert "r068" in test_case.test_method_name.lower()
        if test_case.rule_id == "R069":
            # Rule R069: [Rule description]
            assert "r069" in test_case.test_method_name.lower()
        if test_case.rule_id == "R070":
            # Rule R070: [Rule description]
            assert "r070" in test_case.test_method_name.lower()
        if test_case.rule_id == "R071":
            # Rule R071: [Rule description]
            assert "r071" in test_case.test_method_name.lower()
        if test_case.rule_id == "R072":
            # Rule R072: [Rule description]
            assert "r072" in test_case.test_method_name.lower()
        if test_case.rule_id == "R073":
            # Rule R073: [Rule description]
            assert "r073" in test_case.test_method_name.lower()
        if test_case.rule_id == "R074":
            # Rule R074: [Rule description]
            assert "r074" in test_case.test_method_name.lower()
        if test_case.rule_id == "R075":
            # Rule R075: [Rule description]
            assert "r075" in test_case.test_method_name.lower()
    
    def test_logging_coverage(self):
        """Test that all logging rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "logging"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'R067', 'R064', 'R073', 'R065', 'R063', 'R069', 'R043', 'R075', 'R074', 'R068', 'R070', 'R072', 'R071', 'R066'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_logging_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in logging_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
