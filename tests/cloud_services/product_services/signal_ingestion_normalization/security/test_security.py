from __future__ import annotations
"""Security tests for Signal Ingestion & Normalization module."""

# Imports handled by conftest.py

import sys
import importlib.util
from pathlib import Path
from unittest.mock import patch, Mock

import pytest
from fastapi import status

# Add parent directories to path
PACKAGE_ROOT = Path(__file__).resolve().parents[4] / "src" / "cloud_services" / "product-services" / "signal-ingestion-normalization"
# Path setup handled by conftest.py
# Create package structure and load modules (same as integration tests)
parent_pkg = type(sys)('signal_ingestion_normalization')
sys.modules['signal_ingestion_normalization'] = parent_pkg

modules_to_load = [
    ("models", "models.py"),
    ("dependencies", "dependencies.py"),
    ("main", "main.py"),
]

for module_name, filename in modules_to_load:
    module_path = PACKAGE_ROOT / filename
    if module_path.exists():
        spec = importlib.util.spec_from_file_location(
            f"signal_ingestion_normalization.{module_name}",
            module_path
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"signal_ingestion_normalization.{module_name}"] = module
        spec.loader.exec_module(module)

main_module = sys.modules['signal_ingestion_normalization.main']
app = main_module.create_app()

from fastapi.testclient import TestClient

test_client = TestClient(app)


@pytest.mark.security
class TestTenantIsolation:
    """Test tenant isolation security."""

    def test_cross_tenant_signal_rejection(self, test_client):
        """Test that signals from different tenants are rejected."""
        response = test_client.post(
            "/v1/signals/ingest",
            json={
                "signals": [{
                    "signal_id": "test-1",
                    "tenant_id": "tenant-2",  # Different from token tenant
                    "producer_id": "producer-1",
                    "signal_kind": "event",
                    "plane": "tenant_cloud",
                    "environment": "dev",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "payload": {}
                }]
            },
            headers={"Authorization": "Bearer valid_token_tenant-1"}
        )

        # Should reject due to tenant mismatch
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_unauthorized_access(self, test_client):
        """Test that requests without authorization are rejected."""
        response = test_client.post(
            "/v1/signals/ingest",
            json={"signals": []}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token(self, test_client):
        """Test that invalid tokens are rejected."""
        response = test_client.post(
            "/v1/signals/ingest",
            json={"signals": []},
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.security
class TestInputValidation:
    """Test input validation security."""

    def test_oversized_payload(self, test_client):
        """Test handling of oversized payloads."""
        large_payload = {"data": "x" * 1000000}  # 1MB payload

        response = test_client.post(
            "/v1/signals/ingest",
            json={
                "signals": [{
                    "signal_id": "test-1",
                    "tenant_id": "tenant-1",
                    "producer_id": "producer-1",
                    "signal_kind": "event",
                    "plane": "tenant_cloud",
                    "environment": "dev",
                    "timestamp": "2025-01-01T00:00:00Z",
                    "payload": large_payload
                }]
            },
            headers={"Authorization": "Bearer valid_token_tenant-1"}
        )

        # Should either accept or reject with appropriate error
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_malformed_json(self, test_client):
        """Test handling of malformed JSON."""
        response = test_client.post(
            "/v1/signals/ingest",
            data="not json",
            headers={"Content-Type": "application/json", "Authorization": "Bearer valid_token_tenant-1"}
        )

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_sql_injection_attempt(self, test_client):
        """Test handling of SQL injection attempts in payload."""
        malicious_payload = {"query": "'; DROP TABLE signals; --"}

        with patch('signal_ingestion_normalization.routes.get_ingestion_service') as mock_get_service:
            mock_service = Mock()
            mock_result = Mock()
            mock_result.status = "accepted"
            mock_service.ingest_signal.return_value = mock_result
            mock_get_service.return_value = mock_service

            response = test_client.post(
                "/v1/signals/ingest",
                json={
                    "signals": [{
                        "signal_id": "test-1",
                        "tenant_id": "tenant-1",
                        "producer_id": "producer-1",
                        "signal_kind": "event",
                        "plane": "tenant_cloud",
                        "environment": "dev",
                        "timestamp": "2025-01-01T00:00:00Z",
                        "payload": malicious_payload
                    }]
                },
                headers={"Authorization": "Bearer valid_token_tenant-1"}
            )

            # Service should handle the request (sanitization happens at service layer)
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

