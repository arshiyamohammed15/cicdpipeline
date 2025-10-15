#!/usr/bin/env python3
"""
Consolidated test for Privacy & Security category rules.

Tests rules: L003, L011, L012, L027, L036 (Privacy and security principles)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
privacy_rules = [r for r in factory.get_all_rules() if r.get("category") in ["security", "privacy_security"]]

class TestPrivacySecurityCategory:
    """Test suite for Privacy & Security category rules."""
    
    @pytest.mark.parametrize("rule", privacy_rules, ids=lambda r: r["id"])
    def test_privacy_security_rule_exists(self, rule):
        """Test that privacy/security rules are properly defined."""
        assert rule["id"] in ["L003", "L011", "L012", "L027", "L036"]
        assert rule["category"] in ["security", "privacy_security"]
        assert rule["constitution"] in ["Product (Initial)", "Privacy & Security"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") in ["security", "privacy_security"]), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_privacy_security_validation(self, test_case):
        """Test privacy/security rule validation logic."""
        assert test_case.rule_id in ["L003", "L011", "L012", "L027", "L036"]
        assert test_case.category in ["security", "privacy_security"]
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "L003":
            # Rule L003: Protect people's privacy
            assert "credential" in test_case.test_method_name.lower() or "privacy" in test_case.test_method_name.lower()
        elif test_case.rule_id == "L011":
            # Rule L011: Check your data
            assert "data" in test_case.test_method_name.lower() or "validation" in test_case.test_method_name.lower()
        elif test_case.rule_id == "L012":
            # Rule L012: Keep AI safe
            assert "safe" in test_case.test_method_name.lower() or "ai" in test_case.test_method_name.lower()
        elif test_case.rule_id == "L027":
            # Rule L027: Be smart about data
            assert "data" in test_case.test_method_name.lower() or "smart" in test_case.test_method_name.lower()
        elif test_case.rule_id == "L036":
            # Rule L036: Be extra careful with private data
            assert "private" in test_case.test_method_name.lower() or "careful" in test_case.test_method_name.lower()
    
    def test_privacy_security_coverage(self):
        """Test that all privacy/security rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") in ["security", "privacy_security"]):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {"L003", "L011", "L012", "L027", "L036"}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_privacy_security_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in privacy_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
