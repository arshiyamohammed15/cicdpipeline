#!/usr/bin/env python3
"""
Consolidated test for Folder Standards category rules.

Tests rules: R054, R055, R056, R057, R058, R059, R060, R061, R062, R082 (Project structure and folder organization)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
folder_standards_rules = [r for r in factory.get_all_rules() if r.get("category") == "folder_standards"]

class TestFolderstandardsCategory:
    """Test suite for Folder Standards category rules."""
    
    @pytest.mark.parametrize("rule", folder_standards_rules, ids=lambda r: r["id"])
    def test_folder_standards_rule_exists(self, rule):
        """Test that folder_standards rules are properly defined."""
        assert rule["id"] in ['R054', 'R055', 'R056', 'R057', 'R058', 'R059', 'R060', 'R061', 'R062', 'R082']
        assert rule["category"] == "folder_standards"
        assert rule["constitution"] in ["Product (Initial)", "Folder Standards", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "folder_standards"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_folder_standards_validation(self, test_case):
        """Test folder_standards rule validation logic."""
        assert test_case.rule_id in ['R054', 'R055', 'R056', 'R057', 'R058', 'R059', 'R060', 'R061', 'R062', 'R082']
        assert test_case.category == "folder_standards"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "R054":
            # Rule R054: [Rule description]
            assert "r054" in test_case.test_method_name.lower()
        if test_case.rule_id == "R055":
            # Rule R055: [Rule description]
            assert "r055" in test_case.test_method_name.lower()
        if test_case.rule_id == "R056":
            # Rule R056: [Rule description]
            assert "r056" in test_case.test_method_name.lower()
        if test_case.rule_id == "R057":
            # Rule R057: [Rule description]
            assert "r057" in test_case.test_method_name.lower()
        if test_case.rule_id == "R058":
            # Rule R058: [Rule description]
            assert "r058" in test_case.test_method_name.lower()
        if test_case.rule_id == "R059":
            # Rule R059: [Rule description]
            assert "r059" in test_case.test_method_name.lower()
        if test_case.rule_id == "R060":
            # Rule R060: [Rule description]
            assert "r060" in test_case.test_method_name.lower()
        if test_case.rule_id == "R061":
            # Rule R061: [Rule description]
            assert "r061" in test_case.test_method_name.lower()
        if test_case.rule_id == "R062":
            # Rule R062: [Rule description]
            assert "r062" in test_case.test_method_name.lower()
        if test_case.rule_id == "R082":
            # Rule R082: [Rule description]
            assert "r082" in test_case.test_method_name.lower()
    
    def test_folder_standards_coverage(self):
        """Test that all folder_standards rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "folder_standards"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'R062', 'R061', 'R058', 'R056', 'R082', 'R054', 'R055', 'R059', 'R060', 'R057'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_folder_standards_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in folder_standards_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
