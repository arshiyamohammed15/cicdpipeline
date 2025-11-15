"""
Integration tests for Identity & Access Management API routes.
"""

import pytest
from fastapi.testclient import TestClient
from identity_access_management.main import app


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
        assert data["module_id"] == "M21"
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
