"""
Integration tests for Contracts & Schema Registry API routes.
"""


# Imports handled by conftest.py
import pytest
import httpx
from httpx import ASGITransport
from contracts_schema_registry.main import app


@pytest.mark.integration
class TestContractsSchemaRegistryRoutes:
    """Test Contracts & Schema Registry API routes."""

    @pytest.fixture
    async def client(self):
        """Create async test client."""
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data

    @pytest.mark.asyncio
    async def test_config_endpoint(self, client):
        """Test config endpoint."""
        response = await client.get("/registry/v1/config")
        assert response.status_code == 200
        data = response.json()
        assert "module_id" in data
        assert "version" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
