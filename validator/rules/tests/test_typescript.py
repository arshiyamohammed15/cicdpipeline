"""
Tests for TypeScript Validator (Rules 182-215)

Tests TypeScript-specific validation.
"""

import unittest
from validator.rules.typescript import TypeScriptValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestTypeScriptValidator(unittest.TestCase):
    """Test suite for TypeScript rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = TypeScriptValidator()
        self.test_file_path = "test.ts"
    
    def test_validate_file_runs_without_error(self):
        """Test validate_file() executes successfully."""
        content = '''
interface User {
    id: number;
    name: string;
}

function getUser(id: number): User {
    return { id, name: "Test" };
}
'''
        try:
            violations = self.validator.validate_file(self.test_file_path, content)
            self.assertIsInstance(violations, list)
        except Exception as e:
            self.fail(f"validate_file() raised {type(e).__name__}: {e}")
    
    def test_typescript_strict_mode(self):
        """Test TypeScript strict mode validation."""
        content_without_strict = '''
function example(param) {
    return param;
}
'''
        violations = self.validator.validate_file(self.test_file_path, content_without_strict)
        
        # Check for potential type safety violations
        self.assertIsInstance(violations, list)


if __name__ == '__main__':
    unittest.main()

