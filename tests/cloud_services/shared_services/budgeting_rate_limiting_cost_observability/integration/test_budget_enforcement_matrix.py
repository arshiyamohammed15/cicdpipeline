from __future__ import annotations
"""
Risk→Test Matrix: Budget enforcement bypass (soft limit incorrectly enforced).

Required Evidence: Regression showing hard-stop vs soft-limit vs throttle
behaviours for overlapping budgets.
"""


# Imports handled by conftest.py

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

import importlib.util

# Load bootstrap to register package shims for budgeting-rate-limiting-cost-observability
bootstrap_path = root / "tests" / "src" / "cloud_services" / "shared_services" / "budgeting_rate_limiting_cost_observability" / "bootstrap.py"
spec_bootstrap = importlib.util.spec_from_file_location("brlco_bootstrap", bootstrap_path)
bootstrap_module = importlib.util.module_from_spec(spec_bootstrap)
spec_bootstrap.loader.exec_module(bootstrap_module)
bootstrap_module.ensure_brlco()

from database.models import Base, BudgetDefinition as Budget
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


# Lightweight factory fixtures (the shared harness provides classes, not pytest fixtures)
@pytest.fixture
def tenant_factory() -> TenantFactory:
    return TenantFactory()


@pytest.fixture
def budget_factory() -> BudgetFixtureFactory:
    return BudgetFixtureFactory()


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
    # Use UUID-backed identifiers expected by BudgetService
    tenant_uuid = uuid.uuid4()
    budget.tenant_id = str(tenant_uuid)
    allocated_to_id = str(tenant_uuid)

    # Create budget in service
    created = budget_service.create_budget(
        tenant_id=budget.tenant_id,
        budget_name=f"{budget.budget_type}-budget",
        budget_type=budget.budget_type,
        budget_amount=Decimal(str(budget.budget_amount)),
        period_type=budget.period_type,
        start_date=budget.start_date,
        allocated_to_type=budget.budget_type,
        allocated_to_id=allocated_to_id,
        enforcement_action=budget.enforcement_action,
    )

    # Check budget with a request that exceeds the total amount
    check = budget_service.check_budget(
        tenant_id=budget.tenant_id,
        resource_type=budget.budget_type,
        estimated_cost=Decimal("1500.0"),  # Exceeds 1000.0
        allocated_to_type=budget.budget_type,
        allocated_to_id=allocated_to_id,
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
    # Use UUID-backed identifiers expected by BudgetService
    tenant_uuid = uuid.uuid4()
    budget.tenant_id = str(tenant_uuid)
    allocated_to_id = str(tenant_uuid)

    created = budget_service.create_budget(
        tenant_id=budget.tenant_id,
        budget_name=f"{budget.budget_type}-budget",
        budget_type=budget.budget_type,
        budget_amount=Decimal(str(budget.budget_amount)),
        period_type=budget.period_type,
        start_date=budget.start_date,
        allocated_to_type=budget.budget_type,
        allocated_to_id=allocated_to_id,
        enforcement_action=budget.enforcement_action,
    )

    # Exceed budget - soft limit should allow but emit alert
    check = budget_service.check_budget(
        tenant_id=budget.tenant_id,
        resource_type=budget.budget_type,
        estimated_cost=Decimal("1500.0"),
        allocated_to_type=budget.budget_type,
        allocated_to_id=allocated_to_id,
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
    tenant_uuid = uuid.uuid4()
    allocated_to_id = str(tenant_uuid)
    for budget in budgets:
        budget.tenant_id = str(tenant_uuid)
        created = budget_service.create_budget(
            tenant_id=budget.tenant_id,
            budget_name=f"{budget.budget_type}-budget",
            budget_type=budget.budget_type,
            budget_amount=Decimal(str(budget.budget_amount)),
            period_type=budget.period_type,
            start_date=budget.start_date,
            allocated_to_type=budget.budget_type,
            allocated_to_id=allocated_to_id,
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

