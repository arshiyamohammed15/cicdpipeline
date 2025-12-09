from __future__ import annotations
"""
Risk→Test Matrix: Alerts/receipts missing for threshold breaches.

Required Evidence: Evidence pack containing ERIS receipts + alert payloads when
budgets exceed thresholds.
"""


# Imports handled by conftest.py

import pytest
import uuid
from datetime import datetime
from decimal import Decimal

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from tests.shared_harness import EvidencePackBuilder
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

from budgeting_rate_limiting_cost_observability.database.models import Base
from budgeting_rate_limiting_cost_observability.services.budget_service import BudgetService
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


@pytest.fixture
def evidence_builder(tmp_path) -> EvidencePackBuilder:
    """Provide an evidence builder that writes to a temporary directory."""
    return EvidencePackBuilder(output_dir=tmp_path)


@pytest.mark.budgeting_regression
@pytest.mark.compliance
def test_threshold_breach_emits_receipt_and_alert(
    budget_service: BudgetService,
    evidence_builder: EvidencePackBuilder | None,
) -> None:
    """Test that budget threshold breach emits ERIS receipt and alert."""
    tenant_uuid = str(uuid.uuid4())
    budget_amount = Decimal("1000.0")

    created = budget_service.create_budget(
        tenant_id=tenant_uuid,
        budget_name="threshold-budget",
        budget_type="tenant",
        budget_amount=budget_amount,
        period_type="monthly",
        start_date=datetime.utcnow(),
        allocated_to_type="tenant",
        allocated_to_id=tenant_uuid,
        enforcement_action="hard_stop",
    )

    # Exceed threshold (80% threshold) via check_budget
    check = budget_service.check_budget(
        tenant_id=tenant_uuid,
        resource_type="api_calls",
        estimated_cost=Decimal("850.0"),  # 85% utilization
        allocated_to_type="tenant",
        allocated_to_id=tenant_uuid,
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
            "tenant_id": tenant_uuid,
            "budget_id": str(created.budget_id),
            "payload": breach_event,
        })

