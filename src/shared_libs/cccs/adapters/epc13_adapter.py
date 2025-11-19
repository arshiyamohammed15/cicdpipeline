"""
EPC-13 (Budgeting, Rate-Limiting & Cost Observability) façade adapter.

Calls EPC-13 service endpoints for budget checks and rate limiting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from ..exceptions import BudgetExceededError
from ..types import BudgetDecision

logger = logging.getLogger(__name__)


@dataclass
class EPC13AdapterConfig:
    """Configuration for EPC-13 adapter."""

    base_url: str
    timeout_seconds: float = 5.0
    api_version: str = "v1"
    default_deny_on_unavailable: bool = True


class EPC13BudgetAdapter:
    """
    Façade adapter for EPC-13 Budgeting, Rate-Limiting & Cost Observability service.

    Calls budget check and rate limit endpoints per EPC-13 PRD.
    """

    def __init__(self, config: EPC13AdapterConfig):
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            headers={"Content-Type": "application/json"},
        )

    async def check_budget(
        self, action_id: str, cost: float, tenant_id: Optional[str] = None
    ) -> BudgetDecision:
        """
        Check budget via EPC-13 service.

        Args:
            action_id: Action identifier
            cost: Cost of the action
            tenant_id: Optional tenant identifier

        Returns:
            BudgetDecision with allowed, reason, remaining

        Raises:
            BudgetExceededError: If budget exceeded
        """
        try:
            payload = {
                "action_id": action_id,
                "cost": cost,
            }
            if tenant_id:
                payload["tenant_id"] = tenant_id

            response = await self._client.post(
                f"/budget/{self._config.api_version}/check",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            allowed = result.get("allowed", False)
            if not allowed:
                raise BudgetExceededError(
                    f"Budget exceeded for {action_id}: {result.get('reason', 'unknown')}"
                )

            return BudgetDecision(
                allowed=True,
                reason=result.get("reason", "budget_available"),
                remaining=result.get("remaining", 0.0),
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 or e.response.status_code == 403:
                logger.warning(f"EPC-13 budget check denied: {e.response.status_code}")
                raise BudgetExceededError(f"Budget exceeded: {e.response.text}") from e
            logger.error(f"EPC-13 budget check failed: {e.response.status_code} - {e.response.text}")
            if self._config.default_deny_on_unavailable:
                raise BudgetExceededError("EPC-13 unavailable, denying by default") from e
            raise BudgetExceededError(f"Budget check failed: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"EPC-13 request failed: {e}")
            if self._config.default_deny_on_unavailable:
                raise BudgetExceededError("EPC-13 unavailable, denying by default") from e
            raise BudgetExceededError("EPC-13 service unavailable") from e

    async def check_rate_limit(
        self,
        policy_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check rate limit via EPC-13 service.

        Args:
            policy_id: Rate limit policy identifier
            tenant_id: Optional tenant identifier
            user_id: Optional user identifier

        Returns:
            Rate limit check result with allowed, remaining, limit

        Raises:
            BudgetExceededError: If rate limit exceeded
        """
        try:
            payload = {"policy_id": policy_id}
            if tenant_id:
                payload["tenant_id"] = tenant_id
            if user_id:
                payload["user_id"] = user_id

            response = await self._client.post(
                f"/rate-limit/{self._config.api_version}/check",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"EPC-13 rate limit exceeded: {e.response.status_code}")
                raise BudgetExceededError(f"Rate limit exceeded: {e.response.text}") from e
            logger.error(f"EPC-13 rate limit check failed: {e.response.status_code}")
            if self._config.default_deny_on_unavailable:
                raise BudgetExceededError("EPC-13 unavailable, denying by default") from e
            raise BudgetExceededError(f"Rate limit check failed: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"EPC-13 request failed: {e}")
            if self._config.default_deny_on_unavailable:
                raise BudgetExceededError("EPC-13 unavailable, denying by default") from e
            raise BudgetExceededError("EPC-13 service unavailable") from e

    async def persist_budget_snapshot(
        self, budget_data: Dict[str, Any], tenant_id: Optional[str] = None
    ) -> str:
        """
        Persist budget snapshot to EPC-13 for audit.

        Args:
            budget_data: Budget snapshot data
            tenant_id: Optional tenant identifier

        Returns:
            Snapshot ID
        """
        try:
            payload = {"budget_data": budget_data}
            if tenant_id:
                payload["tenant_id"] = tenant_id

            response = await self._client.post(
                f"/budget/{self._config.api_version}/snapshot",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("snapshot_id", "")
        except httpx.RequestError as e:
            logger.error(f"EPC-13 budget snapshot failed: {e}")
            raise BudgetExceededError("Failed to persist budget snapshot") from e

    async def health_check(self) -> bool:
        """
        Check EPC-13 service health.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self._client.get(f"/budget/{self._config.api_version}/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()

