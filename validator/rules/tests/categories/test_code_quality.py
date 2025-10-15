#!/usr/bin/env python3
"""
Consolidated test for Code Quality category rules.

Tests rules: L015, L018, L068 (Code quality and documentation)
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
code_quality_rules = []
for r in all_rules:
    if r.get("category") == "code_quality":
        code_quality_rules.append(r)
    elif "code_quality" in r.get("categories", []):
        code_quality_rules.append(r)

class TestCodequalityCategory:
    """Test suite for Code Quality category rules."""
    
    @pytest.mark.parametrize("rule", code_quality_rules, ids=lambda r: r["id"])
    def test_code_quality_rule_exists(self, rule):
        """Test that code_quality rules are properly defined."""
        assert rule["id"] in ['L015', 'L018', 'L068']
        # Check if rule belongs to code_quality category (primary or in categories list)
        is_code_quality = (rule["category"] == "code_quality" or 
                           "code_quality" in rule.get("categories", []))
        assert is_code_quality, f"Rule {rule['id']} should belong to code_quality category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_code_quality_validation(self):
        """Test code_quality rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in code_quality_rules:
            is_code_quality = (rule["category"] == "code_quality" or 
                           "code_quality" in rule.get("categories", []))
            assert is_code_quality, f"Rule {rule['id']} should belong to code_quality category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_code_quality_coverage(self):
        """Test that all code_quality rules are covered."""
        covered_rules = {rule["id"] for rule in code_quality_rules}
        
        expected_rules = {'L015', 'L068', 'L018'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_code_quality_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in code_quality_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
