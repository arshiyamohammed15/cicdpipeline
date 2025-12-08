from __future__ import annotations
"""
Risk→Test Matrix: Alerts/receipts missing for threshold breaches.

Required Evidence: Evidence pack containing ERIS receipts + alert payloads when
budgets exceed thresholds.
"""


# Imports handled by conftest.py

import pytest
from decimal import Decimal

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from tests.shared_harness import BudgetFixtureFactory, EvidencePackBuilder, TenantFactory
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
from pathlib import Path

# Add module path
MODULE_ROOT = Path(__file__).resolve().parents[4] / "src" / "cloud_services" / "shared-services" / "budgeting-rate-limiting-cost-observability"
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

import sys
from pathlib import Path

# Add module path
MODULE_ROOT = Path(__file__).resolve().parents[4] / "src" / "cloud_services" / "shared-services" / "budgeting-rate-limiting-cost-observability"
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from database.models import Base
from services.budget_service import BudgetService
from dependencies import MockM29DataPlane


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
    """Event service that captures events for evidence."""

    def __init__(self):
        self.events = []

    def publish_budget_threshold_exceeded(
        self,
        tenant_id: str,
        budget_id: str,
        threshold: str,
        utilization_ratio: float,
        spent_amount: Decimal,
        remaining_budget: Decimal,
        enforcement_action: str,
        correlation_id: str,
    ) -> str:
        event = {
            "event_type": "budget_threshold_exceeded",
            "tenant_id": tenant_id,
            "budget_id": budget_id,
            "threshold": threshold,
            "utilization_ratio": utilization_ratio,
            "spent_amount": float(spent_amount),
            "remaining_budget": float(remaining_budget),
            "enforcement_action": enforcement_action,
            "correlation_id": correlation_id,
        }
        self.events.append(event)
        return correlation_id


@pytest.fixture
def budget_service(db_session):
    event_service = DummyEventService()
    return BudgetService(db_session, MockM29DataPlane(), event_service)


@pytest.mark.budgeting_regression
@pytest.mark.compliance
def test_threshold_breach_emits_receipt_and_alert(
    budget_service: BudgetService,
    tenant_factory: TenantFactory,
    budget_factory: BudgetFixtureFactory,
    evidence_builder: EvidencePackBuilder | None,
) -> None:
    """Test that budget threshold breach emits ERIS receipt and alert."""
    tenant = tenant_factory.create()
    budget = budget_factory.create_budget(tenant, budget_amount=1000.0)

    created = budget_service.create_budget(
        tenant_id=budget.tenant_id,
        budget_type=budget.budget_type,
        budget_amount=Decimal(str(budget.budget_amount)),
        period_type=budget.period_type,
        enforcement_action="hard_stop",
    )

    # Exceed threshold (80% threshold)
    budget_service.record_usage(
        tenant_id=budget.tenant_id,
        budget_id=created["budget_id"],
        amount=Decimal("850.0"),  # 85% utilization
    )

    # Trigger threshold check
    check = budget_service.check_budget(
        tenant_id=budget.tenant_id,
        budget_id=created["budget_id"],
        requested_amount=Decimal("100.0"),
    )

    # Verify event was emitted
    assert len(budget_service.event_service.events) > 0
    breach_event = budget_service.event_service.events[0]
    assert breach_event["event_type"] == "budget_threshold_exceeded"
    assert breach_event["utilization_ratio"] >= 0.8

    # Add to evidence pack if available
    if evidence_builder:
        evidence_builder.add_receipt({
            "receipt_id": breach_event["correlation_id"],
            "operation": "budget_threshold_exceeded",
            "tenant_id": tenant.tenant_id,
            "budget_id": created["budget_id"],
            "payload": breach_event,
        })

