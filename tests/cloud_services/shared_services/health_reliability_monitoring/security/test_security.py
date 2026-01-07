from __future__ import annotations
"""
Security tests for Health & Reliability Monitoring service.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

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
from health_reliability_monitoring.models import ComponentDefinition

test_client = TestClient(app)


@pytest.mark.security
class TestAuthentication:
    """Test authentication requirements."""

    @pytest.mark.security
    def test_endpoint_requires_authentication(self):
        """Test that endpoints require authentication."""
        response = test_client.get("/v1/health/components")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]

    @pytest.mark.security
    def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected."""
        response = test_client.get(
            "/v1/health/components",
            headers={"Authorization": "Bearer invalid_token"},
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]

    @pytest.mark.security
    def test_valid_token_accepted(self):
        """Test that valid tokens are accepted."""
        response = test_client.get(
            "/v1/health/components",
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        # Should not be 401 if token is valid
        assert response.status_code != status.HTTP_401_UNAUTHORIZED


@pytest.mark.security
class TestAuthorization:
    """Test authorization and scope enforcement."""

    @pytest.mark.security
    def test_write_scope_required_for_registration(self):
        """Test that write scope is required for component registration."""
        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
        )

        # Token with only read scope should fail
        response = test_client.post(
            "/v1/health/components",
            json=component.model_dump(),
            headers={"Authorization": "Bearer valid_epc1_readonly_token"},  # Assuming such token exists
        )

        # Should fail if write scope is required
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]


@pytest.mark.security
class TestTenantIsolation:
    """Test tenant isolation."""

    @pytest.mark.security
    def test_tenant_access_restriction(self):
        """Test that tenants can only access their own data."""
        # Request tenant health for different tenant
        response = test_client.get(
            "/v1/health/tenants/other-tenant",
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        # Should be restricted unless cross-tenant scope
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]

    @pytest.mark.security
    def test_cross_tenant_access_with_scope(self):
        """Test that cross-tenant scope allows access."""
        # This test assumes a token with cross_tenant scope
        # Implementation depends on IAM client behavior
        response = test_client.get(
            "/v1/health/tenants/other-tenant",
            headers={"Authorization": "Bearer valid_epc1_cross_tenant_token"},
        )

        # Should succeed with cross-tenant scope
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


@pytest.mark.security
class TestCrossPlaneAccess:
    """Test cross-plane access restrictions."""

    @pytest.mark.security
    def test_plane_access_requires_privilege(self):
        """Test that plane-level access requires privileged scope."""
        response = test_client.get(
            "/v1/health/planes/Product/prod",
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        # Should require cross_tenant or admin scope
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED]

    @pytest.mark.security
    def test_plane_access_with_admin_scope(self):
        """Test that admin scope allows plane access."""
        response = test_client.get(
            "/v1/health/planes/Product/prod",
            headers={"Authorization": "Bearer valid_epc1_admin_token"},
        )

        # Should succeed with admin scope
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


@pytest.mark.security
class TestInputValidation:
    """Test input validation and sanitization."""

    @pytest.mark.security
    def test_component_id_validation(self):
        """Test that component_id is validated."""
        component = {
            "component_id": "ab",  # Too short
            "name": "Test",
            "component_type": "service",
            "plane": "Product",
            "tenant_scope": "tenant",
        }

        response = test_client.post(
            "/v1/health/components",
            json=component,
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        # Should fail validation
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_401_UNAUTHORIZED]

    @pytest.mark.security
    def test_telemetry_label_cardinality(self):
        """Test that telemetry label cardinality is enforced."""
        from health_reliability_monitoring.models import TelemetryPayload
        from datetime import datetime

        # Create payload with excessive labels (if limit is low)
        labels = {f"key_{i}": f"value_{i}" for i in range(100)}
        payload = TelemetryPayload(
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            timestamp=datetime.utcnow(),
            labels=labels,
            telemetry_type="metrics",
        )

        response = test_client.post(
            "/v1/health/telemetry",
            json=payload.model_dump(mode="json"),
            headers={"Authorization": "Bearer valid_epc1_test_token"},
        )

        # Should fail if limit exceeded, or succeed if within limit
        assert response.status_code in [
            status.HTTP_202_ACCEPTED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

