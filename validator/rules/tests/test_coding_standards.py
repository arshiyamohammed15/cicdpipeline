"""
Tests for Coding Standards Validator

Tests coding standards and best practices validation.
"""

import unittest
from validator.rules.coding_standards import CodingStandardsValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestCodingStandardsValidator(unittest.TestCase):
    """Test suite for coding standards rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = CodingStandardsValidator()
        self.test_file_path = "test.py"
    
    def test_validate_runs_without_error(self):
        """Test validate() executes successfully."""
        content = '''
def well_named_function(param_one: str, param_two: int) -> bool:
    """Function following coding standards."""
    return True
'''
        try:
            violations = self.validator.validate(self.test_file_path, content)
            self.assertIsInstance(violations, list)
        except Exception as e:
            self.fail(f"validate() raised {type(e).__name__}: {e}")


if __name__ == '__main__':
    unittest.main()

