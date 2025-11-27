"""
Risk→Test Matrix: Budget check latency >10ms or rate-limit >5ms.

Required Evidence: Perf harness capturing latency histograms for `/budgets/check`
and `/rate-limits/check` APIs.
"""

from __future__ import annotations

import asyncio
import time

import pytest

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from tests.shared_harness import BudgetFixtureFactory, PerfRunner, PerfScenario, RateLimitFixture, TenantFactory
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..database.models import Base
from ..services.budget_service import BudgetService
from ..services.rate_limit_service import RateLimitService
from ..dependencies import MockM29DataPlane


@pytest.fixture
def db_session():
    """Create in-memory database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class DummyEventService:
    def publish_budget_threshold_exceeded(self, *args, **kwargs) -> str:
        return "event-id"


@pytest.fixture
def budget_service(db_session):
    return BudgetService(db_session, MockM29DataPlane(), DummyEventService())


@pytest.fixture
def rate_limit_service(db_session):
    return RateLimitService(db_session, redis_client=None, data_plane=MockM29DataPlane())


@pytest.mark.budgeting_performance
@pytest.mark.performance
@pytest.mark.asyncio
async def test_budget_check_latency_under_10ms(
    budget_service: BudgetService,
    perf_runner: PerfRunner,
    tenant_factory: TenantFactory,
    budget_factory: BudgetFixtureFactory,
) -> None:
    """Test that budget check latency stays under 10ms p95."""
    tenant = tenant_factory.create()
    budget = budget_factory.create_budget(tenant, budget_amount=1000.0)
    
    created = budget_service.create_budget(
        tenant_id=budget.tenant_id,
        budget_type=budget.budget_type,
        budget_amount=1000.0,
        period_type=budget.period_type,
        enforcement_action="hard_stop",
    )
    
    async def check_budget_once() -> None:
        await asyncio.to_thread(
            budget_service.check_budget,
            tenant_id=budget.tenant_id,
            budget_id=created["budget_id"],
            requested_amount=100.0,
        )
    
    scenario = PerfScenario(
        name="budget-check",
        iterations=100,
        concurrency=10,
        coroutine_factory=check_budget_once,
        latency_budget_ms=10.0,
    )
    
    results = await perf_runner.run([scenario])
    assert results[0].p95 <= 10.0, f"Budget check p95 {results[0].p95}ms exceeds 10ms"


@pytest.mark.budgeting_performance
@pytest.mark.performance
@pytest.mark.asyncio
async def test_rate_limit_check_latency_under_5ms(
    rate_limit_service: RateLimitService,
    perf_runner: PerfRunner,
    tenant_factory: TenantFactory,
) -> None:
    """Test that rate limit check latency stays under 5ms p95."""
    tenant = tenant_factory.create()
    
    policy = rate_limit_service.create_rate_limit_policy(
        tenant_id=tenant.tenant_id,
        scope_type="tenant",
        scope_id=tenant.tenant_id,
        resource_type="api_calls",
        limit_value=100,
        time_window_seconds=60,
        algorithm="token_bucket",
    )
    
    async def check_rate_limit_once() -> None:
        await asyncio.to_thread(
            rate_limit_service.check_rate_limit,
            tenant_id=tenant.tenant_id,
            policy_id=policy["policy_id"],
            resource_type="api_calls",
            requested_units=1,
        )
    
    scenario = PerfScenario(
        name="rate-limit-check",
        iterations=100,
        concurrency=10,
        coroutine_factory=check_rate_limit_once,
        latency_budget_ms=5.0,
    )
    
    results = await perf_runner.run([scenario])
    assert results[0].p95 <= 5.0, f"Rate limit check p95 {results[0].p95}ms exceeds 5ms"

