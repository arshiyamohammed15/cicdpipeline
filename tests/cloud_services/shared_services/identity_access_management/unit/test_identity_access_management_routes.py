"""
Integration tests for Identity & Access Management API routes.
"""


# Imports handled by conftest.py
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Ensure module path is set up
MODULE_ROOT = Path(__file__).resolve().parents[4] / "src" / "cloud_services" / "shared-services" / "identity-access-management"
# Remove any conflicting paths and add our module path first
if str(MODULE_ROOT) in sys.path:
    sys.path.remove(str(MODULE_ROOT))
sys.path.insert(0, str(MODULE_ROOT))

# Import using importlib to ensure we get the correct module
import importlib.util
main_spec = importlib.util.spec_from_file_location("identity_access_management_main", MODULE_ROOT / "main.py")
main_module = importlib.util.module_from_spec(main_spec)
main_spec.loader.exec_module(main_module)
app = main_module.app


class TestIAMRoutes:
    """Test IAM API routes."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_config_endpoint(self, client):
        """Test config endpoint."""
        response = client.get("/iam/v1/config")
        assert response.status_code == 200
        data = response.json()
        assert data["module_id"] == "EPC-1"
        assert data["version"] == "1.1.0"

    def test_verify_endpoint_invalid_token(self, client):
        """Test verify endpoint with invalid token."""
        response = client.post(
            "/iam/v1/verify",
            json={"token": "invalid_token"}
        )
        assert response.status_code == 401

    def test_decision_endpoint_missing_fields(self, client):
        """Test decision endpoint with missing fields."""
        response = client.post(
            "/iam/v1/decision",
            json={}
        )
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
