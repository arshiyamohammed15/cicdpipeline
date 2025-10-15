#!/usr/bin/env python3
"""
Consolidated test for Folder Standards category rules.

Tests rules: R054, R055, R056, R057, R058, R059, R060, R061, R062, R082 (Project structure and folder organization)
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
folder_standards_rules = []
for r in all_rules:
    if r.get("category") == "folder_standards":
        folder_standards_rules.append(r)
    elif "folder_standards" in r.get("categories", []):
        folder_standards_rules.append(r)

class TestFolderstandardsCategory:
    """Test suite for Folder Standards category rules."""
    
    @pytest.mark.parametrize("rule", folder_standards_rules, ids=lambda r: r["id"])
    def test_folder_standards_rule_exists(self, rule):
        """Test that folder_standards rules are properly defined."""
        assert rule["id"] in ['R054', 'R055', 'R056', 'R057', 'R058', 'R059', 'R060', 'R061', 'R062', 'R082']
        # Check if rule belongs to folder_standards category (primary or in categories list)
        is_folder_standards = (rule["category"] == "folder_standards" or 
                           "folder_standards" in rule.get("categories", []))
        assert is_folder_standards, f"Rule {rule['id']} should belong to folder_standards category"
        assert rule["priority"] in ("critical", "important", "recommended")
        assert "description" in rule
    
    def test_folder_standards_validation(self):
        """Test folder_standards rule validation logic."""
        # Test that all rules in this category are properly defined
        for rule in folder_standards_rules:
            is_folder_standards = (rule["category"] == "folder_standards" or 
                           "folder_standards" in rule.get("categories", []))
            assert is_folder_standards, f"Rule {rule['id']} should belong to folder_standards category"
            assert rule["priority"] in ("critical", "important", "recommended")
            assert "description" in rule
    
    def test_folder_standards_coverage(self):
        """Test that all folder_standards rules are covered."""
        covered_rules = {rule["id"] for rule in folder_standards_rules}
        
        expected_rules = {'R062', 'R061', 'R058', 'R056', 'R082', 'R054', 'R055', 'R059', 'R060', 'R057'}
        assert covered_rules == expected_rules, f"Missing rules: {expected_rules - covered_rules}"
    
    def test_folder_standards_rule_metadata_consistency(self):
        """Test that rule metadata is consistent across the factory."""
        for rule in folder_standards_rules:
            rule_id = rule["id"]
            all_rules = factory.get_all_rules()
            factory_rule = next((r for r in all_rules if r["id"] == rule_id), None)
            assert factory_rule is not None, f"Rule {rule_id} not found in factory"
            assert rule == factory_rule, f"Metadata inconsistency for rule {rule_id}"
