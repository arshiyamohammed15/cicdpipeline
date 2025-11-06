"""
Service layer for Ollama AI Agent.

What: Business logic for interacting with Ollama LLM API at http://localhost:11434
Why: Encapsulates LLM communication logic, provides abstraction for route handlers
Reads/Writes: Reads environment variables (OLLAMA_BASE_URL, OLLAMA_TIMEOUT), writes HTTP requests to Ollama API
Contracts: Ollama API contract (/api/generate, /api/tags), returns PromptResponse model
Risks: Network failures, timeout errors, invalid API responses, potential exposure of prompts in error messages
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
import requests
from .models import PromptRequest, PromptResponse


class OllamaAIService:
    """Service for interacting with Ollama LLM API."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        """
        Initialize the Ollama AI Service.

        Args:
            base_url: Base URL for Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))

    def check_ollama_available(self) -> bool:
        """
        Check if Ollama service is available.

        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
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
        payload: Dict[str, Any] = {
            "model": request.model or "tinyllama",
            "prompt": request.prompt,
            "stream": request.stream or False
        }

        if request.options:
            payload["options"] = request.options

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

            return PromptResponse(
                success=True,
                response=response_text,
                model=result.get("model", request.model or "tinyllama"),
                timestamp=datetime.utcnow().isoformat(),
                metadata={
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "prompt_eval_count": result.get("prompt_eval_count"),
                    "eval_count": result.get("eval_count")
                }
            )
        except requests.exceptions.RequestException as exc:
            raise Exception(f"Failed to communicate with Ollama service: {str(exc)}")
        except Exception as exc:
            raise Exception(f"Error processing prompt: {str(exc)}")
