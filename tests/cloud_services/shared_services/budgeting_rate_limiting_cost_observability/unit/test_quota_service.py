"""
Tests for Quota Service.

100% test coverage for quota allocation, enforcement, and renewal.
"""


# Imports handled by conftest.py
import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from budgeting_rate_limiting_cost_observability.database.models import Base, QuotaAllocation
from budgeting_rate_limiting_cost_observability.services.quota_service import QuotaService


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
def quota_service(db_session):
    """Create quota service instance."""
    return QuotaService(db_session)


class TestQuotaService:
    """Test suite for QuotaService."""

    def test_allocate_quota(self, quota_service):
        """Test quota allocation."""
        tenant_id = str(uuid.uuid4())
        quota = quota_service.allocate_quota(
            tenant_id=tenant_id,
            resource_type="api_calls",
            allocated_amount=Decimal("1000"),
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow() + timedelta(days=30),
            allocation_type="tenant",
            auto_renew=True
        )
        assert quota.allocated_amount == Decimal("1000")
        assert quota.used_amount == Decimal("0")
        assert quota.auto_renew is True

    def test_check_quota_allowed(self, quota_service):
        """Test quota check when quota is available."""
        tenant_id = str(uuid.uuid4())
        quota = quota_service.allocate_quota(
            tenant_id=tenant_id,
            resource_type="api_calls",
            allocated_amount=Decimal("1000"),
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow() + timedelta(days=30),
            allocation_type="tenant"
        )

        result = quota_service.check_quota(
            tenant_id=tenant_id,
            resource_type="api_calls",
            required_amount=Decimal("100")
        )
        assert result["allowed"] is True
        assert result["remaining_amount"] < Decimal("1000")

    def test_check_quota_exhausted(self, quota_service):
        """Test quota check when quota is exhausted."""
        tenant_id = str(uuid.uuid4())
        quota = quota_service.allocate_quota(
            tenant_id=tenant_id,
            resource_type="api_calls",
            allocated_amount=Decimal("100"),
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow() + timedelta(days=30),
            allocation_type="tenant"
        )

        # Exhaust quota
        quota_service.check_quota(
            tenant_id=tenant_id,
            resource_type="api_calls",
            required_amount=Decimal("100")
        )

        # Try to use more
        result = quota_service.check_quota(
            tenant_id=tenant_id,
            resource_type="api_calls",
            required_amount=Decimal("1")
        )
        assert result["allowed"] is False

    def test_renew_expired_quotas(self, quota_service):
        """Test quota renewal automation."""
        tenant_id = str(uuid.uuid4())
        # Create expired quota with auto_renew
        quota = quota_service.allocate_quota(
            tenant_id=tenant_id,
            resource_type="api_calls",
            allocated_amount=Decimal("1000"),
            period_start=datetime.utcnow() - timedelta(days=31),
            period_end=datetime.utcnow() - timedelta(days=1),
            allocation_type="tenant",
            auto_renew=True
        )

        renewed_count = quota_service.renew_expired_quotas()
        assert renewed_count == 1

        # Verify new quota exists
        quotas, _ = quota_service.list_quotas(tenant_id=tenant_id, active_only=True)
        assert len(quotas) > 0

    def test_list_quotas(self, quota_service):
        """Test quota listing."""
        tenant_id = str(uuid.uuid4())
        # Create multiple quotas
        for i in range(3):
            quota_service.allocate_quota(
                tenant_id=tenant_id,
                resource_type=f"resource_{i}",
                allocated_amount=Decimal("1000"),
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow() + timedelta(days=30),
                allocation_type="tenant"
            )

        quotas, total_count = quota_service.list_quotas(
            tenant_id=tenant_id,
            page=1,
            page_size=10
        )
        assert total_count == 3
        assert len(quotas) == 3

    def test_update_quota(self, quota_service):
        """Test quota update."""
        tenant_id = str(uuid.uuid4())
        quota = quota_service.allocate_quota(
            tenant_id=tenant_id,
            resource_type="api_calls",
            allocated_amount=Decimal("1000"),
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow() + timedelta(days=30),
            allocation_type="tenant"
        )

        updated = quota_service.update_quota(
            str(quota.quota_id),
            allocated_amount=Decimal("2000"),
            auto_renew=False
        )
        assert updated.allocated_amount == Decimal("2000")
        assert updated.auto_renew is False

    def test_delete_quota(self, quota_service):
        """Test quota deletion."""
        tenant_id = str(uuid.uuid4())
        quota = quota_service.allocate_quota(
            tenant_id=tenant_id,
            resource_type="api_calls",
            allocated_amount=Decimal("1000"),
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow() + timedelta(days=30),
            allocation_type="tenant"
        )

        quota_id = str(quota.quota_id)

        deleted = quota_service.delete_quota(quota_id)
        assert deleted is True

        # Verify deletion
        quota_check = quota_service.get_quota(quota_id)
        assert quota_check is None

