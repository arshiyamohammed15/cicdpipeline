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

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
all_rules = factory.get_all_rules()
coding_standards_rules = []
for r in all_rules:
    if r.get("category") == "coding_standards":
        coding_standards_rules.append(r)
    elif "coding_standards" in r.get("categories", []):
        coding_standards_rules.append(r)

class TestCodingstandardsCategory:
    """Test suite for Coding Standards category rules."""
    
    @pytest.mark.parametrize("rule", coding_standards_rules, ids=lambda r: r["id"])
    def test_coding_standards_rule_exists(self, rule):
        """Test that coding_standards rules are properly defined."""
        assert rule["id"] in ['R027', 'R028', 'R029', 'R030', 'R031', 'R032', 'R033', 'R034', 'R035', 'R036', 'R037', 'R038', 'R039', 'R040', 'R041', 'R042', 'R043', 'R044', 'R045', 'R087', 'R088']
        # Check if rule belongs to coding_standards category (primary or in categories list)
        is_coding_standards = (rule["category"] == "coding_standards" or 
                           "coding_standards" in rule.get("categories", []))
        assert is_coding_standards, f"Rule {rule['id']} should belong to coding_standards category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_coding_standards_validation(self):
        """Test coding_standards rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in coding_standards_rules:
            is_coding_standards = (rule["category"] == "coding_standards" or 
                           "coding_standards" in rule.get("categories", []))
            assert is_coding_standards, f"Rule {rule['id']} should belong to coding_standards category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_coding_standards_coverage(self):
        """Test that all coding_standards rules are covered."""
        covered_rules = {rule["id"] for rule in coding_standards_rules}
        
        expected_rules = {'R033', 'R032', 'R039', 'R045', 'R035', 'R034', 'R028', 'R031', 'R041', 'R040', 'R037', 'R027', 'R088', 'R043', 'R038', 'R042', 'R036', 'R030', 'R044', 'R087', 'R029'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_coding_standards_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in coding_standards_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
