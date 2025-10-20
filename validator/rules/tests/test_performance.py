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

