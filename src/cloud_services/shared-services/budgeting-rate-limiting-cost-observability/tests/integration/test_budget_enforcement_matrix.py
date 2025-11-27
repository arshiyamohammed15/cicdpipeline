"""
Risk→Test Matrix: Budget enforcement bypass (soft limit incorrectly enforced).

Required Evidence: Regression showing hard-stop vs soft-limit vs throttle
behaviours for overlapping budgets.
"""

from __future__ import annotations

import pytest
import uuid
from decimal import Decimal

import sys
from pathlib import Path

# Add root to path for shared harness
root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from tests.shared_harness import BudgetFixtureFactory, TenantFactory
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..database.models import Base, Budget
from ..services.budget_service import BudgetService
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
    """Stub event service for testing."""
    
    def __init__(self):
        self.events = []
    
    def publish_budget_threshold_exceeded(self, *args, **kwargs) -> str:
        self.events.append({"event": "budget_threshold_exceeded", **kwargs})
        return str(uuid.uuid4())


@pytest.fixture
def budget_service(db_session):
    """Create budget service for testing."""
    return BudgetService(db_session, MockM29DataPlane(), DummyEventService())


@pytest.mark.budgeting_regression
@pytest.mark.integration
def test_hard_stop_enforcement_blocks_operations(
    budget_service: BudgetService,
    tenant_factory: TenantFactory,
    budget_factory: BudgetFixtureFactory,
) -> None:
    """Test that hard-stop enforcement blocks operations when budget exceeded."""
    tenant = tenant_factory.create()
    budget = budget_factory.create_budget(
        tenant,
        budget_amount=1000.0,
        enforcement_action="hard_stop",
    )
    
    # Create budget in service
    created = budget_service.create_budget(
        tenant_id=budget.tenant_id,
        budget_type=budget.budget_type,
        budget_amount=Decimal(str(budget.budget_amount)),
        period_type=budget.period_type,
        enforcement_action=budget.enforcement_action,
    )
    
    # Exceed budget
    budget_service.record_usage(
        tenant_id=budget.tenant_id,
        budget_id=created["budget_id"],
        amount=Decimal("1500.0"),  # Exceeds 1000.0
    )
    
    # Check budget - should be blocked
    check = budget_service.check_budget(
        tenant_id=budget.tenant_id,
        budget_id=created["budget_id"],
        requested_amount=Decimal("100.0"),
    )
    
    assert check["allowed"] is False
    assert check["enforcement_action"] == "hard_stop"


@pytest.mark.budgeting_regression
@pytest.mark.integration
def test_soft_limit_allows_operations_with_alerts(
    budget_service: BudgetService,
    tenant_factory: TenantFactory,
    budget_factory: BudgetFixtureFactory,
) -> None:
    """Test that soft-limit allows operations but sends alerts."""
    tenant = tenant_factory.create()
    budget = budget_factory.create_budget(
        tenant,
        budget_amount=1000.0,
        enforcement_action="soft_limit",
    )
    
    created = budget_service.create_budget(
        tenant_id=budget.tenant_id,
        budget_type=budget.budget_type,
        budget_amount=Decimal(str(budget.budget_amount)),
        period_type=budget.period_type,
        enforcement_action=budget.enforcement_action,
    )
    
    # Exceed budget
    budget_service.record_usage(
        tenant_id=budget.tenant_id,
        budget_id=created["budget_id"],
        amount=Decimal("1500.0"),
    )
    
    # Check budget - should be allowed but alert sent
    check = budget_service.check_budget(
        tenant_id=budget.tenant_id,
        budget_id=created["budget_id"],
        requested_amount=Decimal("100.0"),
    )
    
    assert check["allowed"] is True  # Soft limit allows
    # Verify alert was sent (check event service)
    assert len(budget_service.event_service.events) > 0


@pytest.mark.budgeting_regression
@pytest.mark.integration
def test_overlapping_budgets_most_restrictive_wins(
    budget_service: BudgetService,
    tenant_factory: TenantFactory,
    budget_factory: BudgetFixtureFactory,
) -> None:
    """Test that overlapping budgets apply most restrictive (lowest amount)."""
    tenant = tenant_factory.create()
    budgets = budget_factory.create_overlapping_budgets(tenant)
    
    # Create all budgets
    created_budgets = []
    for budget in budgets:
        created = budget_service.create_budget(
            tenant_id=budget.tenant_id,
            budget_type=budget.budget_type,
            budget_amount=Decimal(str(budget.budget_amount)),
            period_type=budget.period_type,
            enforcement_action="hard_stop",
        )
        created_budgets.append(created)
    
    # Check budget resolution - should use most restrictive (200.0 from user budget)
    resolved = budget_service.resolve_overlapping_budgets(
        tenant_id=tenant.tenant_id,
        budget_type="user",
    )
    
    # Most restrictive should be user budget (200.0)
    assert resolved is not None
    assert resolved["budget_amount"] == Decimal("200.0")

