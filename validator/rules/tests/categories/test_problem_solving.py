#!/usr/bin/env python3
"""
Consolidated test for Problem Solving category rules.

Tests rules: L033, L034, L035, L037, L038, L039, L041 (Feature development and problem-solving approach)
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
problem_solving_rules = []
for r in all_rules:
    if r.get("category") == "problem_solving":
        problem_solving_rules.append(r)
    elif "problem_solving" in r.get("categories", []):
        problem_solving_rules.append(r)

class TestProblemsolvingCategory:
    """Test suite for Problem Solving category rules."""
    
    @pytest.mark.parametrize("rule", problem_solving_rules, ids=lambda r: r["id"])
    def test_problem_solving_rule_exists(self, rule):
        """Test that problem_solving rules are properly defined."""
        assert rule["id"] in ['L033', 'L034', 'L035', 'L037', 'L038', 'L039', 'L041']
        # Check if rule belongs to problem_solving category (primary or in categories list)
        is_problem_solving = (rule["category"] == "problem_solving" or 
                           "problem_solving" in rule.get("categories", []))
        assert is_problem_solving, f"Rule {rule['id']} should belong to problem_solving category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_problem_solving_validation(self):
        """Test problem_solving rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in problem_solving_rules:
            is_problem_solving = (rule["category"] == "problem_solving" or 
                           "problem_solving" in rule.get("categories", []))
            assert is_problem_solving, f"Rule {rule['id']} should belong to problem_solving category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_problem_solving_coverage(self):
        """Test that all problem_solving rules are covered."""
        covered_rules = {rule["id"] for rule in problem_solving_rules}
        
        expected_rules = {'L037', 'L039', 'L035', 'L041', 'L038', 'L033', 'L034'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_problem_solving_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in problem_solving_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
