"""
Unit tests for API routes.

What: Test all API endpoints, request validation, error handling
Why: Ensure API layer works correctly
Coverage Target: 100%
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

import sys
import os
import importlib.util
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
package_path = os.path.join(os.path.dirname(__file__), "../..")

# Create package structure for relative imports
if "integration_adapters" not in sys.modules:
    sys.modules["integration_adapters"] = types.ModuleType("integration_adapters")
    sys.modules["integration_adapters"].__path__ = [package_path]

# Load modules in dependency order
modules_to_load = [
    ("integration_adapters.config", "config.py"),
    ("integration_adapters.database.connection", "database/connection.py"),
    ("integration_adapters.dependencies", "dependencies.py"),
    ("integration_adapters.middleware", "middleware.py"),
    ("integration_adapters.routes", "routes.py"),
    ("integration_adapters.main", "main.py"),
]

for module_name, file_path in modules_to_load:
    if module_name not in sys.modules:
        full_path = os.path.join(package_path, file_path)
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

from integration_adapters.main import app
from database.models import IntegrationConnection
from models import IntegrationConnectionCreate


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestConnectionEndpoints:
    """Test connection management endpoints."""

    def test_create_connection_requires_auth(self, client):
        """Test creating connection requires authentication."""
        connection_data = {
            "provider_id": "github",
            "display_name": "Test",
            "auth_ref": "secret",
        }
        
        response = client.post("/v1/integrations/connections", json=connection_data)
        assert response.status_code == 401

    def test_list_connections_requires_auth(self, client):
        """Test listing connections requires authentication."""
        response = client.get("/v1/integrations/connections")
        assert response.status_code == 401

    def test_verify_connection_requires_auth(self, client):
        """Test verifying connection requires authentication."""
        connection_id = uuid4()
        response = client.post(f"/v1/integrations/connections/{connection_id}/verify")
        assert response.status_code == 401

    def test_update_connection_requires_auth(self, client):
        """Test updating connection requires authentication."""
        connection_id = uuid4()
        update_data = {"display_name": "Updated"}
        
        response = client.patch(
            f"/v1/integrations/connections/{connection_id}",
            json=update_data
        )
        assert response.status_code == 401


class TestWebhookEndpoint:
    """Test webhook endpoint."""

    def test_receive_webhook(self, client):
        """Test receiving webhook (no auth required)."""
        payload = {"action": "opened", "pull_request": {"number": 123}}
        
        response = client.post(
            "/v1/integrations/webhooks/github/test-token",
            json=payload
        )
        # Should process or return error, but not 401
        assert response.status_code != 401

