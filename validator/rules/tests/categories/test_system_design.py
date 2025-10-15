#!/usr/bin/env python3
"""
Consolidated test for System Design category rules.

Tests rules: L022, L025, L026, L029, L030, L031, L032 (Architecture and system design principles)
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
system_design_rules = []
for r in all_rules:
    if r.get("category") == "system_design":
        system_design_rules.append(r)
    elif "system_design" in r.get("categories", []):
        system_design_rules.append(r)

class TestSystemdesignCategory:
    """Test suite for System Design category rules."""
    
    @pytest.mark.parametrize("rule", system_design_rules, ids=lambda r: r["id"])
    def test_system_design_rule_exists(self, rule):
        """Test that system_design rules are properly defined."""
        assert rule["id"] in ['L022', 'L025', 'L026', 'L029', 'L030', 'L031', 'L032']
        # Check if rule belongs to system_design category (primary or in categories list)
        is_system_design = (rule["category"] == "system_design" or 
                           "system_design" in rule.get("categories", []))
        assert is_system_design, f"Rule {rule['id']} should belong to system_design category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_system_design_validation(self):
        """Test system_design rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in system_design_rules:
            is_system_design = (rule["category"] == "system_design" or 
                           "system_design" in rule.get("categories", []))
            assert is_system_design, f"Rule {rule['id']} should belong to system_design category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_system_design_coverage(self):
        """Test that all system_design rules are covered."""
        covered_rules = {rule["id"] for rule in system_design_rules}
        
        expected_rules = {'L022', 'L029', 'L025', 'L026', 'L031', 'L032', 'L030'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_system_design_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in system_design_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
