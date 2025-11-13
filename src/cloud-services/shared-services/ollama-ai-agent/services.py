"""
Service layer for Ollama AI Agent.

What: Business logic for interacting with Ollama LLM API using shared services configuration
Why: Encapsulates LLM communication logic, provides abstraction for route handlers, uses shared services plane configuration
Reads/Writes: Reads configuration from shared/llm/ollama/config.json and shared/llm/tinyllama/config.json, writes HTTP requests to Ollama API
Contracts: Ollama API contract (/api/generate, /api/tags), returns PromptResponse model
Risks: Network failures, timeout errors, invalid API responses, potential exposure of prompts in error messages
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import requests
from .models import PromptRequest, PromptResponse


def _load_shared_services_config(config_type: str) -> Dict[str, Any]:
    """
    Load configuration from shared services plane.

    Args:
        config_type: Type of configuration ('ollama' or 'tinyllama')

    Returns:
        Configuration dictionary, or empty dict if not found
    """
    try:
        # Get ZU_ROOT from environment variable (per folder-business-rules.md)
        zu_root = os.getenv("ZU_ROOT")

        if zu_root:
            # Use ZU_ROOT for shared services plane
            config_path = Path(zu_root) / "shared" / "llm" / config_type / "config.json"
        else:
            # Fallback: try project root (for development/testing)
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent.parent.parent
            config_path = project_root / "shared" / "llm" / config_type / "config.json"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass

    return {}


class OllamaAIService:
    """Service for interacting with Ollama LLM API using shared services configuration."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        """
        Initialize the Ollama AI Service.

        Args:
            base_url: Base URL for Ollama API (overrides config if provided)
        """
        # Load configuration from shared services plane
        ollama_config = _load_shared_services_config("ollama")
        tinyllama_config = _load_shared_services_config("tinyllama")

        # Use shared services config, fallback to environment, then default
        self.base_url = (
            base_url or
            os.getenv("OLLAMA_BASE_URL") or
            ollama_config.get("base_url", "http://localhost:11434")
        )

        # Get API endpoints from config
        api_endpoints = ollama_config.get("api_endpoints", {})
        generate_path = api_endpoints.get("generate", "/api/generate")
        self.generate_endpoint = f"{self.base_url}{generate_path}"

        # Get timeout from config
        self.timeout = int(
            os.getenv("OLLAMA_TIMEOUT") or
            ollama_config.get("timeout", "120")
        )

        # Store Tinyllama config for default model
        self.tinyllama_config = tinyllama_config

        # Get configurable names from config
        self.llm_name = ollama_config.get("llm_name", "Ollama")
        self.model_name = tinyllama_config.get("model_name", "Tinyllama") if tinyllama_config else "Tinyllama"

    def check_ollama_available(self) -> bool:
        """
        Check if Ollama service is available.

        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            # Load config to get tags endpoint
            ollama_config = _load_shared_services_config("ollama")
            api_endpoints = ollama_config.get("api_endpoints", {})
            tags_path = api_endpoints.get("tags", "/api/tags")
            tags_endpoint = f"{self.base_url}{tags_path}"

            response = requests.get(tags_endpoint, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def process_prompt(self, request: PromptRequest) -> PromptResponse:
        """
        Process a prompt and return the LLM response.

        Args:
            request: The prompt request containing prompt text and options

        Returns:
            PromptResponse with the generated text

        Raises:
            Exception: If the request to Ollama fails
        """
        # Get default model from Tinyllama config if available
        default_model = "tinyllama"
        if self.tinyllama_config:
            default_model = self.tinyllama_config.get("model_id", "tinyllama:latest")

        # Merge default options from Tinyllama config
        model_options = {}
        if self.tinyllama_config and not request.options:
            model_options = self.tinyllama_config.get("default_options", {}).copy()

        payload: Dict[str, Any] = {
            "model": request.model or default_model,
            "prompt": request.prompt,
            "stream": request.stream or False
        }

        if request.options:
            payload["options"] = request.options
        elif model_options:
            payload["options"] = model_options

        try:
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()

            # Extract response text from Ollama API response
            response_text = result.get("response", "")

            # Get default model from config
            default_model = "tinyllama"
            if self.tinyllama_config:
                default_model = self.tinyllama_config.get("model_id", "tinyllama:latest")

            return PromptResponse(
                success=True,
                response=response_text,
                model=result.get("model", request.model or default_model),
                timestamp=datetime.utcnow().isoformat(),
                metadata={
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "prompt_eval_count": result.get("prompt_eval_count"),
                    "eval_count": result.get("eval_count")
                }
            )
        except requests.exceptions.Timeout:
            raise Exception(f"Ollama request timed out after {self.timeout}s. The model may be taking too long to generate or may be unresponsive. Try: 1) Restart Ollama service, 2) Check if model is loaded correctly, 3) Try a simpler prompt.")
        except requests.exceptions.RequestException as exc:
            raise Exception(f"Failed to communicate with Ollama service: {str(exc)}")
        except Exception as exc:
            raise Exception(f"Error processing prompt: {str(exc)}")
