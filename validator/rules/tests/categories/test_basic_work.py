#!/usr/bin/env python3
"""
Consolidated test for Basic Work category rules.

Tests rules: L004, L005, L010, L013, L020 (Core principles for all development work)
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
basic_work_rules = []
for r in all_rules:
    if r.get("category") == "basic_work":
        basic_work_rules.append(r)
    elif "basic_work" in r.get("categories", []):
        basic_work_rules.append(r)

class TestBasicWorkCategory:
    """Test suite for Basic Work category rules."""
    
    @pytest.mark.parametrize("rule", basic_work_rules, ids=lambda r: r["id"])
    def test_basic_work_rule_exists(self, rule):
        """Test that basic work rules are properly defined."""
        assert rule["id"] in ["R004", "R005", "R010", "R013", "R020"]
        # Check if rule belongs to basic_work category (primary or in categories list)
        is_basic_work = (rule["category"] == "basic_work" or 
                        "basic_work" in rule.get("categories", []))
        assert is_basic_work, f"Rule {rule['id']} should belong to basic_work category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_basic_work_validation(self):
        """Test basic work rule validation logic."""
        # Test that we have the expected basic work rules
        basic_work_rule_ids = {rule["id"] for rule in basic_work_rules}
        expected_rule_ids = {"R004", "R005", "R010", "R013", "R020"}
        
        assert basic_work_rule_ids == expected_rule_ids, f"Expected {expected_rule_ids}, got {basic_work_rule_ids}"
        
        # Test that each rule has the required fields
        for rule in basic_work_rules:
            assert "id" in rule
            assert "category" in rule
            assert "priority" in rule
            assert "description" in rule
            # Check if rule belongs to basic_work category (primary or in categories list)
            is_basic_work = (rule["category"] == "basic_work" or 
                            "basic_work" in rule.get("categories", []))
            assert is_basic_work, f"Rule {rule['id']} should belong to basic_work category"
    
    def test_basic_work_coverage(self):
        """Test that all basic work rules are covered."""
        covered_rules = {rule["id"] for rule in basic_work_rules}
        expected_rules = {"R004", "R005", "R010", "R013", "R020"}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_basic_work_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        all_rules = factory.get_all_rules()
        for rule in basic_work_rules:
            rule_id = rule["id"]
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
