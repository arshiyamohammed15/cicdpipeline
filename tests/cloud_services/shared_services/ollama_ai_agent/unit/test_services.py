from __future__ import annotations
"""Unit tests for Ollama AI Agent service layer."""

# Imports handled by conftest.py

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import requests

import sys
import importlib.util
from pathlib import Path

# Add parent directories to path for imports
# From tests/unit/test_services.py, go up 3 levels to ollama-ai-agent directory
PACKAGE_ROOT = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "shared-services" / "ollama-ai-agent"
# Path setup handled by conftest.py
# Create parent package structure for relative imports
parent_pkg = type(sys)('ollama_ai_agent')
sys.modules['ollama_ai_agent'] = parent_pkg

# Load models module first (needed by services)
models_path = PACKAGE_ROOT / "models.py"
spec_models = importlib.util.spec_from_file_location("ollama_ai_agent.models", models_path)
models_module = importlib.util.module_from_spec(spec_models)
sys.modules['ollama_ai_agent.models'] = models_module
spec_models.loader.exec_module(models_module)

# Load services module
services_path = PACKAGE_ROOT / "services.py"
spec_services = importlib.util.spec_from_file_location("ollama_ai_agent.services", services_path)
services_module = importlib.util.module_from_spec(spec_services)
sys.modules['ollama_ai_agent.services'] = services_module
spec_services.loader.exec_module(services_module)

# Import the classes
OllamaAIService = services_module.OllamaAIService
_load_shared_services_config = services_module._load_shared_services_config
PromptRequest = models_module.PromptRequest


@pytest.mark.unit
class TestLoadSharedServicesConfig:
    """Test configuration loading from shared services plane."""

    def test_load_config_with_zu_root(self, zu_root_env, mock_ollama_config):
        """Test loading config when ZU_ROOT is set."""
        config_path = zu_root_env / "shared" / "llm" / "ollama" / "config.json"
        config_path.write_text(json.dumps(mock_ollama_config))

        config = _load_shared-services_config("ollama")
        assert config["base_url"] == "http://localhost:11434"
        assert "api_endpoints" in config

    def test_load_config_missing_file(self, zu_root_env):
        """Test loading config when file doesn't exist."""
        config = _load_shared-services_config("ollama")
        assert config == {}

    def test_load_config_fallback_when_no_zu_root(self, monkeypatch):
        """Test fallback when ZU_ROOT is not set."""
        monkeypatch.delenv("ZU_ROOT", raising=False)
        config = _load_shared-services_config("ollama")
        assert isinstance(config, dict)


@pytest.mark.unit
class TestOllamaAIService:
    """Test OllamaAIService class."""

    def test_service_initialization_default(self):
        """Test service initialization with defaults."""
        service = OllamaAIService()
        assert service.base_url == "http://localhost:11434"
        assert service.timeout == 120
        assert service.llm_name == "Ollama"

    def test_service_initialization_custom_base_url(self):
        """Test service initialization with custom base URL."""
        service = OllamaAIService(base_url="http://custom:8080")
        assert service.base_url == "http://custom:8080"

    @patch('requests.get')
    def test_check_ollama_available_success(self, mock_get):
        """Test checking Ollama availability when service is available."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        service = OllamaAIService()
        result = service.check_ollama_available()
        assert result is True

    @patch('requests.get')
    def test_check_ollama_available_failure(self, mock_get):
        """Test checking Ollama availability when service is unavailable."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        service = OllamaAIService()
        result = service.check_ollama_available()
        assert result is False

    @patch('requests.get')
    def test_check_ollama_available_timeout(self, mock_get):
        """Test checking Ollama availability when request times out."""
        mock_get.side_effect = requests.exceptions.Timeout()

        service = OllamaAIService()
        result = service.check_ollama_available()
        assert result is False

    @patch('requests.post')
    def test_process_prompt_success(self, mock_post, mock_ollama_response):
        """Test successful prompt processing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_ollama_response
        mock_post.return_value = mock_response

        service = OllamaAIService()
        request = PromptRequest(prompt="Test prompt")
        result = service.process_prompt(request)

        assert result.success is True
        assert result.response == "This is a test response"
        assert result.model == "tinyllama:latest"
        assert "timestamp" in result.timestamp
        assert result.metadata is not None

    @patch('requests.post')
    def test_process_prompt_with_custom_model(self, mock_post, mock_ollama_response):
        """Test prompt processing with custom model."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_ollama_response["model"] = "custom-model"
        mock_response.json.return_value = mock_ollama_response
        mock_post.return_value = mock_response

        service = OllamaAIService()
        request = PromptRequest(prompt="Test prompt", model="custom-model")
        result = service.process_prompt(request)

        assert result.model == "custom-model"

    @patch('requests.post')
    def test_process_prompt_timeout(self, mock_post):
        """Test prompt processing when request times out."""
        mock_post.side_effect = requests.exceptions.Timeout()

        service = OllamaAIService()
        request = PromptRequest(prompt="Test prompt")

        with pytest.raises(Exception) as exc_info:
            service.process_prompt(request)
        assert "timed out" in str(exc_info.value).lower()

    @patch('requests.post')
    def test_process_prompt_connection_error(self, mock_post):
        """Test prompt processing when connection fails."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        service = OllamaAIService()
        request = PromptRequest(prompt="Test prompt")

        with pytest.raises(Exception) as exc_info:
            service.process_prompt(request)
        assert "Failed to communicate" in str(exc_info.value)

    @patch('requests.post')
    def test_process_prompt_http_error(self, mock_post):
        """Test prompt processing when HTTP error occurs."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server error")
        mock_post.return_value = mock_response

        service = OllamaAIService()
        request = PromptRequest(prompt="Test prompt")

        with pytest.raises(Exception) as exc_info:
            service.process_prompt(request)
        assert "Error processing prompt" in str(exc_info.value)

    @patch('requests.post')
    def test_process_prompt_with_options(self, mock_post, mock_ollama_response):
        """Test prompt processing with custom options."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_ollama_response
        mock_post.return_value = mock_response

        service = OllamaAIService()
        request = PromptRequest(
            prompt="Test prompt",
            options={"temperature": 0.9, "top_p": 0.95}
        )
        result = service.process_prompt(request)

        # Verify options were passed to API
        call_args = mock_post.call_args
        assert "options" in call_args[1]["json"]
        assert call_args[1]["json"]["options"]["temperature"] == 0.9

    @patch('requests.post')
    def test_process_prompt_with_stream(self, mock_post, mock_ollama_response):
        """Test prompt processing with streaming enabled."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_ollama_response
        mock_post.return_value = mock_response

        service = OllamaAIService()
        request = PromptRequest(prompt="Test prompt", stream=True)
        service.process_prompt(request)

        # Verify stream parameter was passed
        call_args = mock_post.call_args
        assert call_args[1]["json"]["stream"] is True

