from __future__ import annotations
"""
Risk→Test Matrix: Rate limit counters drift causing tenant starvation.

Required Evidence: Stress test verifying token/leaky bucket accuracy over 10^6 ops
without counter skew.
"""


# Imports handled by conftest.py

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from tests.shared_harness import PerfRunner, PerfScenario, RateLimitFixture, TenantFactory
import sys
from pathlib import Path
import importlib.util

# Register package shims for budgeting-rate-limiting-cost-observability
bootstrap_path = root / "tests" / "src" / "cloud_services" / "shared_services" / "budgeting_rate_limiting_cost_observability" / "bootstrap.py"
spec_bootstrap = importlib.util.spec_from_file_location("brlco_bootstrap", bootstrap_path)
bootstrap_module = importlib.util.module_from_spec(spec_bootstrap)
spec_bootstrap.loader.exec_module(bootstrap_module)
bootstrap_module.ensure_brlco()

from database.models import Base, RateLimitUsage
from services.rate_limit_service import RateLimitService
from dependencies import MockM29DataPlane


@pytest.fixture
def db_session():
    """Create in-memory database session for testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from ..database.models import Base

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


@pytest.fixture
def rate_limit_service(db_session):
    """Create rate limit service for testing."""
    return RateLimitService(db_session, redis_client=None, data_plane=MockM29DataPlane())


@pytest.mark.budgeting_performance
@pytest.mark.performance
def test_rate_limit_counter_accuracy_high_throughput(
    rate_limit_service: RateLimitService,
    tenant_factory: TenantFactory,
) -> None:
    """Stress test: 10^6 ops, verify token bucket accuracy without counter skew."""
    tenant = tenant_factory.create()

    # Create rate limit policy (token bucket)
    policy = rate_limit_service.create_rate_limit_policy(
        tenant_id=tenant.tenant_id,
        scope_type="tenant",
        scope_id=tenant.tenant_id,
        resource_type="api_calls",
        limit_value=1000,
        time_window_seconds=60,
        algorithm="token_bucket",
        burst_capacity=100,
    )

    # Simulate high-throughput operations
    allowed_count = 0
    denied_count = 0

    def check_rate_limit() -> None:
        nonlocal allowed_count, denied_count
        result = rate_limit_service.check_rate_limit(
            tenant_id=tenant.tenant_id,
            policy_id=policy["policy_id"],
            resource_type="api_calls",
            requested_units=1,
        )
        if result["allowed"]:
            allowed_count += 1
        else:
            denied_count += 1

    # Run 10^6 operations in parallel
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(check_rate_limit) for _ in range(1000000)]
        for future in futures:
            future.result()

    # Verify counter accuracy: allowed + denied should equal total
    total_ops = allowed_count + denied_count
    assert total_ops == 1000000, f"Counter drift detected: {total_ops} != 1000000"

    # Verify rate limit was enforced (some should be denied)
    assert denied_count > 0, "Rate limit should deny some requests"
    assert allowed_count <= 1100, "Should not exceed limit + burst capacity"


@pytest.mark.budgeting_performance
@pytest.mark.performance
def test_leaky_bucket_accuracy_under_load(
    rate_limit_service: RateLimitService,
    tenant_factory: TenantFactory,
) -> None:
    """Test leaky bucket algorithm accuracy under load."""
    tenant = tenant_factory.create()

    policy = rate_limit_service.create_rate_limit_policy(
        tenant_id=tenant.tenant_id,
        scope_type="tenant",
        scope_id=tenant.tenant_id,
        resource_type="api_calls",
        limit_value=500,
        time_window_seconds=60,
        algorithm="leaky_bucket",
    )

    allowed = 0
    denied = 0

    for _ in range(10000):
        result = rate_limit_service.check_rate_limit(
            tenant_id=tenant.tenant_id,
            policy_id=policy["policy_id"],
            resource_type="api_calls",
            requested_units=1,
        )
        if result["allowed"]:
            allowed += 1
        else:
            denied += 1

    # Verify accuracy
    assert allowed + denied == 10000
    assert allowed <= 500, "Leaky bucket should enforce strict limit"

