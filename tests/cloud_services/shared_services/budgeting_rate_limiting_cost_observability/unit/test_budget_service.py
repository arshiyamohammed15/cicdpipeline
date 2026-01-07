"""
Tests for Budget Service.

100% test coverage for budget management functionality.
"""


# Imports handled by conftest.py
import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from budgeting_rate_limiting_cost_observability.database.models import Base
from budgeting_rate_limiting_cost_observability.services.budget_service import BudgetService
from budgeting_rate_limiting_cost_observability.dependencies import MockM29DataPlane


class DummyEventService:
    """Simple stub to capture emitted events."""

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
        correlation_id: str
    ) -> str:
        self.events.append(
            {
                "tenant_id": tenant_id,
                "budget_id": budget_id,
                "threshold": threshold,
                "utilization_ratio": utilization_ratio,
                "spent_amount": spent_amount,
                "remaining_budget": remaining_budget,
                "enforcement_action": enforcement_action,
                "correlation_id": correlation_id,
            }
        )
        return str(uuid.uuid4())


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
def budget_service(db_session):
    """Create budget service instance."""
    return BudgetService(db_session, MockM29DataPlane(), DummyEventService())


@pytest.mark.unit
class TestBudgetService:
    """Test suite for BudgetService."""

    @pytest.mark.budgeting_regression
    @pytest.mark.unit
    def test_create_budget(self, budget_service):
        """Test budget creation."""
        budget = budget_service.create_budget(
            tenant_id=str(uuid.uuid4()),
            budget_name="Test Budget",
            budget_type="tenant",
            budget_amount=Decimal("1000.00"),
            period_type="monthly",
            start_date=datetime.utcnow(),
            allocated_to_type="tenant",
            allocated_to_id=str(uuid.uuid4()),
            enforcement_action="hard_stop",
            created_by=str(uuid.uuid4())
        )

        assert budget.budget_id is not None
        assert budget.budget_name == "Test Budget"
        assert budget.budget_amount == Decimal("1000.00")

    @pytest.mark.unit
    def test_get_budget(self, budget_service):
        """Test getting budget by ID."""
        budget = budget_service.create_budget(
                tenant_id=str(uuid.uuid4()),
            budget_name="Test Budget",
            budget_type="tenant",
            budget_amount=Decimal("1000.00"),
            period_type="monthly",
            start_date=datetime.utcnow(),
            allocated_to_type="tenant",
            allocated_to_id=str(uuid.uuid4()),
            enforcement_action="hard_stop",
            created_by=str(uuid.uuid4())
        )

        retrieved = budget_service.get_budget(str(budget.budget_id))
        assert retrieved is not None
        assert retrieved.budget_id == budget.budget_id

    @pytest.mark.unit
    def test_list_budgets(self, budget_service):
        """Test listing budgets."""
        tenant_id = str(uuid.uuid4())
        for i in range(5):
            budget_service.create_budget(
                tenant_id=tenant_id,
                budget_name=f"Budget {i}",
                budget_type="tenant",
                budget_amount=Decimal("1000.00"),
                period_type="monthly",
                start_date=datetime.utcnow(),
                allocated_to_type="tenant",
                allocated_to_id=str(uuid.uuid4()),
                enforcement_action="hard_stop",
                created_by=str(uuid.uuid4())
            )

        budgets, total_count = budget_service.list_budgets(tenant_id=tenant_id)
        assert total_count == 5
        assert len(budgets) == 5

    @pytest.mark.unit
    def test_check_budget_allowed(self, budget_service):
        """Test budget check when budget allows operation."""
        tenant_id = str(uuid.uuid4())
        budget = budget_service.create_budget(
            tenant_id=tenant_id,
            budget_name="Test Budget",
            budget_type="tenant",
            budget_amount=Decimal("1000.00"),
            period_type="monthly",
            start_date=datetime.utcnow(),
            allocated_to_type="tenant",
            allocated_to_id=tenant_id,
            enforcement_action="hard_stop",
            created_by=str(uuid.uuid4())
        )

        result = budget_service.check_budget(
            tenant_id=tenant_id,
            resource_type="api_calls",
            estimated_cost=Decimal("100.00"),
            allocated_to_type="tenant",
            allocated_to_id=tenant_id
        )

        assert result["allowed"] is True
        assert result["remaining_budget"] < Decimal("1000.00")

    @pytest.mark.unit
    def test_check_budget_exceeded(self, budget_service):
        """Test budget check when budget is exceeded."""
        tenant_id = str(uuid.uuid4())
        budget = budget_service.create_budget(
            tenant_id=tenant_id,
            budget_name="Test Budget",
            budget_type="tenant",
            budget_amount=Decimal("100.00"),
            period_type="monthly",
            start_date=datetime.utcnow(),
            allocated_to_type="tenant",
            allocated_to_id=tenant_id,
            enforcement_action="hard_stop",
            created_by=str(uuid.uuid4())
        )

        # First check should succeed
        result1 = budget_service.check_budget(
            tenant_id=tenant_id,
            resource_type="api_calls",
            estimated_cost=Decimal("50.00"),
            allocated_to_type="tenant",
            allocated_to_id=tenant_id
        )
        assert result1["allowed"] is True

        # Second check should fail (exceeds remaining)
        result2 = budget_service.check_budget(
            tenant_id=tenant_id,
            resource_type="api_calls",
            estimated_cost=Decimal("60.00"),
            allocated_to_type="tenant",
            allocated_to_id=tenant_id
        )
        assert result2["allowed"] is False

    @pytest.mark.unit
    def test_update_budget(self, budget_service):
        """Test budget update."""
        budget = budget_service.create_budget(
            tenant_id=str(uuid.uuid4()),
            budget_name="Test Budget",
            budget_type="tenant",
            budget_amount=Decimal("1000.00"),
            period_type="monthly",
            start_date=datetime.utcnow(),
            allocated_to_type="tenant",
            allocated_to_id=str(uuid.uuid4()),
            enforcement_action="hard_stop",
            created_by=str(uuid.uuid4())
        )

        updated = budget_service.update_budget(
            str(budget.budget_id),
            budget_amount=Decimal("2000.00")
        )

        assert updated is not None
        assert updated.budget_amount == Decimal("2000.00")

    @pytest.mark.unit
    def test_delete_budget(self, budget_service):
        """Test budget deletion."""
        budget = budget_service.create_budget(
            tenant_id=str(uuid.uuid4()),
            budget_name="Test Budget",
            budget_type="tenant",
            budget_amount=Decimal("1000.00"),
            period_type="monthly",
            start_date=datetime.utcnow(),
            allocated_to_type="tenant",
            allocated_to_id=str(uuid.uuid4()),
            enforcement_action="hard_stop",
            created_by=str(uuid.uuid4())
        )

        budget_id = str(budget.budget_id)

        deleted = budget_service.delete_budget(budget_id)
        assert deleted is True

        retrieved = budget_service.get_budget(budget_id)
        assert retrieved is None

    @pytest.mark.unit
    def test_period_calculation_monthly(self, budget_service):
        """Test monthly period calculation."""
        start_date = datetime.utcnow()
        period_start, period_end = budget_service._calculate_period(
            period_type="monthly",
            start_date=start_date,
            end_date=None
        )

        assert period_start == start_date
        assert (period_end - period_start).days == 30

    @pytest.mark.unit
    def test_resolve_overlapping_budgets(self, budget_service):
        """Test overlapping budget resolution."""
        tenant_id = str(uuid.uuid4())
        allocated_id = str(uuid.uuid4())

        # Create budgets with different types and amounts
        budgets = []
        for budget_type, amount in [("tenant", 1000), ("project", 500), ("user", 300), ("feature", 200)]:
            budget = budget_service.create_budget(
                tenant_id=tenant_id,
                budget_name=f"{budget_type} Budget",
                budget_type=budget_type,
                budget_amount=Decimal(str(amount)),
                period_type="monthly",
                start_date=datetime.utcnow(),
                allocated_to_type=budget_type,
                allocated_to_id=allocated_id,
                enforcement_action="hard_stop",
                created_by=str(uuid.uuid4())
            )
            budgets.append(budget)

        # Most restrictive should be feature (highest priority, lowest amount)
        resolved = budget_service._resolve_overlapping_budgets(budgets)
        assert resolved.budget_type == "feature"
        assert resolved.budget_amount == Decimal("200")

    @pytest.mark.unit
    def test_check_budget_escalate_creates_approval(self, budget_service):
        """Escalation enforcement should trigger approval workflow."""
        tenant_id = str(uuid.uuid4())
        budget_service.create_budget(
            tenant_id=tenant_id,
            budget_name="Escalation Budget",
            budget_type="tenant",
            budget_amount=Decimal("50.00"),
            period_type="monthly",
            start_date=datetime.utcnow(),
            allocated_to_type="tenant",
            allocated_to_id=tenant_id,
            enforcement_action="escalate",
            created_by=str(uuid.uuid4())
        )

        result = budget_service.check_budget(
            tenant_id=tenant_id,
            resource_type="api_calls",
            estimated_cost=Decimal("60.00"),
            allocated_to_type="tenant",
            allocated_to_id=tenant_id
        )

        assert result["allowed"] is False
        assert result["requires_approval"] is True
        assert result["approval_id"] is not None

        approval_record = budget_service.get_approval_request(result["approval_id"])
        assert approval_record is not None
        assert approval_record["status"] == "pending"

    @pytest.mark.unit
    def test_threshold_event_emitted_once(self, budget_service):
        """Threshold events must emit only once per period."""
        tenant_id = str(uuid.uuid4())
        budget_service.create_budget(
            tenant_id=tenant_id,
            budget_name="Threshold Budget",
            budget_type="tenant",
            budget_amount=Decimal("100.00"),
            period_type="monthly",
            start_date=datetime.utcnow(),
            allocated_to_type="tenant",
            allocated_to_id=tenant_id,
            enforcement_action="soft_limit",
            thresholds={"warning_80": True, "critical_90": False, "exhausted_100": False},
            created_by=str(uuid.uuid4())
        )

        budget_service.check_budget(
            tenant_id=tenant_id,
            resource_type="compute",
            estimated_cost=Decimal("85.00"),
            allocated_to_type="tenant",
            allocated_to_id=tenant_id
        )

        budget_service.check_budget(
            tenant_id=tenant_id,
            resource_type="compute",
            estimated_cost=Decimal("1.00"),
            allocated_to_type="tenant",
            allocated_to_id=tenant_id
        )

        events = budget_service.event_service.events
        assert len(events) == 1
        assert events[0]["threshold"] == "warning_80"

