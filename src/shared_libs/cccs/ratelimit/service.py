"""Rate Limiter & Budget Guard (RLBGS) implementation."""

from __future__ import annotations

import asyncio
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from ..adapters.epc13_adapter import EPC13AdapterConfig, EPC13BudgetAdapter
from ..exceptions import BudgetExceededError
from ..types import BudgetDecision


@dataclass
class RateLimiterConfig:
    """Configuration for rate limiter."""

    epc13_base_url: str
    epc13_timeout_seconds: float = 5.0
    epc13_api_version: str = "v1"
    default_deny_on_unavailable: bool = True
    on_budget_exceeded: Callable[[str, float], None] = lambda action, cost: None


class RateLimiterService:
    """
    Token-bucket guard that honours the zero synchronous network-call requirement.

    Request-path checks read from cached state, while EPC-13 refreshes are queued into the WAL.
    """

    def __init__(self, config: RateLimiterConfig, wal: Optional[Any] = None):
        self._config = config
        adapter_config = EPC13AdapterConfig(
            base_url=config.epc13_base_url,
            timeout_seconds=config.epc13_timeout_seconds,
            api_version=config.epc13_api_version,
            default_deny_on_unavailable=config.default_deny_on_unavailable,
        )
        self._adapter = EPC13BudgetAdapter(adapter_config)
        self._wal = wal
        self._budget_cache: Dict[str, float] = {}

    async def _check_budget_async(
        self, action_id: str, cost: float, tenant_id: Optional[str] = None
    ) -> BudgetDecision:
        return await self._adapter.check_budget(action_id, cost, tenant_id)

    def check_budget(
        self, action_id: str, cost: float, tenant_id: Optional[str] = None, use_cache: bool = True
    ) -> BudgetDecision:
        """Checks cached budget; queues EPC-13 refresh when data is stale."""
        if action_id in self._budget_cache:
            remaining = self._budget_cache[action_id]
            if cost > remaining:
                self._config.on_budget_exceeded(action_id, cost)
                raise BudgetExceededError(f"Budget exceeded for {action_id}: {cost} > {remaining}")
            self._budget_cache[action_id] = remaining - cost
            return BudgetDecision(allowed=True, reason="budget_available_cached", remaining=self._budget_cache[action_id])

        if use_cache:
            self._queue_epc13_call(action_id, cost, tenant_id)
            if self._config.default_deny_on_unavailable:
                self._config.on_budget_exceeded(action_id, cost)
                raise BudgetExceededError("Budget unavailable; queued EPC-13 refresh")
            raise BudgetExceededError("Budget check queued for EPC-13 refresh")

        return self._fetch_and_cache(action_id, cost, tenant_id)

    def _fetch_and_cache(self, action_id: str, cost: float, tenant_id: Optional[str]) -> BudgetDecision:
        loop = asyncio.new_event_loop()
        try:
            decision = loop.run_until_complete(self._check_budget_async(action_id, cost, tenant_id))
        except BudgetExceededError:
            self._config.on_budget_exceeded(action_id, cost)
            raise
        finally:
            loop.close()
        if decision.allowed:
            self._budget_cache[action_id] = decision.remaining
        return decision

    def _queue_epc13_call(self, action_id: str, cost: float, tenant_id: Optional[str]) -> None:
        if not self._wal:
            return
        self._wal.append(
            {
                "type": "epc13_call",
                "action": "check_budget",
                "action_id": action_id,
                "cost": cost,
                "tenant_id": tenant_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            entry_type="epc13_call",
        )

    def process_wal_entry(self, payload: dict) -> None:
        """Refreshes cached budgets when the WAL drain runs."""
        action_id = payload.get("action_id")
        cost = payload.get("cost", 0.0)
        tenant_id = payload.get("tenant_id")
        if not action_id:
            return

        try:
            decision = self._fetch_and_cache(action_id, cost, tenant_id)
            if decision.allowed:
                self._budget_cache[action_id] = decision.remaining
        except Exception:
            if self._config.default_deny_on_unavailable:
                self._budget_cache.pop(action_id, None)

    async def health_check(self) -> bool:
        return await self._adapter.health_check()

    async def close(self) -> None:
        await self._adapter.close()

    async def persist_budget_snapshot(
        self, budget_data: Dict, tenant_id: Optional[str] = None
    ) -> str:
        budget_data_copy = copy.deepcopy(budget_data)
        return await self._adapter.persist_budget_snapshot(budget_data_copy, tenant_id)
