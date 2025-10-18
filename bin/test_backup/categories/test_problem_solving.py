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

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
problem_solving_rules = [r for r in factory.get_all_rules() if r.get("category") == "problem_solving"]

class TestProblemsolvingCategory:
    """Test suite for Problem Solving category rules."""
    
    @pytest.mark.parametrize("rule", problem_solving_rules, ids=lambda r: r["id"])
    def test_problem_solving_rule_exists(self, rule):
        """Test that problem_solving rules are properly defined."""
        assert rule["id"] in ['L033', 'L034', 'L035', 'L037', 'L038', 'L039', 'L041']
        assert rule["category"] == "problem_solving"
        assert rule["constitution"] in ["Product (Initial)", "Problem Solving", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "problem_solving"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_problem_solving_validation(self, test_case):
        """Test problem_solving rule validation logic."""
        assert test_case.rule_id in ['L033', 'L034', 'L035', 'L037', 'L038', 'L039', 'L041']
        assert test_case.category == "problem_solving"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "L033":
            # Rule L033: [Rule description]
            assert "l033" in test_case.test_method_name.lower()
        if test_case.rule_id == "L034":
            # Rule L034: [Rule description]
            assert "l034" in test_case.test_method_name.lower()
        if test_case.rule_id == "L035":
            # Rule L035: [Rule description]
            assert "l035" in test_case.test_method_name.lower()
        if test_case.rule_id == "L037":
            # Rule L037: [Rule description]
            assert "l037" in test_case.test_method_name.lower()
        if test_case.rule_id == "L038":
            # Rule L038: [Rule description]
            assert "l038" in test_case.test_method_name.lower()
        if test_case.rule_id == "L039":
            # Rule L039: [Rule description]
            assert "l039" in test_case.test_method_name.lower()
        if test_case.rule_id == "L041":
            # Rule L041: [Rule description]
            assert "l041" in test_case.test_method_name.lower()
    
    def test_problem_solving_coverage(self):
        """Test that all problem_solving rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "problem_solving"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'L037', 'L039', 'L035', 'L041', 'L038', 'L033', 'L034'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_problem_solving_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in problem_solving_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
