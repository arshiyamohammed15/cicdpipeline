"""
Tests for Code Review Validator

Tests code review standards validation.
"""

import unittest
from validator.rules.code_review import CodeReviewValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestCodeReviewValidator(unittest.TestCase):
    """Test suite for code review rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = CodeReviewValidator()
        self.test_file_path = "test.py"
    
    def test_validate_runs_without_error(self):
        """Test validate() executes successfully."""
        content = '''
def reviewed_function():
    """Function ready for code review."""
    return True
'''
        try:
            violations = self.validator.validate(self.test_file_path, content)
            self.assertIsInstance(violations, list)
        except Exception as e:
            self.fail(f"validate() raised {type(e).__name__}: {e}")


if __name__ == '__main__':
    unittest.main()

