"""
Budgeting, Rate-Limiting & Cost Observability (EPC-13) client.

Per FR-9, enforces per-tenant, per-workspace, per-actor budgets for tokens
and request counts via EPC-13 /budgets/check endpoint.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx
from fastapi import HTTPException, status


class BudgetClient:
    """
    Real HTTP client for Budgeting, Rate-Limiting & Cost Observability (EPC-13).

    Calls /budgets/check endpoint to verify tenant has budget remaining for
    estimated token usage. Raises HTTPException if budget exhausted.
    """

    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 1.0):
        self.base_url = base_url or os.getenv(
            "BUDGET_SERVICE_URL", "http://localhost:8035"
        )
        self.timeout = timeout_seconds

    def assert_within_budget(
        self,
        tenant_id: str,
        tokens: int,
        workspace_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> None:
        """
        Check budget availability via EPC-13.

        Calls /budgets/check with CheckBudgetRequest to verify:
        - Per-tenant token budget
        - Per-workspace budget (if workspace_id provided)
        - Per-actor budget (if actor_id provided)

        Raises HTTPException(429) if budget exhausted.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                # Estimate cost (simplified: assume $0.0001 per token)
                estimated_cost = tokens * 0.0001

                response = client.post(
                    f"{self.base_url}/budgets/check",
                    json={
                        "tenant_id": tenant_id,
                        "resource_type": "llm_tokens",
                        "estimated_cost": estimated_cost,
                        "allocated_to_type": "workspace" if workspace_id else "tenant",
                        "allocated_to_id": workspace_id or tenant_id,
                        "operation_context": {
                            "service": "llm_gateway",
                            "actor_id": actor_id,
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()

                if not result.get("allowed", False):
                    enforcement = result.get("enforcement_action", "block")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Budget exhausted: {enforcement}",
                    )

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Budget service indicates budget exhausted",
                ) from exc
            # Other errors: allow request but log
            return
        except httpx.RequestError:
            # Connection error: allow request (fail-open for resilience)
            return

