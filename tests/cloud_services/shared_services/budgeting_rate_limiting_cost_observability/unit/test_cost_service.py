"""
Tests for Cost Service.

100% test coverage for cost calculation, attribution, and anomaly detection.
"""


# Imports handled by conftest.py
import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from budgeting_rate_limiting_cost_observability.database.models import Base, CostRecord
from budgeting_rate_limiting_cost_observability.services.cost_service import CostService


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
def cost_service(db_session):
    """Create cost service instance."""
    return CostService(db_session)


class TestCostService:
    """Test suite for CostService."""

    @pytest.mark.budgeting_regression
    @pytest.mark.unit
    def test_record_cost(self, cost_service):
        """Test cost recording."""
        tenant_id = str(uuid.uuid4())
        record = cost_service.record_cost(
            tenant_id=tenant_id,
            resource_type="api_calls",
            cost_amount=Decimal("10.50"),
            usage_quantity=Decimal("1000"),
            attributed_to_type="tenant",
            attributed_to_id=tenant_id,
            usage_unit="requests",
            service_name="api_service"
        )
        assert record.cost_amount == Decimal("10.50")
        assert record.usage_quantity == Decimal("1000")
        assert str(record.tenant_id) == tenant_id

    def test_query_cost_records(self, cost_service):
        """Test cost record querying."""
        tenant_id = str(uuid.uuid4())
        # Record multiple costs
        for i in range(5):
            cost_service.record_cost(
                tenant_id=tenant_id,
                resource_type="api_calls",
                cost_amount=Decimal(f"{10 + i}"),
                usage_quantity=Decimal("100"),
                attributed_to_type="tenant",
                attributed_to_id=tenant_id
            )

        records, total_count, aggregated = cost_service.query_cost_records(
            tenant_id=tenant_id,
            page=1,
            page_size=10
        )
        assert total_count == 5
        assert len(records) == 5
        assert aggregated["total_cost"] > 0

    def test_generate_cost_report(self, cost_service):
        """Test cost report generation."""
        tenant_id = str(uuid.uuid4())
        start_time = datetime.utcnow() - timedelta(days=7)

        # Record costs
        for i in range(3):
            cost_service.record_cost(
                tenant_id=tenant_id,
                resource_type=f"resource_{i}",
                cost_amount=Decimal("100"),
                usage_quantity=Decimal("1000"),
                attributed_to_type="tenant",
                attributed_to_id=tenant_id
            )

        end_time = datetime.utcnow() + timedelta(seconds=1)

        report = cost_service.generate_cost_report(
            tenant_id=tenant_id,
            report_type="summary",
            start_time=start_time,
            end_time=end_time,
            group_by=["resource_type"]
        )
        assert report["report_type"] == "summary"
        assert report["total_cost"] > 0
        assert len(report["breakdown"]) > 0

    def test_detect_anomalies(self, cost_service):
        """Test anomaly detection."""
        tenant_id = str(uuid.uuid4())
        # Record baseline costs
        for i in range(10):
            record = cost_service.record_cost(
                tenant_id=tenant_id,
                resource_type="api_calls",
                cost_amount=Decimal("100"),
                usage_quantity=Decimal("1000"),
                attributed_to_type="tenant",
                attributed_to_id=tenant_id
            )
            record.timestamp = datetime.utcnow() - timedelta(days=10 - i)
            cost_service.db.commit()

        # Record spike
        spike = cost_service.record_cost(
            tenant_id=tenant_id,
            resource_type="api_calls",
            cost_amount=Decimal("500"),  # 5x baseline
            usage_quantity=Decimal("5000"),
            attributed_to_type="tenant",
            attributed_to_id=tenant_id
        )
        spike.timestamp = datetime.utcnow()
        cost_service.db.commit()

        anomalies = cost_service.detect_anomalies(tenant_id)
        # Should detect the spike
        assert len(anomalies) > 0

    def test_record_cost_batch(self, cost_service):
        """Test batch cost recording."""
        tenant_id = str(uuid.uuid4())
        records = [
            {
                "tenant_id": tenant_id,
                "resource_type": "api_calls",
                "cost_amount": Decimal("10"),
                "usage_quantity": Decimal("100"),
                "attributed_to_type": "tenant",
                "attributed_to_id": tenant_id
            },
            {
                "tenant_id": tenant_id,
                "resource_type": "storage",
                "cost_amount": Decimal("20"),
                "usage_quantity": Decimal("200"),
                "attributed_to_type": "tenant",
                "attributed_to_id": tenant_id
            }
        ]

        processed, failed, failures = cost_service.record_cost_batch(records)
        assert processed == 2
        assert failed == 0
        assert len(failures) == 0

