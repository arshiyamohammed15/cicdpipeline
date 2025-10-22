"""
Tests for Platform Validator

Tests platform-specific rules validation.
"""

import unittest
from validator.rules.platform import PlatformValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestPlatformValidator(unittest.TestCase):
    """Test suite for platform rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = PlatformValidator()
        self.test_file_path = "test.py"
    
    def test_validate_all_runs_without_error(self):
        """Test validate_all() executes successfully."""
        content = '''
import os
path = os.path.join("dir", "file.txt")  # Cross-platform
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

