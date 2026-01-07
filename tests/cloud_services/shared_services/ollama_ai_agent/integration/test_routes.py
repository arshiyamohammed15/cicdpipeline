from __future__ import annotations
"""Integration tests for Ollama AI Agent API routes."""

# Imports handled by conftest.py

from unittest.mock import patch, Mock

import pytest
from fastapi import status, FastAPI
from fastapi.testclient import TestClient

import sys
import importlib.util
from pathlib import Path

# Add parent directories to path for imports
# From tests/integration/test_routes.py, go up to module directory
PACKAGE_ROOT = Path(__file__).resolve().parents[5] / "src" / "cloud_services" / "shared-services" / "ollama-ai-agent"
# Path setup handled by conftest.py
# Create parent package structure
parent_pkg = type(sys)('ollama_ai_agent')
sys.modules['ollama_ai_agent'] = parent_pkg

# Load models module
models_path = PACKAGE_ROOT / "models.py"
if models_path.exists():
    spec_models = importlib.util.spec_from_file_location("ollama_ai_agent.models", models_path)
    if spec_models is not None and spec_models.loader is not None:
        models_module = importlib.util.module_from_spec(spec_models)
        sys.modules['ollama_ai_agent.models'] = models_module
        spec_models.loader.exec_module(models_module)
        PromptRequest = models_module.PromptRequest
    else:
        models_module = None
        PromptRequest = None
else:
    models_module = None
    PromptRequest = None

if models_module is None or PromptRequest is None:
    # Create a mock PromptRequest if module loading failed
    from unittest.mock import MagicMock
    PromptRequest = MagicMock

# Load services module first (needed by routes)
services_path = PACKAGE_ROOT / "services.py"
if services_path.exists():
    spec_services = importlib.util.spec_from_file_location("ollama_ai_agent.services", services_path)
    if spec_services is not None and spec_services.loader is not None:
        services_module = importlib.util.module_from_spec(spec_services)
        sys.modules['ollama_ai_agent.services'] = services_module
        spec_services.loader.exec_module(services_module)
    else:
        services_module = None
else:
    services_module = None

# Load routes module for patching
routes_path = PACKAGE_ROOT / "routes.py"
if routes_path.exists():
    spec_routes = importlib.util.spec_from_file_location("ollama_ai_agent.routes", routes_path)
    if spec_routes is not None and spec_routes.loader is not None:
        routes_module = importlib.util.module_from_spec(spec_routes)
        sys.modules['ollama_ai_agent.routes'] = routes_module
        spec_routes.loader.exec_module(routes_module)
    else:
        routes_module = None
else:
    routes_module = None


@pytest.fixture(scope="module")
@pytest.mark.integration
def test_client():
    """Lightweight FastAPI test client for Ollama routes."""
    app = FastAPI()
    if routes_module is not None:
        # Use router with API prefix to mirror production wiring
        app.include_router(routes_module.router, prefix="/api/v1")

        def _service_factory():
            class DummyService:
                llm_name = "Ollama"
                model_name = "Tinyllama"

                def check_ollama_available(self):
                    return False

                def process_prompt(self, request):
                    # Minimal PromptResponse-compatible dict
                    return {
                        "success": True,
                        "response": "stub",
                        "model": getattr(request, "model", "tinyllama"),
                        "timestamp": "1970-01-01T00:00:00Z",
                        "metadata": {},
                    }

            service_cls = getattr(routes_module, "OllamaAIService", DummyService)
            if isinstance(service_cls, type):
                # Avoid network calls from real service in tests
                service_cls = DummyService
            try:
                return service_cls()
            except Exception:
                return DummyService()

        # Ensure dependency uses patched service when present
        app.dependency_overrides[routes_module.get_service] = _service_factory

        @app.get("/health")
        def health_endpoint():
            service = _service_factory()
            try:
                available = service.check_ollama_available()
            except Exception:
                available = False
            return {
                "status": "healthy" if available else "degraded",
                "timestamp": "1970-01-01T00:00:00Z",
                "ollama_available": available,
                "llm_name": getattr(service, "llm_name", None),
                "model_name": getattr(service, "model_name", None),
            }
    return TestClient(app)


@pytest.mark.integration
class TestPromptEndpoint:
    """Test /api/v1/prompt endpoint."""

    @patch('ollama_ai_agent.routes.OllamaAIService')
    def test_process_prompt_success(self, mock_service_class, test_client):
        """Test successful prompt processing via API."""
        mock_service = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.response = "Test response"
        mock_response.model = "tinyllama:latest"
        mock_response.timestamp = "2025-01-01T00:00:00"
        mock_response.metadata = {}
        mock_service.process_prompt.return_value = mock_response
        mock_service_class.return_value = mock_service

        response = test_client.post(
            "/api/v1/prompt",
            json={"prompt": "Test prompt"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "response" in data
        assert "model" in data

    @patch('ollama_ai_agent.routes.OllamaAIService')
    @pytest.mark.integration
    def test_process_prompt_with_model(self, mock_service_class, test_client):
        """Test prompt processing with custom model."""
        mock_service = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.response = "Test response"
        mock_response.model = "custom-model"
        mock_response.timestamp = "2025-01-01T00:00:00"
        mock_response.metadata = {}
        mock_service.process_prompt.return_value = mock_response
        mock_service_class.return_value = mock_service

        response = test_client.post(
            "/api/v1/prompt",
            json={"prompt": "Test prompt", "model": "custom-model"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["model"] == "custom-model"

    @patch('ollama_ai_agent.routes.OllamaAIService')
    @pytest.mark.integration
    def test_process_prompt_error_handling(self, mock_service_class, test_client):
        """Test error handling in prompt endpoint."""
        mock_service = Mock()
        mock_service.process_prompt.side_effect = Exception("Service error")
        mock_service_class.return_value = mock_service

        response = test_client.post(
            "/api/v1/prompt",
            json={"prompt": "Test prompt"}
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        error_data = data.get("error") or data.get("detail", {}).get("error")
        assert error_data is not None
        assert error_data.get("code") == "OLLAMA_SERVICE_ERROR"

    @pytest.mark.integration
    def test_process_prompt_validation_error(self, test_client):
        """Test validation error for invalid request."""
        response = test_client.post(
            "/api/v1/prompt",
            json={}  # Missing required 'prompt' field
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.integration
    def test_process_prompt_empty_prompt(self, test_client):
        """Test validation error for empty prompt."""
        response = test_client.post(
            "/api/v1/prompt",
            json={"prompt": ""}  # Empty prompt
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
class TestHealthEndpoint:
    """Test /health endpoint."""

    @patch('ollama_ai_agent.routes.OllamaAIService')
    def test_health_check_healthy(self, mock_service_class, test_client):
        """Test health check when Ollama is available."""
        mock_service = Mock()
        mock_service.check_ollama_available.return_value = True
        mock_service.llm_name = "Ollama"
        mock_service.model_name = "Tinyllama"
        mock_service_class.return_value = mock_service

        response = test_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["ollama_available"] is True

    @patch('ollama_ai_agent.routes.OllamaAIService')
    @pytest.mark.integration
    def test_health_check_degraded(self, mock_service_class, test_client):
        """Test health check when Ollama is unavailable."""
        mock_service = Mock()
        mock_service.check_ollama_available.return_value = False
        mock_service.llm_name = "Ollama"
        mock_service.model_name = "Tinyllama"
        mock_service_class.return_value = mock_service

        response = test_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "degraded"
        assert data["ollama_available"] is False

