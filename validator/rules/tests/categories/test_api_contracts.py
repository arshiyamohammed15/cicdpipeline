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

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
all_rules = factory.get_all_rules()
api_contracts_rules = []
for r in all_rules:
    if r.get("category") == "api_contracts":
        api_contracts_rules.append(r)
    elif "api_contracts" in r.get("categories", []):
        api_contracts_rules.append(r)

class TestApicontractsCategory:
    """Test suite for Api Contracts category rules."""
    
    @pytest.mark.parametrize("rule", api_contracts_rules, ids=lambda r: r["id"])
    def test_api_contracts_rule_exists(self, rule):
        """Test that api_contracts rules are properly defined."""
        assert rule["id"] in ['R013', 'R014', 'R015', 'R016', 'R017', 'R018', 'R019', 'R020', 'R021', 'R022', 'R023', 'R024', 'R025', 'R026', 'R080', 'R083', 'R084', 'R085', 'R086']
        # Check if rule belongs to api_contracts category (primary or in categories list)
        is_api_contracts = (rule["category"] == "api_contracts" or 
                           "api_contracts" in rule.get("categories", []))
        assert is_api_contracts, f"Rule {rule['id']} should belong to api_contracts category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_api_contracts_validation(self):
        """Test api_contracts rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in api_contracts_rules:
            assert rule["id"] in ['R013', 'R014', 'R015', 'R016', 'R017', 'R018', 'R019', 'R020', 'R021', 'R022', 'R023', 'R024', 'R025', 'R026', 'R080', 'R083', 'R084', 'R085', 'R086']
            is_api_contracts = (rule["category"] == "api_contracts" or 
                               "api_contracts" in rule.get("categories", []))
            assert is_api_contracts, f"Rule {rule['id']} should belong to api_contracts category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_api_contracts_coverage(self):
        """Test that all api_contracts rules are covered."""
        covered_rules = {rule["id"] for rule in api_contracts_rules}
        expected_rules = {'R014', 'R080', 'R084', 'R013', 'R085', 'R019', 'R016', 'R083', 'R021', 'R020', 'R022', 'R018', 'R017', 'R086', 'R025', 'R026', 'R015', 'R024', 'R023'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_api_contracts_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        all_rules = factory.get_all_rules()
        for rule in api_contracts_rules:
            rule_id = rule["id"]
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
