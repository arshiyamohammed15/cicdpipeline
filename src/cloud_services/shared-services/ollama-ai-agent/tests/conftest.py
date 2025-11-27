"""Pytest fixtures for Ollama AI Agent tests."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

import sys
import importlib.util
from pathlib import Path

# Add parent directories to path for imports
# From tests/conftest.py, go up 2 levels to ollama-ai-agent directory
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

# Create parent package structure for relative imports
parent_pkg = type(sys)('ollama_ai_agent')
sys.modules['ollama_ai_agent'] = parent_pkg

# Load models module first (needed by routes and services)
models_path = PACKAGE_ROOT / "models.py"
spec_models = importlib.util.spec_from_file_location("ollama_ai_agent.models", models_path)
models_module = importlib.util.module_from_spec(spec_models)
sys.modules['ollama_ai_agent.models'] = models_module
spec_models.loader.exec_module(models_module)

# Load services module (needed by routes)
services_path = PACKAGE_ROOT / "services.py"
spec_services = importlib.util.spec_from_file_location("ollama_ai_agent.services", services_path)
services_module = importlib.util.module_from_spec(spec_services)
sys.modules['ollama_ai_agent.services'] = services_module
spec_services.loader.exec_module(services_module)

# Load routes module (needed by main)
routes_path = PACKAGE_ROOT / "routes.py"
spec_routes = importlib.util.spec_from_file_location("ollama_ai_agent.routes", routes_path)
routes_module = importlib.util.module_from_spec(spec_routes)
sys.modules['ollama_ai_agent.routes'] = routes_module
spec_routes.loader.exec_module(routes_module)

# Load middleware and llm_manager (needed by main)
middleware_path = PACKAGE_ROOT / "middleware.py"
spec_middleware = importlib.util.spec_from_file_location("ollama_ai_agent.middleware", middleware_path)
middleware_module = importlib.util.module_from_spec(spec_middleware)
sys.modules['ollama_ai_agent.middleware'] = middleware_module
spec_middleware.loader.exec_module(middleware_module)

llm_manager_path = PACKAGE_ROOT / "llm_manager.py"
spec_llm_manager = importlib.util.spec_from_file_location("ollama_ai_agent.llm_manager", llm_manager_path)
llm_manager_module = importlib.util.module_from_spec(spec_llm_manager)
sys.modules['ollama_ai_agent.llm_manager'] = llm_manager_module
spec_llm_manager.loader.exec_module(llm_manager_module)

# Now load main module
main_path = PACKAGE_ROOT / "main.py"
spec_main = importlib.util.spec_from_file_location("ollama_ai_agent.main", main_path)
main_module = importlib.util.module_from_spec(spec_main)
sys.modules['ollama_ai_agent.main'] = main_module
spec_main.loader.exec_module(main_module)
app = main_module.app


@pytest.fixture
def test_client():
    """Provide FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_ollama_config():
    """Mock Ollama configuration."""
    return {
        "base_url": "http://localhost:11434",
        "api_endpoints": {
            "generate": "/api/generate",
            "tags": "/api/tags"
        },
        "timeout": "120",
        "llm_name": "Ollama"
    }


@pytest.fixture
def mock_tinyllama_config():
    """Mock Tinyllama configuration."""
    return {
        "model_id": "tinyllama:latest",
        "model_name": "Tinyllama",
        "default_options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }


@pytest.fixture
def zu_root_env(tmp_path, monkeypatch):
    """Set up ZU_ROOT environment variable for tests."""
    zu_root = tmp_path / "zu_root"
    zu_root.mkdir()
    (zu_root / "shared" / "llm" / "ollama").mkdir(parents=True)
    (zu_root / "shared" / "llm" / "tinyllama").mkdir(parents=True)
    monkeypatch.setenv("ZU_ROOT", str(zu_root))
    return zu_root


@pytest.fixture
def mock_ollama_response():
    """Mock successful Ollama API response."""
    return {
        "response": "This is a test response",
        "model": "tinyllama:latest",
        "total_duration": 1000000000,
        "load_duration": 500000000,
        "prompt_eval_count": 10,
        "eval_count": 20
    }

