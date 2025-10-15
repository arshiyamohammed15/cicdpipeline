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

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
all_rules = factory.get_all_rules()
comments_rules = []
for r in all_rules:
    if r.get("category") == "comments":
        comments_rules.append(r)
    elif "comments" in r.get("categories", []):
        comments_rules.append(r)

class TestCommentsCategory:
    """Test suite for Comments category rules."""
    
    @pytest.mark.parametrize("rule", comments_rules, ids=lambda r: r["id"])
    def test_comments_rule_exists(self, rule):
        """Test that comments rules are properly defined."""
        assert rule["id"] in ['R008', 'R046', 'R047', 'R048', 'R049', 'R050', 'R051', 'R052', 'R053', 'R089']
        # Check if rule belongs to comments category (primary or in categories list)
        is_comments = (rule["category"] == "comments" or 
                           "comments" in rule.get("categories", []))
        assert is_comments, f"Rule {rule['id']} should belong to comments category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_comments_validation(self):
        """Test comments rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in comments_rules:
            is_comments = (rule["category"] == "comments" or 
                           "comments" in rule.get("categories", []))
            assert is_comments, f"Rule {rule['id']} should belong to comments category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_comments_coverage(self):
        """Test that all comments rules are covered."""
        covered_rules = {rule["id"] for rule in comments_rules}
        
        expected_rules = {'R089', 'R049', 'R047', 'R052', 'R053', 'R051', 'R046', 'R050', 'R048', 'R008'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_comments_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in comments_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
