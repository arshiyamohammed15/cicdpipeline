"""
Tests for Quality Validator

Tests code quality metrics validation.
"""

import unittest
from validator.rules.quality import QualityValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestQualityValidator(unittest.TestCase):
    """Test suite for quality rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = QualityValidator()
        self.test_file_path = "test.py"
    
    def test_validate_all_runs_without_error(self):
        """Test validate_all() executes successfully."""
        content = '''
def high_quality_function(param: str) -> str:
    """High quality function with proper typing."""
    return param.strip()
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

