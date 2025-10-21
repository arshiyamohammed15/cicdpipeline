"""
Tests for Requirements Validator

Tests requirements and specification compliance validation.
"""

import unittest
from validator.rules.requirements import RequirementsValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestRequirementsValidator(unittest.TestCase):
    """Test suite for requirements rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = RequirementsValidator()
        self.test_file_path = "test.py"
    
    def test_validate_all_runs_without_error(self):
        """Test validate_all() executes successfully."""
        content = '''
def implement_feature():
    """Implement feature according to requirements."""
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

