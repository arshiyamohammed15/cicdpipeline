"""
Unit tests for FastAPI main app.

What: Test app initialization, middleware, router inclusion
Why: Ensure FastAPI app is configured correctly
Coverage Target: 100%
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

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


class TestMainApp:
    """Test FastAPI main app."""

    def test_app_initialization(self):
        """Test app initialization."""
        assert app is not None
        assert app.title == "ZeroUI Integration Adapters Service"
        assert app.version == "2.0.0"

    def test_health_endpoint(self):
        """Test health check endpoint."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_docs_endpoint(self):
        """Test OpenAPI docs endpoint."""
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint(self):
        """Test ReDoc endpoint."""
        client = TestClient(app)
        response = client.get("/redoc")
        assert response.status_code == 200

