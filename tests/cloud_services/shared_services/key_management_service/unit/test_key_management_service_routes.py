"""
Integration tests for Key Management Service API routes.
"""


# Imports handled by conftest.py
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Ensure module path is set up
MODULE_ROOT = Path(__file__).resolve().parents[4] / "src" / "cloud_services" / "shared-services" / "key-management-service"
# Remove any conflicting paths and add our module path first
if str(MODULE_ROOT) in sys.path:
    sys.path.remove(str(MODULE_ROOT))
sys.path.insert(0, str(MODULE_ROOT))

# Import using importlib to ensure we get the correct module
import importlib.util
main_spec = importlib.util.spec_from_file_location("key_management_service_main", MODULE_ROOT / "main.py")
main_module = importlib.util.module_from_spec(main_spec)
main_spec.loader.exec_module(main_module)
app = main_module.app


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
