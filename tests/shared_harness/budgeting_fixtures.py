from __future__ import annotations
"""
Budgeting-specific fixtures for test harness.
"""


from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
from uuid import uuid4

from .tenants import TenantProfile


@dataclass
class BudgetFixture:
    """Synthetic budget configuration for testing."""

    budget_id: str
    tenant_id: str
    budget_type: str  # tenant/project/user/feature
    budget_amount: float
    period_type: str  # monthly_rolling/quarterly_fixed/project_duration/custom
    enforcement_action: str  # hard_stop/soft_limit/throttle/escalate
    start_date: datetime
    end_date: datetime | None = None


@dataclass
class RateLimitFixture:
    """Synthetic rate limit configuration for testing."""

    limit_id: str
    tenant_id: str
    limit_dimension: str  # api_calls_per_second/compute_minutes_per_hour
    limit_value: int
    time_window_seconds: int
    algorithm: str  # token_bucket/leaky_bucket/fixed_window/sliding_window_log


class BudgetFixtureFactory:
    """Generates budget and rate limit fixtures for testing."""

    def create_budget(
        self,
        tenant: TenantProfile,
        *,
        budget_type: str = "tenant",
        budget_amount: float = 1000.0,
        period_type: str = "monthly_rolling",
        enforcement_action: str = "hard_stop",
    ) -> BudgetFixture:
        return BudgetFixture(
            budget_id=f"budget-{uuid4().hex[:8]}",
            tenant_id=tenant.tenant_id,
            budget_type=budget_type,
            budget_amount=budget_amount,
            period_type=period_type,
            enforcement_action=enforcement_action,
            start_date=datetime.utcnow(),
        )

    def create_overlapping_budgets(
        self, tenant: TenantProfile
    ) -> List[BudgetFixture]:
        """Create overlapping budgets to test priority resolution (most restrictive wins)."""
        return [
            self.create_budget(tenant, budget_type="tenant", budget_amount=1000.0),
            self.create_budget(tenant, budget_type="project", budget_amount=500.0),
            self.create_budget(tenant, budget_type="user", budget_amount=200.0),
        ]

    def create_rate_limit(
        self,
        tenant: TenantProfile,
        *,
        limit_dimension: str = "api_calls_per_second",
        limit_value: int = 100,
        time_window_seconds: int = 60,
        algorithm: str = "token_bucket",
    ) -> RateLimitFixture:
        return RateLimitFixture(
            limit_id=f"limit-{uuid4().hex[:8]}",
            tenant_id=tenant.tenant_id,
            limit_dimension=limit_dimension,
            limit_value=limit_value,
            time_window_seconds=time_window_seconds,
            algorithm=algorithm,
        )

