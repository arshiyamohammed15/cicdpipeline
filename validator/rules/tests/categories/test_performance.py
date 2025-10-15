#!/usr/bin/env python3
"""
Consolidated test for Performance category rules.

Tests rules: L008, L067 (Performance optimization)
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
performance_rules = []
for r in all_rules:
    if r.get("category") == "performance":
        performance_rules.append(r)
    elif "performance" in r.get("categories", []):
        performance_rules.append(r)

class TestPerformanceCategory:
    """Test suite for Performance category rules."""
    
    @pytest.mark.parametrize("rule", performance_rules, ids=lambda r: r["id"])
    def test_performance_rule_exists(self, rule):
        """Test that performance rules are properly defined."""
        assert rule["id"] in ["L008", "L067"]
        # Check if rule belongs to performance category (primary or in categories list)
        is_performance = (rule["category"] == "performance" or 
                           "performance" in rule.get("categories", []))
        assert is_performance, f"Rule {rule['id']} should belong to performance category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_performance_validation(self):
        """Test performance rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in performance_rules:
            is_performance = (rule["category"] == "performance" or 
                           "performance" in rule.get("categories", []))
            assert is_performance, f"Rule {rule['id']} should belong to performance category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_performance_coverage(self):
        """Test that all performance rules are covered."""
        covered_rules = {rule["id"] for rule in performance_rules}
        
        expected_rules = {"L008", "L067"}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_performance_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in performance_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
