"""
Tests for Problem Solving Validator

Tests problem-solving approaches validation.
"""

import unittest
from validator.rules.problem_solving import ProblemSolvingValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestProblemSolvingValidator(unittest.TestCase):
    """Test suite for problem-solving rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ProblemSolvingValidator()
        self.test_file_path = "test.py"
    
    def test_validate_all_runs_without_error(self):
        """Test validate_all() executes successfully."""
        content = '''
def solve_problem(input_data):
    """Solve problem efficiently."""
    return process(input_data)
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

