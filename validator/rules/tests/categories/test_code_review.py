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

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
all_rules = factory.get_all_rules()
code_review_rules = []
for r in all_rules:
    if r.get("category") == "code_review":
        code_review_rules.append(r)
    elif "code_review" in r.get("categories", []):
        code_review_rules.append(r)

class TestCodereviewCategory:
    """Test suite for Code Review category rules."""
    
    @pytest.mark.parametrize("rule", code_review_rules, ids=lambda r: r["id"])
    def test_code_review_rule_exists(self, rule):
        """Test that code_review rules are properly defined."""
        assert rule["id"] in ['R001', 'R002', 'R003', 'R004', 'R005', 'R006', 'R007', 'R008', 'R009', 'R010', 'R011', 'R012', 'R076', 'R077', 'R081']
        # Check if rule belongs to code_review category (primary or in categories list)
        is_code_review = (rule["category"] == "code_review" or 
                           "code_review" in rule.get("categories", []))
        assert is_code_review, f"Rule {rule['id']} should belong to code_review category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_code_review_validation(self):
        """Test code_review rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in code_review_rules:
            is_code_review = (rule["category"] == "code_review" or 
                           "code_review" in rule.get("categories", []))
            assert is_code_review, f"Rule {rule['id']} should belong to code_review category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_code_review_coverage(self):
        """Test that all code_review rules are covered."""
        covered_rules = {rule["id"] for rule in code_review_rules}
        
        expected_rules = {'R005', 'R004', 'R012', 'R006', 'R010', 'R076', 'R011', 'R009', 'R077', 'R007', 'R002', 'R081', 'R003', 'R001', 'R008'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_code_review_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in code_review_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
