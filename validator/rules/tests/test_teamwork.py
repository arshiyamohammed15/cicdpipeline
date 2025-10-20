"""
Tests for Teamwork Validator

Tests teamwork and collaboration rules validation.
"""

import unittest
from validator.rules.teamwork import TeamworkValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestTeamworkValidator(unittest.TestCase):
    """Test suite for teamwork rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = TeamworkValidator()
        self.test_file_path = "test.py"
    
    def test_validate_all_runs_without_error(self):
        """Test validate_all() executes successfully."""
        content = '''
def collaborate():
    """Function with clear documentation for team."""
    pass
'''
        try:
            import ast
            tree = ast.parse(content)
            violations = self.validator.validate_all(tree, content, self.test_file_path)
            self.assertIsInstance(violations, list)
        except Exception as e:
            self.fail(f"validate_all() raised {type(e).__name__}: {e}")


if __name__ == '__main__':
    unittest.main()

