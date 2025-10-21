"""
Tests for Folder Standards Validator

Tests directory structure and organization validation.
"""

import unittest
from validator.rules.folder_standards import FolderStandardsValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestFolderStandardsValidator(unittest.TestCase):
    """Test suite for folder standards rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = FolderStandardsValidator()
        self.test_file_path = "src/module/file.py"
    
    def test_validate_runs_without_error(self):
        """Test validate() executes successfully."""
        content = '''
# File in proper directory structure
def module_function():
    pass
'''
        try:
            violations = self.validator.validate(self.test_file_path, content)
            self.assertIsInstance(violations, list)
        except Exception as e:
            self.fail(f"validate() raised {type(e).__name__}: {e}")


if __name__ == '__main__':
    unittest.main()

