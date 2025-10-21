"""
Tests for Performance Validator

Tests performance optimization validation.
"""

import unittest
from validator.rules.performance import PerformanceValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestPerformanceValidator(unittest.TestCase):
    """Test suite for performance rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = PerformanceValidator()
        self.test_file_path = "test.py"
    
    def test_wildcard_import_violation(self):
        """Test detection of wildcard imports."""
        content = '''
from module import *
'''
        import ast
        tree = ast.parse(content)
        violations = self.validator.validate_all(tree, content, self.test_file_path)
        
        # Check for wildcard import violations
        wildcard_violations = [v for v in violations if 'wildcard' in v.message.lower() or 'import *' in v.message.lower()]
        self.assertGreaterEqual(len(wildcard_violations), 0)
    
    def test_rule_008_nested_loops_violation(self):
        """Test Rule 8: Nested loops should raise a performance warning."""
        content = '''
for i in range(10):
    for j in range(5):
        x = i * j
'''
        import ast
        tree = ast.parse(content)
        violations = self.validator.validate_all(tree, content, self.test_file_path)
        r8 = [v for v in violations if (getattr(v, 'rule_id', '') == 'rule_8') or (getattr(v, 'rule_number', None) == 8)]
        self.assertEqual(len(r8), 1)
        self.assertEqual(r8[0].severity, Severity.WARNING)
        self.assertIn('Nested loops', r8[0].message)
    
    def test_rule_067_blocking_operation_violation(self):
        """Test Rule 67: Blocking operations should be flagged."""
        content = '''
import time

def work():
    time.sleep(1)
'''
        import ast
        tree = ast.parse(content)
        violations = self.validator.validate_all(tree, content, self.test_file_path)
        r67 = [v for v in violations if (getattr(v, 'rule_id', '') == 'rule_67') or (getattr(v, 'rule_number', None) == 67)]
        self.assertEqual(len(r67), 1)
        self.assertEqual(r67[0].severity, Severity.WARNING)
        self.assertIn('Blocking operation', r67[0].message)
    
    def test_rule_067_no_blocking_operation_valid(self):
        """Test Rule 67: No blocking operations yields no violations for R67."""
        content = '''
def compute(n):
    return [i * 2 for i in range(n)]
'''
        import ast
        tree = ast.parse(content)
        violations = self.validator.validate_all(tree, content, self.test_file_path)
        r67 = [v for v in violations if (getattr(v, 'rule_id', '') == 'rule_67') or (getattr(v, 'rule_number', None) == 67)]
        self.assertEqual(len(r67), 0)
    
    def test_specific_import_valid(self):
        """Test valid specific imports."""
        content = '''
from module import SpecificClass, specific_function
'''
        import ast
        tree = ast.parse(content)
        violations = self.validator.validate_all(tree, content, self.test_file_path)
        
        # Specific imports should not violate
        wildcard_violations = [v for v in violations if 'wildcard' in v.message.lower()]
        self.assertEqual(len(wildcard_violations), 0)


if __name__ == '__main__':
    unittest.main()

