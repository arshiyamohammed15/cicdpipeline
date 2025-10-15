#!/usr/bin/env python3
"""
Consolidated test for Architecture category rules.

Tests rules: L019, L021, L023, L024, L028 (Architecture and system design)
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
architecture_rules = []
for r in all_rules:
    if r.get("category") == "architecture":
        architecture_rules.append(r)
    elif "architecture" in r.get("categories", []):
        architecture_rules.append(r)

class TestArchitectureCategory:
    """Test suite for Architecture category rules."""
    
    @pytest.mark.parametrize("rule", architecture_rules, ids=lambda r: r["id"])
    def test_architecture_rule_exists(self, rule):
        """Test that architecture rules are properly defined."""
        assert rule["id"] in ['L019', 'L021', 'L023', 'L024', 'L028']
        # Check if rule belongs to architecture category (primary or in categories list)
        is_architecture = (rule["category"] == "architecture" or 
                           "architecture" in rule.get("categories", []))
        assert is_architecture, f"Rule {rule['id']} should belong to architecture category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_architecture_validation(self):
        """Test architecture rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in architecture_rules:
            assert rule["id"] in ['L019', 'L021', 'L023', 'L024', 'L028']
            is_architecture = (rule["category"] == "architecture" or 
                             "architecture" in rule.get("categories", []))
            assert is_architecture, f"Rule {rule['id']} should belong to architecture category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_architecture_coverage(self):
        """Test that all architecture rules are covered."""
        covered_rules = {rule["id"] for rule in architecture_rules}
        
        expected_rules = {'L023', 'L019', 'L028', 'L021', 'L024'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_architecture_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in architecture_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
