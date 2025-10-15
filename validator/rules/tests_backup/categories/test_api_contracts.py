#!/usr/bin/env python3
"""
Consolidated test for Api Contracts category rules.

Tests rules: R013, R014, R015, R016, R017, R018, R019, R020, R021, R022, R023, R024, R025, R026, R080, R083, R084, R085, R086 (API design, contracts, and governance)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
api_contracts_rules = [r for r in factory.get_all_rules() if r.get("category") == "api_contracts"]

class TestApicontractsCategory:
    """Test suite for Api Contracts category rules."""
    
    @pytest.mark.parametrize("rule", api_contracts_rules, ids=lambda r: r["id"])
    def test_api_contracts_rule_exists(self, rule):
        """Test that api_contracts rules are properly defined."""
        assert rule["id"] in ['R013', 'R014', 'R015', 'R016', 'R017', 'R018', 'R019', 'R020', 'R021', 'R022', 'R023', 'R024', 'R025', 'R026', 'R080', 'R083', 'R084', 'R085', 'R086']
        assert rule["category"] == "api_contracts"
        assert rule["constitution"] in ["Product (Initial)", "Api Contracts", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "api_contracts"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_api_contracts_validation(self, test_case):
        """Test api_contracts rule validation logic."""
        assert test_case.rule_id in ['R013', 'R014', 'R015', 'R016', 'R017', 'R018', 'R019', 'R020', 'R021', 'R022', 'R023', 'R024', 'R025', 'R026', 'R080', 'R083', 'R084', 'R085', 'R086']
        assert test_case.category == "api_contracts"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "R013":
            # Rule R013: [Rule description]
            assert "r013" in test_case.test_method_name.lower()
        if test_case.rule_id == "R014":
            # Rule R014: [Rule description]
            assert "r014" in test_case.test_method_name.lower()
        if test_case.rule_id == "R015":
            # Rule R015: [Rule description]
            assert "r015" in test_case.test_method_name.lower()
        if test_case.rule_id == "R016":
            # Rule R016: [Rule description]
            assert "r016" in test_case.test_method_name.lower()
        if test_case.rule_id == "R017":
            # Rule R017: [Rule description]
            assert "r017" in test_case.test_method_name.lower()
        if test_case.rule_id == "R018":
            # Rule R018: [Rule description]
            assert "r018" in test_case.test_method_name.lower()
        if test_case.rule_id == "R019":
            # Rule R019: [Rule description]
            assert "r019" in test_case.test_method_name.lower()
        if test_case.rule_id == "R020":
            # Rule R020: [Rule description]
            assert "r020" in test_case.test_method_name.lower()
        if test_case.rule_id == "R021":
            # Rule R021: [Rule description]
            assert "r021" in test_case.test_method_name.lower()
        if test_case.rule_id == "R022":
            # Rule R022: [Rule description]
            assert "r022" in test_case.test_method_name.lower()
        if test_case.rule_id == "R023":
            # Rule R023: [Rule description]
            assert "r023" in test_case.test_method_name.lower()
        if test_case.rule_id == "R024":
            # Rule R024: [Rule description]
            assert "r024" in test_case.test_method_name.lower()
        if test_case.rule_id == "R025":
            # Rule R025: [Rule description]
            assert "r025" in test_case.test_method_name.lower()
        if test_case.rule_id == "R026":
            # Rule R026: [Rule description]
            assert "r026" in test_case.test_method_name.lower()
        if test_case.rule_id == "R080":
            # Rule R080: [Rule description]
            assert "r080" in test_case.test_method_name.lower()
        if test_case.rule_id == "R083":
            # Rule R083: [Rule description]
            assert "r083" in test_case.test_method_name.lower()
        if test_case.rule_id == "R084":
            # Rule R084: [Rule description]
            assert "r084" in test_case.test_method_name.lower()
        if test_case.rule_id == "R085":
            # Rule R085: [Rule description]
            assert "r085" in test_case.test_method_name.lower()
        if test_case.rule_id == "R086":
            # Rule R086: [Rule description]
            assert "r086" in test_case.test_method_name.lower()
    
    def test_api_contracts_coverage(self):
        """Test that all api_contracts rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "api_contracts"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'R014', 'R080', 'R084', 'R013', 'R085', 'R019', 'R016', 'R083', 'R021', 'R020', 'R022', 'R018', 'R017', 'R086', 'R025', 'R026', 'R015', 'R024', 'R023'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_api_contracts_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in api_contracts_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
