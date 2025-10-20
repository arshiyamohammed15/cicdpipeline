"""
Tests for System Design Validator

Tests system design patterns validation.
"""

import unittest
from validator.rules.system_design import SystemDesignValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestSystemDesignValidator(unittest.TestCase):
    """Test suite for system design rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = SystemDesignValidator()
        self.test_file_path = "test.py"
    
    def test_validate_all_runs_without_error(self):
        """Test validate_all() executes successfully."""
        content = '''
class SystemComponent:
    """System component with proper design."""
    def process(self):
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

