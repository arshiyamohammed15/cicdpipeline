"""
IAM client that validates actor identity and permissions via EPC-1 (IAM service).

Per §14.3, validates actor identity, roles, capabilities, and scope before
allowing LLM requests to proceed.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx
from fastapi import HTTPException, status

from ..models import Actor


class IAMClient:
    """Validates actor claims via IAM service (EPC-1) per §14.3."""

    _required_capabilities = {"llm.invoke"}

    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 2.0):
        self.base_url = base_url or os.getenv(
            "IAM_SERVICE_URL", "http://localhost:8001/iam/v1"
        )
        self.timeout = timeout_seconds

    def validate_actor(self, actor: Actor, scope: str) -> None:
        """
        Validate actor identity and permissions via IAM service.

        Calls IAM /decision endpoint to verify:
        - Actor identity (actor_id)
        - Required capabilities (llm.invoke)
        - Scope authorization (llm.{operation_type})
        - Session assurance level

        Raises HTTPException if validation fails.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/decision",
                    json={
                        "subject": {
                            "subject_id": actor.actor_id,
                            "subject_type": actor.actor_type.value,
                            "roles": actor.roles,
                            "capabilities": actor.capabilities,
                            "scopes": actor.scopes or [],
                        },
                        "action": scope,
                        "resource": {"resource_type": "llm_gateway", "resource_id": "*"},
                        "context": {
                            "session_assurance_level": actor.session_assurance_level,
                            "workspace_id": actor.workspace_id,
                        },
                    },
                )
                response.raise_for_status()
                decision = response.json()

                if decision.get("decision") != "ALLOW":
                    reason = decision.get("reason", "Access denied")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"IAM decision: {reason}",
                    )

                # Additional capability check
                missing: set[str] = self._required_capabilities - set(actor.capabilities)
                if missing:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Actor lacks required capabilities: {', '.join(missing)}",
                    )

                # Session assurance check
                if actor.session_assurance_level == "low":
                    raise HTTPException(
                        status_code=status.HTTP_412_PRECONDITION_FAILED,
                        detail="Session assurance insufficient for gateway access",
                    )

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IAM service denied access",
                ) from exc
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="IAM service unavailable",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"IAM service connection failed: {exc}",
            ) from exc

