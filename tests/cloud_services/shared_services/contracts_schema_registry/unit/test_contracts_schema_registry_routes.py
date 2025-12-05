"""
Integration tests for Contracts & Schema Registry API routes.
"""


# Imports handled by conftest.py
import pytest
from fastapi.testclient import TestClient
from contracts_schema_registry.main import app


@pytest.mark.integration
class TestContractsSchemaRegistryRoutes:
    """Test Contracts & Schema Registry API routes."""

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
        response = client.get("/registry/v1/config")
        assert response.status_code == 200
        data = response.json()
        assert "module_id" in data
        assert "version" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
