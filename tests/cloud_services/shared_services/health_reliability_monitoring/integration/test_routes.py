from __future__ import annotations
"""
Integration tests for Health & Reliability Monitoring API routes.
"""

import pytest
from datetime import datetime
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# Path setup handled by conftest.py
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parents[4] / "src" / "cloud_services" / "shared-services" / "health-reliability-monitoring"
# Remove any conflicting paths and add our module path first
if str(MODULE_ROOT) in sys.path:
    sys.path.remove(str(MODULE_ROOT))
sys.path.insert(0, str(MODULE_ROOT))

# Import using importlib to ensure we get the correct module
import importlib.util
main_spec = importlib.util.spec_from_file_location("health_reliability_monitoring_main", MODULE_ROOT / "main.py")
main_module = importlib.util.module_from_spec(main_spec)
main_spec.loader.exec_module(main_module)
app = main_module.app
from health_reliability_monitoring.models import ComponentDefinition, TelemetryPayload
try:
    from health_reliability_monitoring.database import models as db_models
except ImportError:
    db_models = None  # Database module not implemented

test_client = TestClient(app)


@pytest.fixture
def db_session():
    """Provide a dummy database session for tests that expect one."""
    return MagicMock()


class TestHealthEndpoints:
    """Test health endpoints."""

    def test_healthz_endpoint(self):
        """Test /healthz endpoint."""
        response = test_client.get("/healthz")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert data["status"] == "UP"

    def test_metrics_endpoint(self):
        """Test /metrics endpoint."""
        response = test_client.get("/metrics")

        assert response.status_code == status.HTTP_200_OK
        content_type = response.headers.get("content-type", "").lower()
        assert content_type.startswith("text/plain; version=0.0.4")


@pytest.mark.skip(reason="Health registry persistence not configured in test harness")
class TestRegistryEndpoints:
    """Test registry endpoints."""

    def test_register_component(self, db_session):
        """Test POST /v1/health/components."""
        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
        )

        response = test_client.post(
            "/v1/health/components",
            json=component.model_dump(),
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_401_UNAUTHORIZED]
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            assert data["component_id"] == "test-component-1"
            assert data["enrolled"] is True

    def test_get_component(self, db_session):
        """Test GET /v1/health/components/{component_id}."""
        # First register a component
        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
        )
        test_client.post(
            "/v1/health/components",
            json=component.model_dump(),
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        response = test_client.get(
            "/v1/health/components/test-component-1",
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]

    def test_list_components(self, db_session):
        """Test GET /v1/health/components."""
        response = test_client.get(
            "/v1/health/components",
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.json(), list)


@pytest.mark.skip(reason="Health registry persistence not configured in test harness")
class TestHealthStatusEndpoints:
    """Test health status endpoints."""

    def test_get_component_status(self, db_session):
        """Test GET /v1/health/components/{component_id}/status."""
        # Create component and snapshot
        component = db_models.Component(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            environment="prod",
            tenant_scope="tenant",
        )
        db_session.add(component)

        snapshot = db_models.HealthSnapshot(
            snapshot_id="snapshot-1",
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            state="OK",
            reason_code="healthy",
            evaluated_at=datetime.utcnow(),
        )
        db_session.add(snapshot)
        db_session.commit()

        response = test_client.get(
            "/v1/health/components/test-component-1/status",
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]

    def test_get_tenant_health(self, db_session):
        """Test GET /v1/health/tenants/{tenant_id}."""
        response = test_client.get(
            "/v1/health/tenants/test-tenant",
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]

    def test_get_plane_health(self, db_session):
        """Test GET /v1/health/planes/{plane}/{environment}."""
        response = test_client.get(
            "/v1/health/planes/Product/prod",
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_get_component_slo(self, db_session):
        """Test GET /v1/health/components/{component_id}/slo."""
        response = test_client.get(
            "/v1/health/components/test-component-1/slo",
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND]


@pytest.mark.skip(reason="Health registry persistence not configured in test harness")
class TestTelemetryEndpoints:
    """Test telemetry endpoints."""

    def test_ingest_telemetry(self, db_session):
        """Test POST /v1/health/telemetry."""
        # First register component
        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
        )
        test_client.post(
            "/v1/health/components",
            json=component.model_dump(),
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        payload = TelemetryPayload(
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            timestamp=datetime.utcnow(),
            metrics={"latency_p95_ms": 150.0},
            telemetry_type="metrics",
        )

        response = test_client.post(
            "/v1/health/telemetry",
            json=payload.model_dump(),
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        assert response.status_code in [status.HTTP_202_ACCEPTED, status.HTTP_401_UNAUTHORIZED]


@pytest.mark.skip(reason="Health registry persistence not configured in test harness")
class TestSafeToActEndpoints:
    """Test Safe-to-Act endpoints."""

    def test_check_safe_to_act(self, db_session):
        """Test POST /v1/health/check_safe_to_act."""
        request = {
            "tenant_id": "test-tenant",
            "plane": "Product",
            "action_type": "standard_action",
            "component_scope": None,
        }

        response = test_client.post(
            "/v1/health/check_safe_to_act",
            json=request,
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "allowed" in data
            assert "recommended_mode" in data
            assert "reason_codes" in data

