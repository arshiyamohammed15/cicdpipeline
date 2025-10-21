"""
Tests for Comments Validator

Tests documentation and comment standards validation.
"""

import unittest
from validator.rules.comments import CommentsValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestCommentsValidator(unittest.TestCase):
    """Test suite for comments rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = CommentsValidator()
        self.test_file_path = "test.py"
    
    def test_validate_runs_without_error(self):
        """Test validate() executes successfully."""
        content = '''
def documented_function():
    """This function has proper documentation."""
    # Clear comment explaining logic
    return True
'''
        try:
            violations = self.validator.validate(self.test_file_path, content)
            self.assertIsInstance(violations, list)
        except Exception as e:
            self.fail(f"validate() raised {type(e).__name__}: {e}")


if __name__ == '__main__':
    unittest.main()

