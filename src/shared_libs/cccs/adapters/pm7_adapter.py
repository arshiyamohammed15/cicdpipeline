"""
PM-7 (Evidence & Audit Ledger) façade adapter.

Calls PM-7 service for receipt indexing and Merkle proof generation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class PM7AdapterConfig:
    """Configuration for PM-7 adapter."""

    base_url: str
    timeout_seconds: float = 5.0
    api_version: str = "v1"


class PM7ReceiptAdapter:
    """Façade adapter for PM-7 Evidence & Audit Ledger service."""

    def __init__(self, config: PM7AdapterConfig):
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            headers={"Content-Type": "application/json"},
        )

    async def index_receipt(self, receipt: Dict[str, Any]) -> Dict[str, Any]:
        """
        Index receipt via PM-7 service.

        Raises:
            Exception: If indexing fails
        """
        try:
            response = await self._client.post(
                f"/evidence/{self._config.api_version}/receipts",
                json=receipt,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"PM-7 receipt indexing failed: {e.response.status_code} - {e.response.text}")
            raise Exception(f"PM-7 receipt indexing failed: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"PM-7 request failed: {e}")
            raise Exception("PM-7 service unavailable") from e

    async def index_batch(
        self, receipts: List[Dict[str, Any]], batch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Index batch of receipts via PM-7 service."""
        try:
            payload = {"receipts": receipts}
            if batch_id:
                payload["batch_id"] = batch_id

            response = await self._client.post(
                f"/evidence/{self._config.api_version}/batches",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"PM-7 batch indexing failed: {e.response.status_code} - {e.response.text}")
            raise Exception(f"PM-7 batch indexing failed: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"PM-7 request failed: {e}")
            raise Exception("PM-7 service unavailable") from e

    async def generate_merkle_proof(
        self, receipt_id: str, batch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate Merkle proof for receipt via PM-7."""
        try:
            payload = {"receipt_id": receipt_id}
            if batch_id:
                payload["batch_id"] = batch_id

            response = await self._client.post(
                f"/evidence/{self._config.api_version}/merkle-proof",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"PM-7 Merkle proof failed: {e.response.status_code} - {e.response.text}")
            raise Exception(f"PM-7 Merkle proof failed: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"PM-7 request failed: {e}")
            raise Exception("PM-7 service unavailable") from e

    async def health_check(self) -> bool:
        """Check PM-7 service health."""
        try:
            response = await self._client.get(f"/evidence/{self._config.api_version}/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
