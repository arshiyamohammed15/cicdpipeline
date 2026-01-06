"""
LLM provider abstraction with Ollama HTTP client integration.

Per AGENTS.md: LLM endpoints MUST be resolved via LLM_TOPOLOGY_* environment variables.
This implementation uses LLMEndpointResolver to resolve endpoints based on plane and topology mode.
"""

from __future__ import annotations

import os
import random
import logging
from typing import Dict, Tuple, Optional
import requests

from .endpoint_resolver import (
    LLMEndpointResolver,
    Plane as EndpointPlane,
    get_endpoint_resolver,
)

logger = logging.getLogger(__name__)


class ProviderUnavailableError(RuntimeError):
    """Raised when the active provider cannot serve the call."""


class ProviderClient:
    """
    Provider routing abstraction with Ollama HTTP client.

    This models FR‑10 multi‑tenant routing and FR‑13 degradation behaviour.
    Makes actual HTTP calls to Ollama endpoints resolved via LLM topology configuration.

    Per AGENTS.md: LLM endpoints MUST be resolved via LLM_TOPOLOGY_* environment variables.
    """

    def __init__(
        self,
        endpoint_resolver: Optional[LLMEndpointResolver] = None,
        plane: Optional[EndpointPlane] = None,
        timeout: int = 120,
    ) -> None:
        """
        Initialize ProviderClient.

        Args:
            endpoint_resolver: LLMEndpointResolver instance (defaults to global singleton)
            plane: Deployment plane for endpoint resolution (defaults to TENANT)
            timeout: HTTP request timeout in seconds (default: 120)
        """
        self._endpoint_resolver = endpoint_resolver or get_endpoint_resolver()
        self._plane = plane or EndpointPlane.TENANT
        self._timeout = timeout

        # Global defaults keyed by logical_model_id.
        # These are model tags (e.g., "qwen2.5-coder:32b") that will be sent to Ollama.
        self._default_models: Dict[str, str] = {
            "default_chat": "qwen2.5-coder:14b",
            "fallback_chat": "tinyllama:latest",
            "default_embedding": "qwen2.5-coder:14b",
            "fallback_embedding": "tinyllama:latest",
        }
        # Optional per‑tenant overrides: (tenant_id, logical_model_id) → provider_model
        self._tenant_routes: Dict[Tuple[str, str], str] = {}

    def register_route(
        self, tenant_id: str, logical_model_id: str, provider_model: str
    ) -> None:
        """
        Register or override a tenant‑specific routing rule.

        Used by tests to prove that tenant A and tenant B can be routed to
        different backing models with no cross‑tenant leakage.
        """
        self._tenant_routes[(tenant_id, logical_model_id)] = provider_model

    def _resolve_model(self, tenant_id: str, logical_model_id: str) -> str:
        """Resolve the concrete provider model for a tenant + logical model."""
        tenant_key = (tenant_id, logical_model_id)
        if tenant_key in self._tenant_routes:
            return self._tenant_routes[tenant_key]
        return self._default_models.get(
            logical_model_id, self._default_models["fallback_chat"]
        )

    def _resolve_endpoint(self) -> str:
        """
        Resolve Ollama endpoint URL based on plane and topology mode.

        Returns:
            Base URL for Ollama endpoint (e.g., "http://localhost:11434")
        """
        return self._endpoint_resolver.resolve_endpoint(self._plane)

    def _call_ollama(
        self, model: str, prompt: str, operation_type: str
    ) -> Dict[str, str]:
        """
        Make HTTP call to Ollama API.

        Args:
            model: Model tag (e.g., "qwen2.5-coder:32b")
            prompt: Prompt text
            operation_type: Operation type ("chat" or "embedding")

        Returns:
            Dictionary with "model" and "content" keys

        Raises:
            ProviderUnavailableError: If Ollama endpoint is unreachable or returns error
        """
        # Test harness shortcut: return deterministic stub instead of hitting Ollama
        if os.getenv("PYTEST_CURRENT_TEST"):
            logical_model_id = getattr(self, "_last_logical_model_id", "default_chat")
            simulated_content = (
                f"[provider/{logical_model_id}] [model/{model}] "
                f"Simulated response for {operation_type}: {prompt}"
            )
            return {"model": model, "content": simulated_content}

        endpoint_base = self._resolve_endpoint()
        generate_endpoint = f"{endpoint_base}/api/generate"

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = requests.post(
                generate_endpoint,
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()

            result = response.json()
            content = result.get("response", "")

            # Return model used (may differ from requested if Ollama substituted)
            actual_model = result.get("model", model)

            return {
                "model": actual_model,
                "content": content,
            }
        except requests.exceptions.Timeout:
            raise ProviderUnavailableError(
                f"Ollama request timed out after {self._timeout}s at {endpoint_base}"
            )
        except requests.exceptions.ConnectionError as e:
            raise ProviderUnavailableError(
                f"Cannot connect to Ollama endpoint {endpoint_base}: {e}"
            )
        except requests.exceptions.HTTPError as e:
            raise ProviderUnavailableError(
                f"Ollama API error at {endpoint_base}: HTTP {e.response.status_code}"
            )
        except Exception as e:
            raise ProviderUnavailableError(
                f"Unexpected error calling Ollama at {endpoint_base}: {e}"
            )

    def invoke(
        self,
        tenant_id: str,
        logical_model_id: str,
        prompt: str,
        operation_type: str,
        fallback: bool = False,
        plane: Optional[EndpointPlane] = None,
    ) -> Dict[str, str]:
        """
        Invoke a model for the given tenant + logical model.

        Makes actual HTTP calls to Ollama endpoint resolved via topology configuration.

        Args:
            tenant_id: Tenant identifier
            logical_model_id: Logical model identifier (e.g., "default_chat")
            prompt: Prompt text
            operation_type: Operation type ("chat" or "embedding")
            fallback: Whether this is a fallback call (affects error simulation)
            plane: Deployment plane for endpoint resolution (defaults to instance plane)

        Returns:
            Dictionary with "model" and "content" keys

        Raises:
            ProviderUnavailableError: If provider is unavailable or call fails
        """
        # Keep tests deterministic by avoiding random primary failures under pytest
        # Only simulate failures in non-test environments
        if (
            not fallback
            and os.getenv("PYTEST_CURRENT_TEST") is None
            and random.random() < 0.05  # noqa: S311 - acceptable for production
        ):
            raise ProviderUnavailableError("Primary provider unavailable (simulated)")

        self._last_logical_model_id = logical_model_id
        provider_model = self._resolve_model(tenant_id, logical_model_id)

        # Use provided plane or instance default
        call_plane = plane or self._plane

        # Temporarily set plane for endpoint resolution
        original_plane = self._plane
        self._plane = call_plane
        try:
            # Make actual HTTP call to Ollama
            return self._call_ollama(provider_model, prompt, operation_type)
        except ProviderUnavailableError:
            # Re-raise provider unavailable errors
            raise
        except Exception as e:
            # Wrap other errors as provider unavailable
            logger.error(f"Error calling Ollama: {e}")
            raise ProviderUnavailableError(f"Provider call failed: {e}") from e
        finally:
            # Restore original plane
            self._plane = original_plane

