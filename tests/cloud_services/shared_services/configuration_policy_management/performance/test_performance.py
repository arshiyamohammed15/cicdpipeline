from __future__ import annotations
"""Performance tests for Configuration & Policy Management service."""

# Imports handled by conftest.py

import time
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from configuration_policy_management.main import app


@pytest.mark.performance
class TestPolicyEvaluationPerformance:
    """Test policy evaluation performance."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_policy_evaluation_latency(self, client):
        """Test that policy evaluation meets latency requirements."""
        request = {
            "context": {},
            "principal": {"sub": "user123", "role": "admin"},
            "resource": {"id": "resource123"},
            "action": "read",
            "tenant_id": "tenant-1",
            "environment": "dev"
        }

        start_time = time.perf_counter()
        response = client.post(
            "/policy/v1/policies/test-policy/evaluate",
            json=request
        )
        latency_ms = (time.perf_counter() - start_time) * 1000

        # Should complete within reasonable time (< 50ms per PRD)
        assert latency_ms < 50
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_concurrent_policy_evaluations(self, client):
        """Test performance under concurrent policy evaluations."""
        import concurrent.futures

        def evaluate_policy(i):
            request = {
                "context": {},
                "principal": {"sub": f"user{i}", "role": "admin"},
                "resource": {"id": f"resource{i}"},
                "action": "read",
                "tenant_id": "tenant-1",
                "environment": "dev"
            }
            return client.post(
                "/policy/v1/policies/test-policy/evaluate",
                json=request
            )

        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(evaluate_policy, i) for i in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        total_time = (time.perf_counter() - start_time) * 1000

        # Should handle 20 concurrent evaluations within reasonable time (< 1s)
        assert total_time < 1000


@pytest.mark.performance
class TestConfigurationPerformance:
    """Test configuration operations performance."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_configuration_creation_latency(self, client):
        """Test that configuration creation meets latency requirements."""
        request = {
            "config_id": "perf-test-config",
            "name": "Performance Test Config",
            "config_data": {"key": "value"}
        }

        start_time = time.perf_counter()
        response = client.post(
            "/policy/v1/configurations?tenant_id=tenant-1",
            json=request
        )
        latency_ms = (time.perf_counter() - start_time) * 1000

        # Should complete within reasonable time (< 200ms)
        assert latency_ms < 200
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

