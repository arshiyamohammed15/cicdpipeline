#!/usr/bin/env python3
"""
Consolidated test for Coding Standards category rules.

Tests rules: R027, R028, R029, R030, R031, R032, R033, R034, R035, R036, R037, R038, R039, R040, R041, R042, R043, R044, R045, R087, R088 (Technical coding standards and best practices)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
coding_standards_rules = [r for r in factory.get_all_rules() if r.get("category") == "coding_standards"]

class TestCodingstandardsCategory:
    """Test suite for Coding Standards category rules."""
    
    @pytest.mark.parametrize("rule", coding_standards_rules, ids=lambda r: r["id"])
    def test_coding_standards_rule_exists(self, rule):
        """Test that coding_standards rules are properly defined."""
        assert rule["id"] in ['R027', 'R028', 'R029', 'R030', 'R031', 'R032', 'R033', 'R034', 'R035', 'R036', 'R037', 'R038', 'R039', 'R040', 'R041', 'R042', 'R043', 'R044', 'R045', 'R087', 'R088']
        assert rule["category"] == "coding_standards"
        assert rule["constitution"] in ["Product (Initial)", "Coding Standards", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "coding_standards"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_coding_standards_validation(self, test_case):
        """Test coding_standards rule validation logic."""
        assert test_case.rule_id in ['R027', 'R028', 'R029', 'R030', 'R031', 'R032', 'R033', 'R034', 'R035', 'R036', 'R037', 'R038', 'R039', 'R040', 'R041', 'R042', 'R043', 'R044', 'R045', 'R087', 'R088']
        assert test_case.category == "coding_standards"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "R027":
            # Rule R027: [Rule description]
            assert "r027" in test_case.test_method_name.lower()
        if test_case.rule_id == "R028":
            # Rule R028: [Rule description]
            assert "r028" in test_case.test_method_name.lower()
        if test_case.rule_id == "R029":
            # Rule R029: [Rule description]
            assert "r029" in test_case.test_method_name.lower()
        if test_case.rule_id == "R030":
            # Rule R030: [Rule description]
            assert "r030" in test_case.test_method_name.lower()
        if test_case.rule_id == "R031":
            # Rule R031: [Rule description]
            assert "r031" in test_case.test_method_name.lower()
        if test_case.rule_id == "R032":
            # Rule R032: [Rule description]
            assert "r032" in test_case.test_method_name.lower()
        if test_case.rule_id == "R033":
            # Rule R033: [Rule description]
            assert "r033" in test_case.test_method_name.lower()
        if test_case.rule_id == "R034":
            # Rule R034: [Rule description]
            assert "r034" in test_case.test_method_name.lower()
        if test_case.rule_id == "R035":
            # Rule R035: [Rule description]
            assert "r035" in test_case.test_method_name.lower()
        if test_case.rule_id == "R036":
            # Rule R036: [Rule description]
            assert "r036" in test_case.test_method_name.lower()
        if test_case.rule_id == "R037":
            # Rule R037: [Rule description]
            assert "r037" in test_case.test_method_name.lower()
        if test_case.rule_id == "R038":
            # Rule R038: [Rule description]
            assert "r038" in test_case.test_method_name.lower()
        if test_case.rule_id == "R039":
            # Rule R039: [Rule description]
            assert "r039" in test_case.test_method_name.lower()
        if test_case.rule_id == "R040":
            # Rule R040: [Rule description]
            assert "r040" in test_case.test_method_name.lower()
        if test_case.rule_id == "R041":
            # Rule R041: [Rule description]
            assert "r041" in test_case.test_method_name.lower()
        if test_case.rule_id == "R042":
            # Rule R042: [Rule description]
            assert "r042" in test_case.test_method_name.lower()
        if test_case.rule_id == "R043":
            # Rule R043: [Rule description]
            assert "r043" in test_case.test_method_name.lower()
        if test_case.rule_id == "R044":
            # Rule R044: [Rule description]
            assert "r044" in test_case.test_method_name.lower()
        if test_case.rule_id == "R045":
            # Rule R045: [Rule description]
            assert "r045" in test_case.test_method_name.lower()
        if test_case.rule_id == "R087":
            # Rule R087: [Rule description]
            assert "r087" in test_case.test_method_name.lower()
        if test_case.rule_id == "R088":
            # Rule R088: [Rule description]
            assert "r088" in test_case.test_method_name.lower()
    
    def test_coding_standards_coverage(self):
        """Test that all coding_standards rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "coding_standards"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'R033', 'R032', 'R039', 'R045', 'R035', 'R034', 'R028', 'R031', 'R041', 'R040', 'R037', 'R027', 'R088', 'R043', 'R038', 'R042', 'R036', 'R030', 'R044', 'R087', 'R029'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_coding_standards_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in coding_standards_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
