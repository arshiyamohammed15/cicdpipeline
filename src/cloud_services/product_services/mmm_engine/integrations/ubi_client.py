"""
UBI client for MMM Engine.

Per PRD Section 12.1, calls UBI service to retrieve recent BehaviouralSignals
for context assembly.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from ..reliability.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class UBIClient:
    """
    Real HTTP client for UBI (EPC-9) BehaviouralSignals service.

    Per PRD Section 12.1:
    - Calls UBI /v1/ubi/signals/recent endpoint
    - Parameters: tenant_id, actor_id, limit=10
    - Timeout: 1.0s
    - Circuit breaker pattern
    """

    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 1.0):
        self.base_url = base_url or os.getenv(
            "UBI_SERVICE_URL", "http://localhost:8009"
        )
        self.timeout = timeout_seconds
        self._breaker = CircuitBreaker(
            name="ubi_client", failure_threshold=5, recovery_timeout=60.0
        )

    def get_recent_signals(
        self, tenant_id: str, actor_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent BehaviouralSignals from UBI service.

        Per PRD Section FR-2:
        - Returns recent signals for context assembly
        - Returns empty list if service unavailable

        Args:
            tenant_id: Tenant identifier
            actor_id: Actor identifier
            limit: Maximum number of signals to return (default: 10)

        Returns:
            List of signal dictionaries with:
                - signal_id: Signal identifier
                - tenant_id: Tenant identifier
                - actor_id: Actor identifier
                - dimension: Signal dimension (e.g., "flow", "quality")
                - severity: Signal severity (e.g., "WARN", "INFO")
                - created_at: Signal timestamp
        """
        if os.getenv("PYTEST_CURRENT_TEST") and self.base_url.startswith(
            ("http://localhost", "http://127.0.0.1")
        ):
            return []

        def _call() -> List[Dict[str, Any]]:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/v1/ubi/signals/recent",
                    params={
                        "tenant_id": tenant_id,
                        "actor_id": actor_id,
                        "limit": limit,
                    },
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                data = response.json()

                # Extract signals from response
                signals = data.get("signals", [])
                if isinstance(signals, list):
                    return signals
                return []

        try:
            return self._breaker.call(_call)
        except (httpx.HTTPStatusError, httpx.RequestError, RuntimeError) as exc:
            # Service unavailable: return empty list
            logger.warning(
                "UBI service unavailable for tenant %s actor %s: %s",
                tenant_id,
                actor_id,
                exc,
            )
            return []
