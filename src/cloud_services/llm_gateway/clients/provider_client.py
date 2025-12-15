"""
LLM provider abstraction.
"""

from __future__ import annotations

import random
from typing import Dict, Tuple


class ProviderUnavailableError(RuntimeError):
    """Raised when the active provider cannot serve the call."""


class ProviderClient:
    """
    Provider routing abstraction.

    This models FR‑10 multi‑tenant routing and FR‑13 degradation behaviour in
    a deterministic, in‑memory way suitable for tests.
    """

    def __init__(self) -> None:
        # Global defaults keyed by logical_model_id.
        self._default_models: Dict[str, str] = {
            "default_chat": "provider/gpt-4o",
            "fallback_chat": "provider/gpt-4o-mini",
            "default_embedding": "provider/text-embedding-3-small",
            "fallback_embedding": "provider/text-embedding-3-small",
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

    def invoke(
        self,
        tenant_id: str,
        logical_model_id: str,
        prompt: str,
        operation_type: str,
        fallback: bool = False,
    ) -> Dict[str, str]:
        """
        Invoke a model for the given tenant + logical model.

        For now this remains an in‑memory simulation but enforces the routing
        and failure semantics required for FR‑10 and FR‑13.
        """
        if not fallback and random.random() < 0.05:  # noqa: S311 - acceptable stub
            raise ProviderUnavailableError("Primary provider unavailable")

        provider_model = self._resolve_model(tenant_id, logical_model_id)
        content = (
            f"[{provider_model}] response for operation={operation_type}: {prompt[:200]}"
        )
        return {"model": provider_model, "content": content}

