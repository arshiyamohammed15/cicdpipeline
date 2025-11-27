"""Integration tests for Ollama AI Agent API routes."""
from __future__ import annotations

from unittest.mock import patch, Mock

import pytest
from fastapi import status

import sys
import importlib.util
from pathlib import Path

# Add parent directories to path for imports
# From tests/integration/test_routes.py, go up 3 levels to ollama-ai-agent directory
PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

# Create parent package structure
parent_pkg = type(sys)('ollama_ai_agent')
sys.modules['ollama_ai_agent'] = parent_pkg

# Load models module
models_path = PACKAGE_ROOT / "models.py"
spec_models = importlib.util.spec_from_file_location("ollama_ai_agent.models", models_path)
models_module = importlib.util.module_from_spec(spec_models)
sys.modules['ollama_ai_agent.models'] = models_module
spec_models.loader.exec_module(models_module)
PromptRequest = models_module.PromptRequest

# Load routes module for patching
routes_path = PACKAGE_ROOT / "routes.py"
spec_routes = importlib.util.spec_from_file_location("ollama_ai_agent.routes", routes_path)
routes_module = importlib.util.module_from_spec(spec_routes)
sys.modules['ollama_ai_agent.routes'] = routes_module
spec_routes.loader.exec_module(routes_module)


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
        assert "error" in data
        assert data["error"]["code"] == "OLLAMA_SERVICE_ERROR"

    def test_process_prompt_validation_error(self, test_client):
        """Test validation error for invalid request."""
        response = test_client.post(
            "/api/v1/prompt",
            json={}  # Missing required 'prompt' field
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

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

