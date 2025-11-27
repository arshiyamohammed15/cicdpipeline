"""
Integration tests for Key Management Service API routes.
"""

import pytest
from fastapi.testclient import TestClient
from key_management_service.main import app


class TestKMSRoutes:
    """Test KMS API routes."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data

    def test_config_endpoint(self, client):
        """Test config endpoint."""
        response = client.get("/kms/v1/config")
        assert response.status_code == 200
        data = response.json()
        assert "key_rotation_schedule" in data
        assert "allowed_algorithms" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
