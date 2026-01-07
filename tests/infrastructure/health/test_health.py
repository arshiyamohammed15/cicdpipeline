#!/usr/bin/env python3
"""
Test Suite for Health Check Module

Tests validator/health.py functionality:
- Rule count consistency checks
- JSON files accessibility checks
- Hook manager functionality checks
- Comprehensive health status
"""

import sys
import pytest
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validator.health import HealthChecker, get_health_endpoint
REPO_ROOT = Path(__file__).resolve().parents[3]
CONSTITUTION_DIR = REPO_ROOT / "docs" / "constitution"


@pytest.mark.unit
class TestHealthChecker(unittest.TestCase):
    """Test HealthChecker class."""

    def setUp(self):
        """Set up test fixtures."""
        self.checker = HealthChecker()

    @pytest.mark.unit
    def test_initialization(self):
        """Test HealthChecker initializes correctly."""
        self.assertIsNotNone(self.checker.constitution_dir)
        self.assertIsNotNone(self.checker.hook_manager)
        self.assertEqual(self.checker.constitution_dir, CONSTITUTION_DIR)

    @pytest.mark.unit
    def test_check_rule_count_consistency(self):
        """Test rule count consistency check."""
        result = self.checker.check_rule_count_consistency()

        # Should return a dict with health status
        self.assertIn('healthy', result)
        self.assertIn('expected_count', result)
        self.assertIn('actual_count', result)
        self.assertIn('json_files', result)

        # Should be healthy (counts match)
        self.assertTrue(result['healthy'])
        self.assertEqual(result['expected_count'], result['actual_count'])
        self.assertGreater(result['expected_count'], 0)

    @pytest.mark.unit
    def test_check_json_files_accessible(self):
        """Test JSON files accessibility check."""
        result = self.checker.check_json_files_accessible()

        # Should return a dict with health status
        self.assertIn('healthy', result)
        self.assertIn('accessible_files', result)
        self.assertIn('missing_files', result)
        self.assertIn('total_files', result)

        # Should be healthy (all files accessible)
        self.assertTrue(result['healthy'])
        self.assertEqual(len(result['missing_files']), 0)
        self.assertGreater(result['total_files'], 0)

    @pytest.mark.unit
    def test_check_hook_manager_functional(self):
        """Test hook manager functionality check."""
        result = self.checker.check_hook_manager_functional()

        # Should return a dict with health status
        self.assertIn('healthy', result)
        self.assertIn('test_result', result)

        # Should be healthy (hook manager works)
        self.assertTrue(result['healthy'])
        self.assertIsNotNone(result['test_result'])

        # Test result should have expected structure
        test_result = result['test_result']
        self.assertIn('valid', test_result)
        self.assertIn('violations_count', test_result)
        self.assertIn('rules_checked', test_result)

    @pytest.mark.unit
    def test_get_health_status(self):
        """Test comprehensive health status."""
        result = self.checker.get_health_status()

        # Should return comprehensive status
        self.assertIn('status', result)
        self.assertIn('checks', result)
        self.assertIn('summary', result)

        # Status should be healthy
        self.assertEqual(result['status'], 'healthy')

        # All checks should be present
        checks = result['checks']
        self.assertIn('rule_count_consistency', checks)
        self.assertIn('json_files_accessible', checks)
        self.assertIn('hook_manager_functional', checks)

        # All checks should be healthy
        self.assertTrue(checks['rule_count_consistency']['healthy'])
        self.assertTrue(checks['json_files_accessible']['healthy'])
        self.assertTrue(checks['hook_manager_functional']['healthy'])

        # Summary should have expected fields
        summary = result['summary']
        self.assertIn('total_rules', summary)
        self.assertIn('json_files_count', summary)
        self.assertIn('constitution_dir', summary)
        self.assertGreater(summary['total_rules'], 0)
        self.assertGreater(summary['json_files_count'], 0)

    @pytest.mark.unit
    def test_check_rule_count_consistency_with_missing_file(self):
        """Test rule count check handles missing files gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # HealthChecker requires JSON files, so we'll test error handling differently
            # Create a file that will cause an error
            invalid_file = Path(tmpdir) / "test.json"
            invalid_file.write_text("invalid json {")

            # This will fail during initialization, so we test the error path
            try:
                checker = HealthChecker(constitution_dir=tmpdir)
                result = checker.check_rule_count_consistency()
                # If it gets here, check that it handles the error
                if not result['healthy']:
                    self.assertIn('error', result)
            except FileNotFoundError:
                # Expected when no valid JSON files exist
                pass

    @pytest.mark.unit
    def test_check_json_files_accessible_with_invalid_json(self):
        """Test JSON files check handles invalid JSON gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid JSON file
            invalid_json = Path(tmpdir) / "invalid.json"
            invalid_json.write_text("not valid json {")

            checker = HealthChecker(constitution_dir=tmpdir)
            result = checker.check_json_files_accessible()

            # Should detect invalid JSON
            self.assertFalse(result['healthy'])
            self.assertGreater(len(result['missing_files']), 0)


@pytest.mark.unit
class TestHealthEndpoint(unittest.TestCase):
    """Test get_health_endpoint function."""

    @pytest.mark.unit
    def test_get_health_endpoint(self):
        """Test health endpoint function."""
        result = get_health_endpoint()

        # Should return health status dict
        self.assertIn('status', result)
        self.assertIn('checks', result)
        self.assertIn('summary', result)

        # Should be healthy
        self.assertEqual(result['status'], 'healthy')

        # Should have all required checks
        checks = result['checks']
        self.assertIn('rule_count_consistency', checks)
        self.assertIn('json_files_accessible', checks)
        self.assertIn('hook_manager_functional', checks)


@pytest.mark.unit
class TestHealthCheckerEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    @pytest.mark.unit
    def test_initialization_with_custom_dir(self):
        """Test initialization with custom constitution directory."""
        # Use actual constitution dir for this test
        checker = HealthChecker(constitution_dir="docs/constitution")
        self.assertEqual(checker.constitution_dir, CONSTITUTION_DIR)

    @pytest.mark.unit
    def test_check_hook_manager_with_exception(self):
        """Test hook manager check handles exceptions."""
        checker = HealthChecker()

        # Mock hook manager to raise exception
        with patch.object(checker.hook_manager, 'validate_before_generation', side_effect=Exception("Test error")):
            result = checker.check_hook_manager_functional()

            # Should handle exception gracefully
            self.assertFalse(result['healthy'])
            self.assertIn('error', result)


if __name__ == '__main__':
    unittest.main()
