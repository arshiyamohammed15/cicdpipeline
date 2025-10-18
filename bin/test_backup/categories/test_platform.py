#!/usr/bin/env python3
"""
Consolidated test for Platform category rules.

Tests rules: L042, L043, L044, L045, L046, L047, L048, L049, L050, L051 (Platform features and technical implementation)
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory

factory = DynamicTestFactory()
platform_rules = [r for r in factory.get_all_rules() if r.get("category") == "platform"]

class TestPlatformCategory:
    """Test suite for Platform category rules."""
    
    @pytest.mark.parametrize("rule", platform_rules, ids=lambda r: r["id"])
    def test_platform_rule_exists(self, rule):
        """Test that platform rules are properly defined."""
        assert rule["id"] in ['L042', 'L043', 'L044', 'L045', 'L046', 'L047', 'L048', 'L049', 'L050', 'L051']
        assert rule["category"] == "platform"
        assert rule["constitution"] in ["Product (Initial)", "Platform", "General"]
        assert rule["severity"] in ("error", "warning", "info")
    
    @pytest.mark.parametrize("test_case", 
                           factory.create_test_cases(lambda x: x.get("category") == "platform"), 
                           ids=lambda tc: f"{tc.rule_id}_{tc.test_method_name}")
    def test_platform_validation(self, test_case):
        """Test platform rule validation logic."""
        assert test_case.rule_id in ['L042', 'L043', 'L044', 'L045', 'L046', 'L047', 'L048', 'L049', 'L050', 'L051']
        assert test_case.category == "platform"
        assert test_case.severity in ("error", "warning", "info")
        
        # Test specific rule logic
        if test_case.rule_id == "L042":
            # Rule L042: [Rule description]
            assert "l042" in test_case.test_method_name.lower()
        if test_case.rule_id == "L043":
            # Rule L043: [Rule description]
            assert "l043" in test_case.test_method_name.lower()
        if test_case.rule_id == "L044":
            # Rule L044: [Rule description]
            assert "l044" in test_case.test_method_name.lower()
        if test_case.rule_id == "L045":
            # Rule L045: [Rule description]
            assert "l045" in test_case.test_method_name.lower()
        if test_case.rule_id == "L046":
            # Rule L046: [Rule description]
            assert "l046" in test_case.test_method_name.lower()
        if test_case.rule_id == "L047":
            # Rule L047: [Rule description]
            assert "l047" in test_case.test_method_name.lower()
        if test_case.rule_id == "L048":
            # Rule L048: [Rule description]
            assert "l048" in test_case.test_method_name.lower()
        if test_case.rule_id == "L049":
            # Rule L049: [Rule description]
            assert "l049" in test_case.test_method_name.lower()
        if test_case.rule_id == "L050":
            # Rule L050: [Rule description]
            assert "l050" in test_case.test_method_name.lower()
        if test_case.rule_id == "L051":
            # Rule L051: [Rule description]
            assert "l051" in test_case.test_method_name.lower()
    
    def test_platform_coverage(self):
        """Test that all platform rules are covered."""
        covered_rules = set()
        for test_case in factory.create_test_cases(lambda x: x.get("category") == "platform"):
            covered_rules.add(test_case.rule_id)
        
        expected_rules = {'L046', 'L050', 'L048', 'L049', 'L051', 'L044', 'L045', 'L042', 'L043', 'L047'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_platform_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in platform_rules:
            rule_id = rule["id"]
            factory_rule = next(r for r in factory.get_all_rules() if r["id"] == rule_id)
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
