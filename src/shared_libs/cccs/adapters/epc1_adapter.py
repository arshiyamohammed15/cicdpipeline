"""
EPC-1 (Identity & Access Management) façade adapter.

Calls EPC-1 service endpoints for identity verification and actor provenance.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from ..exceptions import ActorUnavailableError
from ..types import ActorBlock, ActorContext

logger = logging.getLogger(__name__)


def _sanitize_error_message(error_text: str, max_length: int = 200) -> str:
    """CR-039: Sanitize error messages to prevent information disclosure."""
    # Remove potential sensitive data patterns
    sanitized = error_text
    # Remove potential tokens/keys
    sanitized = sanitized.replace(r'Bearer ', 'Bearer [REDACTED] ')
    sanitized = sanitized.replace(r'api_key=', 'api_key=[REDACTED]')
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + '...'
    return sanitized


@dataclass
class EPC1AdapterConfig:
    """Configuration for EPC-1 adapter."""

    base_url: str
    timeout_seconds: float = 5.0
    api_version: str = "v1"


class EPC1IdentityAdapter:
    """
    Façade adapter for EPC-1 Identity & Access Management service.

    Calls /iam/v1/verify and /iam/v1/decision endpoints per IAM spec v1.1.0.
    """

    def __init__(self, config: EPC1AdapterConfig):
        self._config = config
        # CR-036: Configure separate connection and read timeouts
        timeout = httpx.Timeout(
            connect=min(config.timeout_seconds, 5.0),  # Connection timeout
            read=config.timeout_seconds,  # Read timeout
            write=config.timeout_seconds,  # Write timeout
            pool=10.0  # Pool timeout
        )
        # CR-040: Configure connection pooling limits
        limits = httpx.Limits(
            max_keepalive_connections=10,
            max_connections=20,
            keepalive_expiry=30.0
        )
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=timeout,
            limits=limits,
            headers={"Content-Type": "application/json"},
        )

    async def verify_identity(
        self, context: ActorContext, token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify identity via EPC-1 /iam/v1/verify endpoint.

        Args:
            context: Actor context with tenant_id, user_id, device_id, session_id
            token: Optional JWT token for authentication

        Returns:
            Verification response with identity metadata

        Raises:
            ActorUnavailableError: If EPC-1 service is unavailable or verification fails
        """
        # CR-038: Add request ID for tracing
        request_id = str(uuid.uuid4())
        headers = {"X-Request-ID": request_id}
        
        try:
            payload = {
                "tenant_id": context.tenant_id,
                "user_id": context.user_id,
                "device_id": context.device_id,
                "session_id": context.session_id,
                "actor_type": context.actor_type,
            }
            if token:
                payload["token"] = token

            response = await self._client.post(
                f"/iam/{self._config.api_version}/verify",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # CR-039: Sanitize error messages
            error_text = _sanitize_error_message(str(e.response.text))
            logger.error(f"EPC-1 verification failed (request_id={request_id}): {e.response.status_code} - {error_text}")
            raise ActorUnavailableError(f"EPC-1 verification failed: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"EPC-1 request failed (request_id={request_id}): {type(e).__name__}")
            raise ActorUnavailableError("EPC-1 service unavailable") from e

    async def get_actor_provenance(
        self, context: ActorContext
    ) -> Dict[str, Any]:
        """
        Get actor provenance metadata via EPC-1.

        Returns provenance signature, normalization version, and warnings.

        Args:
            context: Actor context

        Returns:
            Provenance metadata with signature and version

        Raises:
            ActorUnavailableError: If EPC-1 service is unavailable
        """
        try:
            payload = {
                "tenant_id": context.tenant_id,
                "user_id": context.user_id,
                "device_id": context.device_id,
                "session_id": context.session_id,
            }

            response = await self._client.post(
                f"/iam/{self._config.api_version}/decision",
                json={
                    **payload,
                    "action": "get_provenance",
                    "resource": "actor_metadata",
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"EPC-1 provenance failed: {e.response.status_code} - {e.response.text}")
            raise ActorUnavailableError(f"EPC-1 provenance failed: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"EPC-1 request failed: {e}")
            raise ActorUnavailableError("EPC-1 service unavailable") from e

    async def resolve_actor(self, context: ActorContext) -> ActorBlock:
        """
        Resolve actor block by calling EPC-1 service.

        Combines identity verification and provenance metadata.

        Args:
            context: Actor context

        Returns:
            ActorBlock with actor_id, provenance_signature, normalization_version

        Raises:
            ActorUnavailableError: If EPC-1 service is unavailable or context invalid
        """
        # Verify identity first
        verify_result = await self.verify_identity(context)

        # Get provenance metadata
        provenance_result = await self.get_actor_provenance(context)

        # Extract actor_id from verification result
        actor_id = verify_result.get("actor_id") or verify_result.get("user_id")
        if not actor_id:
            raise ActorUnavailableError("EPC-1 did not return actor_id")

        return ActorBlock(
            actor_id=actor_id,
            actor_type=context.actor_type,
            session_id=context.session_id,
            provenance_signature=provenance_result.get("provenance_signature", ""),
            normalization_version=provenance_result.get("normalization_version", "v1"),
            warnings=tuple(provenance_result.get("warnings", [])),
            salt_version=provenance_result.get("salt_version", ""),  # EPC-1 salt version per PRD §9
            monotonic_counter=provenance_result.get("monotonic_counter", 0),  # Provenance counter per PRD §9
        )

    async def health_check(self) -> bool:
        """
        Check EPC-1 service health.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self._client.get(f"/iam/{self._config.api_version}/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()

