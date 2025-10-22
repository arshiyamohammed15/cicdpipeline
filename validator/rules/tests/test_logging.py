"""
Tests for Logging Validator

Tests logging standards validation.
"""

import unittest
from validator.rules.logging import LoggingValidator
from validator.models import Severity
from validator.rules.tests.base_test import BaseValidatorTest


class TestLoggingValidator(unittest.TestCase):
    """Test suite for logging rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = LoggingValidator()
        self.test_file_path = "test.py"
    
    def test_validate_runs_without_error(self):
        """Test validate() executes successfully."""
        content = '''
import logging
logger = logging.getLogger(__name__)

def process():
    logger.info("Processing started")
    logger.error("Error occurred")
'''
        try:
            violations = self.validator.validate(self.test_file_path, content)
            self.assertIsInstance(violations, list)
        except Exception as e:
            self.fail(f"validate() raised {type(e).__name__}: {e}")


if __name__ == '__main__':
    unittest.main()

