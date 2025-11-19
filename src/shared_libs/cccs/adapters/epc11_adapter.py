"""
EPC-11 (Key Management Service) façade adapter.

Calls EPC-11 service for Ed25519/HSM-backed signing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class EPC11AdapterConfig:
    """Configuration for EPC-11 adapter."""

    base_url: str
    timeout_seconds: float = 5.0
    api_version: str = "v1"
    key_id: Optional[str] = None  # HSM key identifier


class EPC11SigningAdapter:
    """
    Façade adapter for EPC-11 Key Management Service.

    Calls EPC-11 endpoints for Ed25519/HSM-backed signing per KMS spec.
    """

    def __init__(self, config: EPC11AdapterConfig):
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            headers={"Content-Type": "application/json"},
        )

    async def sign_receipt(
        self, receipt_payload: Dict[str, Any], key_id: Optional[str] = None
    ) -> str:
        """
        Sign receipt using Ed25519/HSM-backed key via EPC-11.

        Raises:
            Exception: If signing fails
        """
        try:
            signing_key_id = key_id or self._config.key_id
            if not signing_key_id:
                raise ValueError("Key ID required for signing")

            response = await self._client.post(
                f"/kms/{self._config.api_version}/sign",
                json={
                    "payload": receipt_payload,
                    "key_id": signing_key_id,
                    "algorithm": "Ed25519",
                },
            )
            response.raise_for_status()
            result = response.json()
            return result.get("signature", "")
        except httpx.HTTPStatusError as e:
            logger.error(f"EPC-11 signing failed: {e.response.status_code} - {e.response.text}")
            raise Exception(f"EPC-11 signing failed: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"EPC-11 request failed: {e}")
            raise Exception("EPC-11 service unavailable") from e

    async def verify_signature(
        self, payload: Dict[str, Any], signature: str, key_id: Optional[str] = None
    ) -> bool:
        """
        Verify Ed25519 signature via EPC-11.

        Returns:
            True if signature is valid

        Raises:
            Exception: If verification fails
        """
        try:
            signing_key_id = key_id or self._config.key_id
            if not signing_key_id:
                raise ValueError("Key ID required for verification")

            response = await self._client.post(
                f"/kms/{self._config.api_version}/verify",
                json={
                    "payload": payload,
                    "signature": signature,
                    "key_id": signing_key_id,
                    "algorithm": "Ed25519",
                },
            )
            response.raise_for_status()
            result = response.json()
            return result.get("valid", False)
        except httpx.HTTPStatusError as e:
            logger.error(f"EPC-11 verification failed: {e.response.status_code} - {e.response.text}")
            return False
        except httpx.RequestError as e:
            logger.error(f"EPC-11 request failed: {e}")
            return False

    async def health_check(self) -> bool:
        """Check EPC-11 service health."""
        try:
            response = await self._client.get(f"/kms/{self._config.api_version}/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()
