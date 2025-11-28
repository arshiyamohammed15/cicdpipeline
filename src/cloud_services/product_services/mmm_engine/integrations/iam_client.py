"""
IAM client for MMM Engine that validates actor identity and permissions via EPC-1 (IAM service).

Per PRD Section 12.8, validates JWT tokens and actor permissions for all API requests.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Tuple

import httpx
from fastapi import HTTPException, status

from ..reliability.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class IAMClient:
    """Validates actor claims via IAM service (EPC-1) per PRD Section 12.8."""

    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 2.0):
        self.base_url = base_url or os.getenv(
            "IAM_SERVICE_URL", "http://localhost:8001/iam/v1"
        )
        self.timeout = timeout_seconds
        self._breaker = CircuitBreaker(
            name="iam_client", failure_threshold=5, recovery_timeout=60.0
        )

    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Verify JWT token via IAM service.

        Calls IAM /v1/iam/verify endpoint to validate token and extract claims.

        Returns:
            Tuple of (success, claims, error_message)
        """
        try:
            def _call():
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/verify",
                        json={"token": token},
                        headers={"Content-Type": "application/json"},
                    )
                    response.raise_for_status()
                    data = response.json()
                    if data.get("valid"):
                        return True, data.get("claims", {}), None
                    return False, None, data.get("error", "Token invalid")

            return self._breaker.call(_call)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                return False, None, "Token invalid or expired"
            logger.error("IAM verify error: %s", exc)
            return False, None, "IAM service error"
        except httpx.RequestError as exc:
            logger.error("IAM connection error: %s", exc)
            return False, None, f"IAM service unavailable: {exc}"
        except RuntimeError as exc:
            # Circuit breaker open
            logger.warning("IAM circuit breaker open: %s", exc)
            return False, None, "IAM service temporarily unavailable"
        except Exception as exc:
            logger.exception("Unexpected IAM verify error: %s", exc)
            return False, None, "IAM verification failed"

    def validate_actor(self, actor_id: str, actor_type: str, scope: str, tenant_id: str) -> None:
        """
        Validate actor permissions via IAM service.

        Calls IAM /v1/iam/decision endpoint to verify:
        - Actor identity (actor_id)
        - Required scope authorization (e.g., "mmm.decide")
        - Tenant context

        Raises HTTPException if validation fails.
        """
        try:
            def _call():
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/decision",
                        json={
                            "subject": {
                                "subject_id": actor_id,
                                "subject_type": actor_type,
                            },
                            "action": scope,
                            "resource": {"resource_type": "mmm_engine", "resource_id": "*"},
                            "context": {
                                "tenant_id": tenant_id,
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

            self._breaker.call(_call)
        except HTTPException:
            raise
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
        except RuntimeError as exc:
            # Circuit breaker open
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="IAM service temporarily unavailable",
            ) from exc

