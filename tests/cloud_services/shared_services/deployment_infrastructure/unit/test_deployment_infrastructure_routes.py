"""
Integration tests for Deployment & Infrastructure API routes.
"""


# Imports handled by conftest.py
import pytest
from fastapi.testclient import TestClient
from deployment_infrastructure.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestDeployEndpoint:
    """Test deploy endpoint."""

    def test_deploy_development_local(self, client):
        """Test deploy to development/local."""
        response = client.post(
            "/deploy/v1/deploy",
            json={
                "environment": "development",
                "target": "local"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "deployment_id" in data
        assert data["status"] in ["pending", "in_progress", "completed", "failed"]
        assert data["environment"] == "development"
        assert data["target"] == "local"

    def test_deploy_staging_cloud(self, client):
        """Test deploy to staging/cloud."""
        response = client.post(
            "/deploy/v1/deploy",
            json={
                "environment": "staging",
                "target": "cloud"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["environment"] == "staging"
        assert data["target"] == "cloud"

    def test_deploy_with_service(self, client):
        """Test deploy with specific service."""
        response = client.post(
            "/deploy/v1/deploy",
            json={
                "environment": "development",
                "target": "local",
                "service": "identity-access-management"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["environment"] == "development"

    def test_deploy_invalid_environment(self, client):
        """Test deploy with invalid environment."""
        response = client.post(
            "/deploy/v1/deploy",
            json={
                "environment": "invalid",
                "target": "local"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_deploy_invalid_target(self, client):
        """Test deploy with invalid target."""
        response = client.post(
            "/deploy/v1/deploy",
            json={
                "environment": "development",
                "target": "invalid"
            }
        )
        assert response.status_code == 422  # Validation error


class TestParityEndpoint:
    """Test parity endpoint."""

    def test_verify_parity(self, client):
        """Test verify environment parity."""
        response = client.post(
            "/deploy/v1/parity",
            json={
                "source_environment": "development",
                "target_environment": "staging"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source_environment"] == "development"
        assert data["target_environment"] == "staging"
        assert data["parity_status"] in ["match", "mismatch", "partial"]
        assert "differences" in data
        assert "checked_at" in data

    def test_verify_parity_with_resources(self, client):
        """Test verify parity with specific resources."""
        response = client.post(
            "/deploy/v1/parity",
            json={
                "source_environment": "development",
                "target_environment": "staging",
                "check_resources": ["database", "compute"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["parity_status"] in ["match", "mismatch", "partial"]


class TestStatusEndpoint:
    """Test status endpoint."""

    def test_get_status(self, client):
        """Test get infrastructure status."""
        response = client.get("/deploy/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert "environment" in data
        assert "resources" in data
        assert "status_summary" in data
        assert "checked_at" in data

    def test_get_status_with_environment(self, client):
        """Test get status with environment parameter."""
        response = client.get("/deploy/v1/status?environment=production")
        assert response.status_code == 200
        data = response.json()
        assert data["environment"] == "production"

    def test_get_status_with_resource_type(self, client):
        """Test get status with resource type parameter."""
        response = client.get("/deploy/v1/status?resource_type=database")
        assert response.status_code == 200
        data = response.json()
        assert all(r["resource_type"] == "database" for r in data["resources"])


class TestHealthEndpoint:
    """Test health endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "deployment-infrastructure"
        assert data["version"] == "1.0.0"
        assert "environment" in data
        assert "timestamp" in data
