from __future__ import annotations
"""Integration tests for Signal Ingestion & Normalization API routes."""

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
# Create package structure and load modules
parent_pkg = type(sys)('signal_ingestion_normalization')
sys.modules['signal_ingestion_normalization'] = parent_pkg

# Load all required modules (similar pattern to conftest.py)
modules_to_load = [
    ("models", "models.py"),
    ("dependencies", "dependencies.py"),
    ("producer_registry", "producer_registry.py"),
    ("governance", "governance.py"),
    ("validation", "validation.py"),
    ("normalization", "normalization.py"),
    ("routing", "routing.py"),
    ("deduplication", "deduplication.py"),
    ("dlq", "dlq.py"),
    ("observability", "observability.py"),
    ("services", "services.py"),
    ("routes", "routes.py"),
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

# Import main app
if 'signal_ingestion_normalization.main' not in sys.modules:
    # Load main module
    main_path = PACKAGE_ROOT / "main.py"
    if main_path.exists():
        spec_main = importlib.util.spec_from_file_location("signal_ingestion_normalization.main", main_path)
        if spec_main is not None and spec_main.loader is not None:
            main_module = importlib.util.module_from_spec(spec_main)
            sys.modules['signal_ingestion_normalization.main'] = main_module
            spec_main.loader.exec_module(main_module)
        else:
            raise ImportError(f"Cannot load main module from {main_path}")
    else:
        raise FileNotFoundError(f"Main module not found at {main_path}")
else:
    main_module = sys.modules['signal_ingestion_normalization.main']

# Check if create_app exists, otherwise use app directly
if hasattr(main_module, 'create_app'):
    app = main_module.create_app()
elif hasattr(main_module, 'app'):
    app = main_module.app
else:
    raise AttributeError("Main module has neither 'create_app' nor 'app'")

from fastapi.testclient import TestClient

_test_client = TestClient(app)


@pytest.fixture
def test_client():
    return _test_client


@pytest.mark.integration
class TestIngestEndpoint:
    """Test /v1/signals/ingest endpoint."""

    @patch('signal_ingestion_normalization.routes.get_ingestion_service')
    def test_ingest_signals_success(self, mock_get_service, test_client):
        """Test successful signal ingestion."""
        mock_service = Mock()
        mock_result = Mock()
        mock_result.status = "accepted"
        mock_result.signal_id = "test-1"
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
                    "signal_type": "test_event",
                    "environment": "dev",
                    "occurred_at": "2025-01-01T00:00:00Z",
                    "ingested_at": "2025-01-01T00:00:01Z",
                    "schema_version": "1.0.0",
                    "payload": {"message": "test"}
                }]
            },
            headers={"Authorization": "Bearer valid_token_tenant-1"}
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    def test_ingest_signals_missing_auth(self, test_client):
        """Test signal ingestion without authorization."""
        response = test_client.post(
            "/v1/signals/ingest",
            json={"signals": []}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_ingest_signals_invalid_payload(self, test_client):
        """Test signal ingestion with invalid payload."""
        response = test_client.post(
            "/v1/signals/ingest",
            json={"invalid": "payload"},
            headers={"Authorization": "Bearer valid_token_tenant-1"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
class TestHealthEndpoint:
    """Test health and readiness endpoints."""

    def test_health_check(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_readiness_check(self, test_client):
        """Test readiness check endpoint."""
        response = test_client.get("/ready")
        assert response.status_code == status.HTTP_200_OK

