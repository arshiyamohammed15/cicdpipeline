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

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
all_rules = factory.get_all_rules()
privacy_rules = []
for r in all_rules:
    if r.get("category") in ["security", "privacy_security"]:
        privacy_rules.append(r)
    elif any(cat in r.get("categories", []) for cat in ["security", "privacy_security"]):
        privacy_rules.append(r)

class TestPrivacySecurityCategory:
    """Test suite for Privacy & Security category rules."""
    
    @pytest.mark.parametrize("rule", privacy_rules, ids=lambda r: r["id"])
    def test_privacy_security_rule_exists(self, rule):
        """Test that privacy/security rules are properly defined."""
        assert rule["id"] in ["L003", "L011", "L012", "L027", "L036"]
        assert rule["category"] in ["security", "privacy_security"]
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_privacy_security_validation(self):
        """Test privacy/security rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in privacy_rules:
            assert rule["id"] in ["L003", "L011", "L012", "L027", "L036"]
            is_privacy_security = (rule["category"] in ["security", "privacy_security"] or 
                                 any(cat in rule.get("categories", []) for cat in ["security", "privacy_security"]))
            assert is_privacy_security, f"Rule {rule['id']} should belong to privacy/security category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_privacy_security_coverage(self):
        """Test that all privacy/security rules are covered."""
        covered_rules = {rule["id"] for rule in privacy_rules}
        expected_rules = {"L003", "L011", "L012", "L027", "L036"}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_privacy_security_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in privacy_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
