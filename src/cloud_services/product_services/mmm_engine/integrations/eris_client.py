"""
ERIS (EPC-7) client for MMM Engine.

Provides real HTTP transport with circuit breaker plus a mock fallback for dev/tests.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx

from ..dependencies import MockERISClient
from ..reliability.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class ERISClient:
    """HTTP client wrapper for Evidence & Receipt Indexing Service."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: float = 3.0,
    ) -> None:
        self.base_url = base_url or os.getenv("MMM_ERIS_BASE_URL")
        self.timeout = timeout_seconds
        self.use_mock = not self.base_url
        self._mock = MockERISClient() if self.use_mock else None
        self._breaker = CircuitBreaker(name="eris_client", failure_threshold=5, recovery_timeout=60.0)

    async def emit_receipt(self, receipt: Dict[str, Any]) -> Optional[str]:
        if self.use_mock:
            return await self._mock.emit_receipt(receipt)  # type: ignore[union-attr]

        async def _call():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/evidence/receipts",
                    json=receipt,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("receipt_id")

        return await self._breaker.call_async(_call)


