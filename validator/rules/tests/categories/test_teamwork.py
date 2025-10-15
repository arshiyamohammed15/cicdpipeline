#!/usr/bin/env python3
"""
Consolidated test for Teamwork category rules.

Tests rules: L052, L053, L054, L055, L056, L057, L058, L060, L061, L062, L063, L064, L065, L066, L070, L071, L072, L074, L075, L076, L077 (Collaboration, UX, and team dynamics)
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
teamwork_rules = []
for r in all_rules:
    if r.get("category") == "teamwork":
        teamwork_rules.append(r)
    elif "teamwork" in r.get("categories", []):
        teamwork_rules.append(r)

class TestTeamworkCategory:
    """Test suite for Teamwork category rules."""
    
    @pytest.mark.parametrize("rule", teamwork_rules, ids=lambda r: r["id"])
    def test_teamwork_rule_exists(self, rule):
        """Test that teamwork rules are properly defined."""
        assert rule["id"] in ['L052', 'L053', 'L054', 'L055', 'L056', 'L057', 'L058', 'L060', 'L061', 'L062', 'L063', 'L064', 'L065', 'L066', 'L070', 'L071', 'L072', 'L074', 'L075', 'L076', 'L077']
        # Check if rule belongs to teamwork category (primary or in categories list)
        is_teamwork = (rule["category"] == "teamwork" or 
                           "teamwork" in rule.get("categories", []))
        assert is_teamwork, f"Rule {rule['id']} should belong to teamwork category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_teamwork_validation(self):
        """Test teamwork rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in teamwork_rules:
            is_teamwork = (rule["category"] == "teamwork" or 
                           "teamwork" in rule.get("categories", []))
            assert is_teamwork, f"Rule {rule['id']} should belong to teamwork category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_teamwork_coverage(self):
        """Test that all teamwork rules are covered."""
        covered_rules = {rule["id"] for rule in teamwork_rules}
        
        expected_rules = {'L071', 'L058', 'L063', 'L056', 'L061', 'L064', 'L053', 'L060', 'L075', 'L077', 'L070', 'L052', 'L066', 'L055', 'L065', 'L057', 'L062', 'L074', 'L054', 'L076', 'L072'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_teamwork_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in teamwork_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
