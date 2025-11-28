"""
LLM Gateway client for MMM Engine.

Per PRD Section 12.5, calls LLM Gateway & Safety Enforcement module for
Mentor/Multiplier content generation with safety pipeline integration.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from ..reliability.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class LLMGatewayClient:
    """HTTP client for LLM Gateway & Safety Enforcement (PM-6)."""

    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 3.0):
        self.base_url = base_url or os.getenv(
            "LLM_GATEWAY_SERVICE_URL", "http://localhost:8006"
        )
        self.timeout = timeout_seconds
        self._breaker = CircuitBreaker(
            name="llm_gateway_client", failure_threshold=5, recovery_timeout=60.0
        )

    async def generate(
        self,
        prompt: str,
        tenant_id: str,
        actor_id: str,
        actor_type: str,
        operation_type: str = "chat",
        system_prompt_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate content via LLM Gateway with safety pipeline.

        Per PRD Section FR-5:
        - Calls LLM Gateway /v1/llm/generate (or /api/v1/llm/chat) endpoint
        - Returns content with safety metadata
        - Raises exception if safety check fails

        Args:
            prompt: User prompt for LLM generation
            tenant_id: Tenant identifier
            actor_id: Actor identifier
            actor_type: Actor type (human/ai_agent)
            operation_type: Operation type (chat/completion)
            system_prompt_id: System prompt identifier from tenant policy
            dry_run: Whether this is a dry run

        Returns:
            Dict with:
                - content: Generated content
                - safety: Safety metadata (status, risk_flags, redaction_summary)
                - response_id: Response identifier
                - receipt_id: Receipt identifier

        Raises:
            RuntimeError: If LLM Gateway unavailable or safety check fails
        """
        request_id = f"mmm-{uuid.uuid4().hex[:16]}"
        system_prompt_id = system_prompt_id or "default-system-prompt"

        # Build LLM Gateway request payload
        request_payload = {
            "request_id": request_id,
            "schema_version": "v1",
            "actor": {
                "actor_id": actor_id,
                "actor_type": actor_type,
                "roles": [],
                "capabilities": [],
                "scopes": [],
                "session_assurance_level": "medium",
            },
            "tenant": {
                "tenant_id": tenant_id,
            },
            "logical_model_id": "default_chat",
            "operation_type": operation_type,
            "sensitivity_level": "medium",
            "system_prompt_id": system_prompt_id,
            "user_prompt": prompt,
            "context_segments": [],
            "policy_snapshot_id": f"{tenant_id}-snapshot-default",
            "policy_version_ids": [f"pol-{tenant_id[:4]}-v1"],
            "budget": {
                "max_tokens": 2048,
                "max_cost_usd": 0.10,
            },
            "safety_overrides": {},
            "dry_run": dry_run,
        }

        async def _call() -> Dict[str, Any]:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Try /v1/llm/generate first, fallback to /api/v1/llm/chat
                endpoints = [
                    f"{self.base_url}/v1/llm/generate",
                    f"{self.base_url}/api/v1/llm/chat",
                ]
                last_exc = None

                for endpoint in endpoints:
                    try:
                        response = await client.post(
                            endpoint,
                            json=request_payload,
                            headers={"Content-Type": "application/json"},
                        )
                        response.raise_for_status()
                        data = response.json()

                        # Extract content and safety metadata
                        output = data.get("output", {})
                        content = output.get("content") if output else None

                        # Build safety object from response
                        safety_status = "pass"
                        if data.get("decision", {}).get("status") == "BLOCK":
                            safety_status = "fail"
                        elif data.get("risk_flags"):
                            safety_status = "warn"

                        safety = {
                            "status": safety_status,
                            "risk_flags": [
                                {
                                    "risk_class": rf.get("risk_class", "unknown"),
                                    "severity": rf.get("severity", "low"),
                                }
                                for rf in data.get("risk_flags", [])
                            ],
                            "redaction_summary": output.get("redacted_output_summary")
                            if output
                            else None,
                        }

                        # If safety check failed, raise exception
                        if safety_status == "fail":
                            raise RuntimeError(
                                f"LLM Gateway safety check failed: {data.get('decision', {}).get('reasons', [])}"
                            )

                        return {
                            "content": content or "",
                            "safety": safety,
                            "response_id": data.get("response_id", request_id),
                            "receipt_id": data.get("receipt_id", ""),
                        }
                    except httpx.HTTPStatusError as exc:
                        last_exc = exc
                        if exc.response.status_code == 404:
                            # Try next endpoint
                            continue
                        # For other errors, raise immediately
                        raise
                    except httpx.RequestError as exc:
                        last_exc = exc
                        # Try next endpoint
                        continue

                # If all endpoints failed
                if last_exc:
                    raise last_exc
                raise RuntimeError("No LLM Gateway endpoints available")

        try:
            return await self._breaker.call_async(_call)
        except RuntimeError as exc:
            # Circuit breaker open or safety check failed
            if "safety check failed" in str(exc):
                raise
            logger.warning("LLM Gateway circuit breaker open: %s", exc)
            raise RuntimeError("LLM Gateway temporarily unavailable") from exc
        except httpx.HTTPStatusError as exc:
            logger.error("LLM Gateway HTTP error: %s", exc)
            raise RuntimeError(f"LLM Gateway error: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error("LLM Gateway connection error: %s", exc)
            raise RuntimeError(f"LLM Gateway connection failed: {exc}") from exc
        except Exception as exc:
            logger.exception("Unexpected LLM Gateway error: %s", exc)
            raise RuntimeError(f"LLM Gateway error: {exc}") from exc

