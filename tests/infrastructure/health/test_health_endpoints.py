#!/usr/bin/env python3
"""
Test Suite for Health Endpoints

Tests the updated /health and /healthz endpoints in api_service.py
"""

import sys
import pytest
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validator.integrations.api_service import app


@pytest.mark.unit
class TestHealthEndpoints(unittest.TestCase):
    """Test health endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = app.test_client()

    @pytest.mark.unit
    def test_health_endpoint(self):
        """Test /health endpoint returns comprehensive status."""
        response = self.client.get('/health')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        # Should have comprehensive health status
        self.assertIn('status', data)
        self.assertIn('checks', data)
        self.assertIn('summary', data)

        # Should have rule count from JSON files (not hardcoded)
        summary = data['summary']
        self.assertIn('total_rules', summary)
        self.assertGreater(summary['total_rules'], 0)

        # Should have integration info
        self.assertIn('integrations', data)
        self.assertIn('integration_status', data)

    @pytest.mark.unit
    def test_healthz_endpoint(self):
        """Test /healthz endpoint returns simple status."""
        response = self.client.get('/healthz')

        # Should return 200 if healthy, 503 if unhealthy
        self.assertIn(response.status_code, [200, 503])
        data = response.get_json()

        # Should have simple status
        self.assertIn('status', data)
        self.assertIn(data['status'], ['ok', 'unhealthy', 'error'])

    @pytest.mark.unit
    def test_health_endpoint_structure(self):
        """Test /health endpoint has correct structure."""
        response = self.client.get('/health')
        data = response.get_json()

        # Checks should have all required components
        checks = data['checks']
        self.assertIn('rule_count_consistency', checks)
        self.assertIn('json_files_accessible', checks)
        self.assertIn('hook_manager_functional', checks)

        # Each check should have 'healthy' field
        for check_name, check_result in checks.items():
            self.assertIn('healthy', check_result)

    @pytest.mark.unit
    def test_health_endpoint_rule_count_consistency(self):
        """Test /health endpoint verifies rule count consistency."""
        response = self.client.get('/health')
        data = response.get_json()

        rule_check = data['checks']['rule_count_consistency']

        # Should verify counts match
        self.assertIn('expected_count', rule_check)
        self.assertIn('actual_count', rule_check)

        # If healthy, counts should match
        if rule_check['healthy']:
            self.assertEqual(rule_check['expected_count'], rule_check['actual_count'])


if __name__ == '__main__':
    unittest.main()
