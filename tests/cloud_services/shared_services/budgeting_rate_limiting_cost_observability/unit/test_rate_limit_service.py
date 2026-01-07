"""
Tests for RateLimitService covering advanced algorithms and dynamic adjustments.
"""


# Imports handled by conftest.py
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from budgeting_rate_limiting_cost_observability.database.models import Base, RateLimitUsage
from budgeting_rate_limiting_cost_observability.services.rate_limit_service import RateLimitService
from budgeting_rate_limiting_cost_observability.dependencies import MockM29DataPlane


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


@pytest.fixture
def rate_limit_service(db_session):
    """Create rate limit service instance with mock data plane."""
    return RateLimitService(db_session, redis_client=None, data_plane=MockM29DataPlane())


def create_policy(service, tenant_id, algorithm, overrides=None, burst_capacity=None, limit_value=10, window_seconds=10):
    return service.create_rate_limit_policy(
        tenant_id=tenant_id,
        scope_type="tenant",
        scope_id=str(uuid.uuid4()),
        resource_type="api_calls",
        limit_value=limit_value,
        time_window_seconds=window_seconds,
        algorithm=algorithm,
        burst_capacity=burst_capacity,
        overrides=overrides or {}
    )


@pytest.mark.unit
class TestRateLimitService:
    """Test suite for RateLimitService."""

    @staticmethod
    def _resource_key(tenant_id: str) -> str:
        return f"{tenant_id}:api_calls"

    @pytest.mark.budgeting_regression
    @pytest.mark.unit
    def test_leaky_bucket_blocks_when_queue_full(self, rate_limit_service):
        tenant_id = str(uuid.uuid4())
        policy = create_policy(rate_limit_service, tenant_id, "leaky_bucket", limit_value=5, window_seconds=5)

        assert rate_limit_service.check_rate_limit(
            tenant_id=tenant_id,
            resource_type="api_calls",
            request_count=5
        )["allowed"] is True

        assert rate_limit_service.check_rate_limit(
            tenant_id=tenant_id,
            resource_type="api_calls",
            request_count=1
        )["allowed"] is False

        state_key = f"leaky:{policy.policy_id}:{self._resource_key(tenant_id)}"
        state = rate_limit_service.data_plane.cache_get(state_key)
        assert state is not None
        state["last_ts"] -= 10
        rate_limit_service.data_plane.cache_set(state_key, state, ttl_seconds=policy.time_window_seconds)

        assert rate_limit_service.check_rate_limit(
            tenant_id=tenant_id,
            resource_type="api_calls",
            request_count=1
        )["allowed"] is True

    @pytest.mark.unit
    def test_sliding_window_enforces_limit(self, rate_limit_service):
        tenant_id = str(uuid.uuid4())
        policy = create_policy(rate_limit_service, tenant_id, "sliding_window_log", limit_value=3, window_seconds=60)

        for _ in range(3):
            assert rate_limit_service.check_rate_limit(
                tenant_id=tenant_id,
                resource_type="api_calls",
                request_count=1
            )["allowed"] is True

        assert rate_limit_service.check_rate_limit(
            tenant_id=tenant_id,
            resource_type="api_calls",
            request_count=1
        )["allowed"] is False

        state_key = f"sliding:{policy.policy_id}:{self._resource_key(tenant_id)}"
        entries = rate_limit_service.data_plane.cache_get(state_key)
        assert entries is not None
        for entry in entries:
            entry["ts"] -= 120
        rate_limit_service.data_plane.cache_set(state_key, entries, ttl_seconds=policy.time_window_seconds)

        assert rate_limit_service.check_rate_limit(
            tenant_id=tenant_id,
            resource_type="api_calls",
            request_count=1
        )["allowed"] is True

    @pytest.mark.unit
    def test_usage_pattern_adjustment_scales_down_limit(self, rate_limit_service, db_session):
        tenant_id = str(uuid.uuid4())
        overrides = {
            "usage_pattern_analysis": {
                "window_seconds": 60,
                "high_utilization_threshold": 0.5,
                "scale_down_multiplier": 0.5
            }
        }
        policy = create_policy(
            rate_limit_service,
            tenant_id,
            "fixed_window",
            overrides=overrides,
            limit_value=10,
            window_seconds=60
        )

        now = datetime.utcnow()
        usage = RateLimitUsage(
            usage_id=uuid.uuid4(),
            policy_id=policy.policy_id,
            tenant_id=uuid.UUID(tenant_id),
            resource_key=self._resource_key(tenant_id),
            window_start=now - timedelta(seconds=30),
            window_end=now + timedelta(seconds=30),
            current_count=10,
            last_request_at=now
        )
        db_session.add(usage)
        db_session.commit()

        rate_limit_service._now = lambda: now  # type: ignore

        result = rate_limit_service.check_rate_limit(
            tenant_id=tenant_id,
            resource_type="api_calls",
            request_count=6
        )

        assert result["allowed"] is False
        assert result["limit_value"] == 5

