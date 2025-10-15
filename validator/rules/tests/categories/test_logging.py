#!/usr/bin/env python3
"""
Consolidated test for Logging category rules.

Tests rules: R043, R063, R064, R065, R066, R067, R068, R069, R070, R071, R072, R073, R074, R075 (Logging standards and troubleshooting)
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
logging_rules = []
for r in all_rules:
    if r.get("category") == "logging":
        logging_rules.append(r)
    elif "logging" in r.get("categories", []):
        logging_rules.append(r)

class TestLoggingCategory:
    """Test suite for Logging category rules."""
    
    @pytest.mark.parametrize("rule", logging_rules, ids=lambda r: r["id"])
    def test_logging_rule_exists(self, rule):
        """Test that logging rules are properly defined."""
        assert rule["id"] in ['R043', 'R063', 'R064', 'R065', 'R066', 'R067', 'R068', 'R069', 'R070', 'R071', 'R072', 'R073', 'R074', 'R075']
        # Check if rule belongs to logging category (primary or in categories list)
        is_logging = (rule["category"] == "logging" or 
                           "logging" in rule.get("categories", []))
        assert is_logging, f"Rule {rule['id']} should belong to logging category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_logging_validation(self):
        """Test logging rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in logging_rules:
            is_logging = (rule["category"] == "logging" or 
                           "logging" in rule.get("categories", []))
            assert is_logging, f"Rule {rule['id']} should belong to logging category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_logging_coverage(self):
        """Test that all logging rules are covered."""
        covered_rules = {rule["id"] for rule in logging_rules}
        
        expected_rules = {'R067', 'R064', 'R073', 'R065', 'R063', 'R069', 'R043', 'R075', 'R074', 'R068', 'R070', 'R072', 'R071', 'R066'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_logging_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in logging_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
