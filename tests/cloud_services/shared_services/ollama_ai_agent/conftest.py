"""
Test fixtures for Ollama AI Agent.

Uses standardized module setup from root conftest.py
"""
import pytest
from pathlib import Path
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Root conftest should have set up ollama_ai_agent package
# But ensure module path is in sys.path
MODULE_ROOT = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "shared-services" / "ollama-ai-agent"
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

# Import will work because root conftest.py sets up the package structure
# Tests can use: from ollama_ai_agent.main import app


@pytest.fixture(scope="module")
def test_client():
    """Provide a lightweight FastAPI TestClient for Ollama routes."""
    try:
        import ollama_ai_agent.routes as routes_module
    except Exception:
        routes_module = None

    app = FastAPI()

    if routes_module is not None:
        app.include_router(routes_module.router, prefix="/api/v1")

        def _service_factory():
            class DummyService:
                llm_name = "Ollama"
                model_name = "Tinyllama"

                def check_ollama_available(self):
                    return False

                def process_prompt(self, request):
                    return {
                        "success": True,
                        "response": "stub",
                        "model": getattr(request, "model", "tinyllama"),
                        "timestamp": "1970-01-01T00:00:00Z",
                        "metadata": {},
                    }

            service_cls = getattr(routes_module, "OllamaAIService", DummyService)
            if isinstance(service_cls, type):
                service_cls = DummyService
            try:
                return service_cls()
            except Exception:
                return DummyService()

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


@pytest.fixture
def zu_root_env(tmp_path, monkeypatch):
    """Create a temporary ZU_ROOT with shared/llm structure."""
    root = tmp_path / "zu_root"
    for subdir in ("ollama", "tinyllama"):
        (root / "shared" / "llm" / subdir).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("ZU_ROOT", str(root))
    return root


@pytest.fixture
def mock_ollama_config():
    """Sample Ollama config payload."""
    return {
        "base_url": "http://localhost:11434",
        "api_endpoints": {"generate": "/api/generate", "tags": "/api/tags"},
        "timeout": "120",
        "llm_name": "Ollama",
    }


@pytest.fixture
def mock_ollama_response():
    """Sample Ollama API response payload."""
    return {
        "response": "This is a test response",
        "model": "tinyllama:latest",
        "total_duration": 1,
        "load_duration": 1,
        "prompt_eval_count": 1,
        "eval_count": 1,
    }
