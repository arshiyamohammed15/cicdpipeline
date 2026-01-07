"""
Integration tests for Configuration & Policy Management API routes.
"""


# Imports handled by conftest.py
import pytest
from fastapi.testclient import TestClient
from configuration_policy_management.main import app


@pytest.mark.integration
class TestConfigurationPolicyManagementRoutes:
    """Test Configuration & Policy Management API routes."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.mark.unit
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.unit
    def test_config_endpoint(self, client):
        """Test config endpoint."""
        response = client.get("/policy/v1/config")
        assert response.status_code == 200
        data = response.json()
        assert "module_id" in data
        assert "version" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
