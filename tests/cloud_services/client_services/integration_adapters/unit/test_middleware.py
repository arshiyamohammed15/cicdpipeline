"""
Unit tests for middleware.

What: Test IAM authentication middleware, error handling
Why: Ensure middleware works correctly
Coverage Target: 100%
"""
from __future__ import annotations

import os
import sys
import types
import importlib.util
from pathlib import Path

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import Request
from fastapi.testclient import TestClient

# Module setup handled by root conftest.py

# Create package structure for relative imports
package_path = str(Path(__file__).resolve().parents[4] / "src" / "cloud_services" / "client-services" / "integration-adapters")
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

@pytest.mark.unit
class TestIAMAuthMiddleware:
    """Test IAM authentication middleware."""

    @pytest.mark.unit
    def test_health_endpoint_no_auth_required(self):
        """Test health endpoint doesn't require auth."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.unit
    def test_webhook_endpoint_no_auth_required(self):
        """Test webhook endpoint doesn't require auth."""
        client = TestClient(app)
        response = client.post(
            "/v1/integrations/webhooks/github/test-token",
            json={"test": "data"}
        )
        # Should not return 401 (auth not required for webhooks)
        assert response.status_code != 401

    @pytest.mark.unit
    def test_management_endpoints_require_auth(self):
        """Test management endpoints require authentication."""
        client = TestClient(app)

        # Create connection endpoint
        response = client.post(
            "/v1/integrations/connections",
            json={"provider_id": "github", "display_name": "Test", "auth_ref": "secret"}
        )
        assert response.status_code == 401

        # List connections endpoint
        response = client.get("/v1/integrations/connections")
        assert response.status_code == 401

