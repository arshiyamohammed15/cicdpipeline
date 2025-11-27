"""Performance tests for Contracts & Schema Registry service."""
from __future__ import annotations

import time
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from contracts_schema_registry.main import app


@pytest.mark.performance
class TestSchemaValidationPerformance:
    """Test schema validation performance."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_schema_validation_latency(self, client):
        """Test that schema validation meets latency requirements."""
        request = {
            "schema_id": "test-schema",
            "data": {"name": "test"}
        }
        
        start_time = time.perf_counter()
        response = client.post("/registry/v1/validate", json=request)
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Should complete within reasonable time (< 100ms per PRD)
        assert latency_ms < 100
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_concurrent_validations(self, client):
        """Test performance under concurrent validations."""
        import concurrent.futures
        
        def validate_data(i):
            request = {
                "schema_id": "test-schema",
                "data": {"name": f"test{i}"}
            }
            return client.post("/registry/v1/validate", json=request)
        
        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(validate_data, i) for i in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        total_time = (time.perf_counter() - start_time) * 1000
        
        # Should handle 20 concurrent validations within reasonable time (< 1s)
        assert total_time < 1000


@pytest.mark.performance
class TestSchemaRegistrationPerformance:
    """Test schema registration performance."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_schema_registration_latency(self, client):
        """Test that schema registration meets latency requirements."""
        request = {
            "name": "perf-test-schema",
            "schema_type": "json",
            "definition": {"type": "object", "properties": {"name": {"type": "string"}}},
            "namespace": "test"
        }
        
        start_time = time.perf_counter()
        response = client.post("/registry/v1/schemas", json=request)
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Should complete within reasonable time (< 200ms per PRD)
        assert latency_ms < 200
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_compatibility_check_latency(self, client):
        """Test that compatibility checks meet latency requirements."""
        request = {
            "source_schema": {"type": "object"},
            "target_schema": {"type": "object", "properties": {"id": {"type": "string"}}},
            "compatibility_mode": "backward"
        }
        
        start_time = time.perf_counter()
        response = client.post("/registry/v1/compatibility", json=request)
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Should complete within reasonable time (< 150ms per PRD)
        assert latency_ms < 150
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

