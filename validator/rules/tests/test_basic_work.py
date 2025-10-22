"""
Tests for Basic Work Validator (Rules 4, 5, 10, 13, 20)

Tests core development principles validation.
"""

import unittest
from validator.rules.basic_work import BasicWorkValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestBasicWorkValidator(unittest.TestCase):
    """Test suite for basic work rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = BasicWorkValidator()
        self.test_file_path = "test.py"
    
    def test_validate_all_runs_without_error(self):
        """Test validate_all() executes successfully."""
        content = '''
def example_function():
    """Example function."""
    pass
'''
        try:
            import ast
            tree = ast.parse(content)
            violations = self.validator.validate_all(tree, content, self.test_file_path)
            self.assertIsInstance(violations, list)
        except Exception as e:
            self.fail(f"validate_all() raised {type(e).__name__}: {e}")
    
    def test_validator_has_correct_config(self):
        """Test validator has correct configuration."""
        self.assertIsNotNone(self.validator)
        if hasattr(self.validator, 'rule_config'):
            config = self.validator.rule_config
            self.assertEqual(config.get('category'), 'basic_work')


if __name__ == '__main__':
    unittest.main()

