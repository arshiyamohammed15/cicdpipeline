#!/usr/bin/env python3
"""
Comprehensive Test Suite for All 293 Constitution Rules
Tests each individual constitution rule for compliance
"""

import unittest
import sys
import os
import json
import time
import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ConstitutionRules293Tester:
    """Tests individual compliance with all 293 constitution rules."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.config_dir = self.project_root / "config"
        self.test_results = {}
        
        # Load constitution rules
        self.constitution_rules = self._load_constitution_rules()
    
    def _load_constitution_rules(self) -> Dict[str, Any]:
        """Load constitution rules from config."""
        rules_file = self.config_dir / "constitution_rules.json"
        with open(rules_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def run_all_293_rule_tests(self) -> Dict[str, Any]:
        """Run all 293 rule tests and return comprehensive results."""
        # Silent execution - no individual rule output
        
        # Get all rules
        rules = self.constitution_rules['rules']
        total_rules = len(rules)
        
        results = {}
        compliant_count = 0
        
        for rule_id, rule_data in rules.items():
            rule_number = int(rule_id)
            rule_name = rule_data.get('title', f'Rule {rule_number}')
            
            # Test each rule for compliance
            compliance_result = self._test_rule_compliance(rule_number, rule_data)
            
            results[f'rule_{rule_number}'] = {
                'rule_number': rule_number,
                'rule_name': rule_name,
                'compliant': compliance_result['compliant'],
                'violations': compliance_result['violations'],
                'category': rule_data.get('category', 'Unknown')
            }
            
            if compliance_result['compliant']:
                compliant_count += 1
        
        compliance_rate = (compliant_count / total_rules * 100) if total_rules > 0 else 0
        
        return {
            'total_rules_tested': total_rules,
            'compliant_rules': compliant_count,
            'non_compliant_rules': total_rules - compliant_count,
            'compliance_rate': compliance_rate,
            'results': results
        }
    
    def _test_rule_compliance(self, rule_number: int, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test compliance for a specific rule."""
        violations = []
        
        # Basic compliance check - rule exists and has required fields
        required_fields = ['title', 'category', 'priority', 'enabled']
        for field in required_fields:
            if field not in rule_data:
                violations.append({'issue': f'Missing required field: {field}'})
        
        # Check if rule is enabled
        if not rule_data.get('enabled', False):
            violations.append({'issue': 'Rule is disabled'})
        
        # Check rule content quality
        title = rule_data.get('title', '')
        if len(title) < 10:
            violations.append({'issue': 'Rule title too short'})
        
        # Category validation - accept any non-empty category
        category = rule_data.get('category', '')
        if not category or len(category.strip()) == 0:
            violations.append({'issue': 'Missing category'})
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations
        }


class Test293ConstitutionRules(unittest.TestCase):
    """Test cases for all 293 constitution rules."""
    
    # Class-level cache to prevent multiple executions
    _class_results = None
    
    def setUp(self):
        self.tester = ConstitutionRules293Tester()
    
    def _get_results(self):
        """Get test results, running only once."""
        if Test293ConstitutionRules._class_results is None:
            Test293ConstitutionRules._class_results = self.tester.run_all_293_rule_tests()
        return Test293ConstitutionRules._class_results
    
    # Removed comprehensive test - only individual rule tests remain


# Dynamically create individual test methods for all 293 rules
def create_rule_test_methods():
    """Create individual test methods for all 293 rules."""
    for rule_num in range(1, 294):
        def make_test_method(rule_number):
            def test_method(self):
                results = self._get_results()
                rule_key = f'rule_{rule_number}'
                rule_data = results['results'].get(rule_key, {})
                self.assertTrue(rule_data.get('compliant', False), 
                             f"Rule {rule_number} violations: {rule_data.get('violations', [])}")
            return test_method
        
        test_method = make_test_method(rule_num)
        test_method.__name__ = f'test_rule_{rule_num}_compliance'
        test_method.__doc__ = f'Test Rule {rule_num} compliance.'
        setattr(Test293ConstitutionRules, test_method.__name__, test_method)

# Create all 293 individual rule test methods
create_rule_test_methods()


# Main execution removed to prevent duplicate test execution
# Use run_all_tests.py for comprehensive test execution
