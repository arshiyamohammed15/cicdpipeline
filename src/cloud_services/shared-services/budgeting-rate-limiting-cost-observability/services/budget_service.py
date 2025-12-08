"""
Budget Management Service for M35.

What: Manages budget definitions, period calculations, utilization tracking, and enforcement
Why: Provides real-time budget controls per PRD lines 72-122
Reads/Writes: Reads/writes budget definitions and utilization to database
Contracts: Budget management API per PRD
Risks: Budget calculation errors, race conditions, enforcement failures
"""

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..database.models import BudgetDefinition, BudgetUtilization
from ..dependencies import MockM29DataPlane
from ..utils.cache import CacheManager
from ..utils.transactions import serializable_transaction
from .event_service import EventService

logger = logging.getLogger(__name__)

# Budget type priority: Feature > User > Project > Tenant (most specific to least specific)
BUDGET_TYPE_PRIORITY = {
    "feature": 4,
    "user": 3,
    "project": 2,
    "tenant": 1
}


class BudgetService:
    """
    Budget Management Service per M35 PRD Functional Components section 1.

    Handles: Budget CRUD, period calculation, utilization tracking, enforcement.
    """

    def __init__(
        self,
        db: Session,
        data_plane: MockM29DataPlane,
        event_service: Optional[EventService] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        """
        Initialize budget service.

        Args:
            db: Database session
            data_plane: M29 data plane for caching
            event_service: Event service for notifications
            cache_manager: Cache manager for budget definitions
        """
        self.db = db
        self.data_plane = data_plane
        self.event_service = event_service
        self.cache_manager = cache_manager

    @staticmethod
    def _threshold_rank(threshold_name: str) -> int:
        order = {
            "warning_80": 1,
            "critical_90": 2,
            "exhausted_100": 3
        }
        return order.get(threshold_name, 0)

    def _threshold_cache_key(self, budget_id: uuid.UUID, period_start: datetime) -> str:
        return f"budget_threshold:{budget_id}:{period_start.isoformat()}"

    def _mark_threshold_triggered(
        self,
        budget_id: uuid.UUID,
        period_start: datetime,
        threshold_name: str,
        ttl_seconds: int
    ) -> None:
        cache_key = self._threshold_cache_key(budget_id, period_start)
        if self.cache_manager:
            self.cache_manager.set(cache_key, threshold_name, ttl_seconds=ttl_seconds)
        else:
            self.data_plane.cache_set(cache_key, threshold_name, ttl_seconds=ttl_seconds)

    def _was_threshold_already_triggered(
        self,
        budget_id: uuid.UUID,
        period_start: datetime,
        threshold_name: str
    ) -> bool:
        cache_key = self._threshold_cache_key(budget_id, period_start)
        if self.cache_manager:
            last = self.cache_manager.get(cache_key)
        else:
            last = self.data_plane.cache_get(cache_key)
        return last is not None and self._threshold_rank(last) >= self._threshold_rank(threshold_name)

    def _emit_threshold_event(
        self,
        budget: BudgetDefinition,
        threshold_name: str,
        utilization_ratio: float,
        spent_amount: Decimal,
        remaining_budget: Decimal,
        correlation_id: Optional[str] = None
    ) -> None:
        if not self.event_service:
            return

        self.event_service.publish_budget_threshold_exceeded(
            tenant_id=str(budget.tenant_id),
            budget_id=str(budget.budget_id),
            threshold=threshold_name,
            utilization_ratio=utilization_ratio,
            spent_amount=spent_amount,
            remaining_budget=remaining_budget,
            enforcement_action=budget.enforcement_action,
            correlation_id=correlation_id or str(uuid.uuid4())
        )

    def _maybe_emit_threshold_events(
        self,
        budget: BudgetDefinition,
        spent_amount: Decimal,
        remaining_budget: Decimal,
        period_start: datetime,
        period_end: datetime
    ) -> None:
        if not budget.thresholds:
            thresholds = {
                "warning_80": True,
                "critical_90": True,
                "exhausted_100": True
            }
        else:
            thresholds = budget.thresholds

        if budget.budget_amount <= 0:
            return

        utilization_ratio = float(spent_amount / budget.budget_amount)
        ttl_seconds = int((period_end - period_start).total_seconds())

        sequence = [
            ("warning_80", 0.80),
            ("critical_90", 0.90),
            ("exhausted_100", 1.00)
        ]

        for threshold_name, threshold_value in sequence:
            if not thresholds.get(threshold_name, False):
                continue

            if utilization_ratio >= threshold_value:
                if not self._was_threshold_already_triggered(budget.budget_id, period_start, threshold_name):
                    self._mark_threshold_triggered(budget.budget_id, period_start, threshold_name, ttl_seconds)
                    self._emit_threshold_event(
                        budget=budget,
                        threshold_name=threshold_name,
                        utilization_ratio=utilization_ratio,
                        spent_amount=spent_amount,
                        remaining_budget=remaining_budget
                    )

    def _create_approval_request(
        self,
        budget: BudgetDefinition,
        estimated_cost: Decimal,
        remaining_budget: Decimal
    ) -> Dict[str, Any]:
        approval_id = str(uuid.uuid4())
        approval_record = {
            "approval_id": approval_id,
            "budget_id": str(budget.budget_id),
            "tenant_id": str(budget.tenant_id),
            "status": "pending",
            "requested_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "estimated_cost": str(estimated_cost),
            "remaining_budget": str(remaining_budget)
        }
        self.data_plane.store(f"budget_approval:{approval_id}", approval_record)
        return approval_record

    def get_approval_request(self, approval_id: str) -> Optional[Dict[str, Any]]:
        return self.data_plane.get(f"budget_approval:{approval_id}")

    def update_approval_status(
        self,
        approval_id: str,
        status: str,
        rationale: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        record = self.get_approval_request(approval_id)
        if not record:
            return None
        record["status"] = status
        record["updated_at"] = datetime.utcnow().isoformat()
        if rationale:
            record["rationale"] = rationale
        self.data_plane.store(f"budget_approval:{approval_id}", record)
        return record

    def _calculate_period(
        self,
        period_type: str,
        start_date: datetime,
        end_date: Optional[datetime],
        first_usage_date: Optional[datetime] = None
    ) -> Tuple[datetime, datetime]:
        """
        Calculate budget period per PRD lines 85-101.

        Args:
            period_type: Period type (monthly, quarterly, yearly, custom)
            start_date: Budget start date
            end_date: Budget end date (for custom periods)
            first_usage_date: First usage date (for monthly rolling)

        Returns:
            Tuple of (period_start, period_end)
        """
        now = datetime.utcnow()

        if period_type == "monthly":
            # Monthly rolling: 30-day window from first usage or budget start
            period_start = first_usage_date or start_date
            period_end = period_start + timedelta(days=30)
        elif period_type == "quarterly":
            # Fixed calendar quarters
            quarter = (now.month - 1) // 3
            period_start = datetime(now.year, quarter * 3 + 1, 1)
            if quarter == 3:
                period_end = datetime(now.year + 1, 1, 1)
            else:
                period_end = datetime(now.year, (quarter + 1) * 3 + 1, 1)
        elif period_type == "yearly":
            # Yearly: calendar year
            period_start = datetime(now.year, 1, 1)
            period_end = datetime(now.year + 1, 1, 1)
        else:  # custom
            # Custom time windows: user-defined start and end
            period_start = start_date
            period_end = end_date or (start_date + timedelta(days=365))

        return period_start, period_end

    def _resolve_overlapping_budgets(
        self,
        budgets: List[BudgetDefinition]
    ) -> Optional[BudgetDefinition]:
        """
        Resolve overlapping budgets per PRD lines 102-104.

        Most restrictive budget applies (lowest budget_amount).
        Priority: Feature > User > Project > Tenant.

        Args:
            budgets: List of applicable budgets

        Returns:
            Most restrictive budget or None
        """
        if not budgets:
            return None

        # Sort by priority (highest first), then by budget_amount (lowest first)
        sorted_budgets = sorted(
            budgets,
            key=lambda b: (
                -BUDGET_TYPE_PRIORITY.get(b.budget_type, 0),
                float(b.budget_amount)
            )
        )

        return sorted_budgets[0]

    def resolve_overlapping_budgets(
        self,
        tenant_id: str,
        budget_type: Optional[str] = None,
        allocated_to_type: Optional[str] = None,
        allocated_to_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Public helper to resolve overlapping budgets for a tenant.

        Returns the most restrictive budget (highest priority, lowest amount)
        as a dictionary, or None if no applicable budgets exist.
        """
        query = self.db.query(BudgetDefinition).filter(BudgetDefinition.tenant_id == uuid.UUID(tenant_id))
        if budget_type:
            query = query.filter(BudgetDefinition.budget_type == budget_type)
        if allocated_to_type and allocated_to_id:
            query = query.filter(
                and_(
                    BudgetDefinition.allocated_to_type == allocated_to_type,
                    BudgetDefinition.allocated_to_id == uuid.UUID(allocated_to_id),
                )
            )
        budgets = query.all()
        resolved = self._resolve_overlapping_budgets(budgets)
        if not resolved:
            return None
        return {
            "budget_id": str(resolved.budget_id),
            "tenant_id": str(resolved.tenant_id),
            "budget_type": resolved.budget_type,
            "budget_amount": resolved.budget_amount,
            "period_type": resolved.period_type,
            "allocated_to_type": resolved.allocated_to_type,
            "allocated_to_id": str(resolved.allocated_to_id),
            "enforcement_action": resolved.enforcement_action,
        }

    def create_budget(
        self,
        tenant_id: str,
        budget_name: str,
        budget_type: str,
        budget_amount: Decimal,
        period_type: str,
        start_date: datetime,
        allocated_to_type: str,
        allocated_to_id: str,
        enforcement_action: str,
        currency: str = "USD",
        end_date: Optional[datetime] = None,
        thresholds: Optional[Dict[str, Any]] = None,
        notifications: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> BudgetDefinition:
        """
        Create budget definition per PRD.

        Args:
            tenant_id: Tenant identifier
            budget_name: Budget name
            budget_type: Budget type
            budget_amount: Budget amount
            period_type: Period type
            start_date: Start date
            allocated_to_type: Allocated to type
            allocated_to_id: Allocated to identifier
            enforcement_action: Enforcement action
            currency: Currency code
            end_date: End date (for custom periods)
            thresholds: Threshold configuration
            notifications: Notification configuration
            created_by: Creator identifier

        Returns:
            Created budget definition
        """
        budget = BudgetDefinition(
            budget_id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            budget_name=budget_name,
            budget_type=budget_type,
            budget_amount=budget_amount,
            currency=currency,
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            allocated_to_type=allocated_to_type,
            allocated_to_id=uuid.UUID(allocated_to_id),
            enforcement_action=enforcement_action,
            thresholds=thresholds or {},
            notifications=notifications or {},
            created_by=uuid.UUID(created_by) if created_by else uuid.uuid4()
        )

        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)

        logger.info(f"Created budget {budget.budget_id} for tenant {tenant_id}")
        return budget

    def get_budget(self, budget_id: str) -> Optional[BudgetDefinition]:
        """
        Get budget by ID.

        Args:
            budget_id: Budget identifier

        Returns:
            Budget definition or None
        """
        return self.db.query(BudgetDefinition).filter(
            BudgetDefinition.budget_id == uuid.UUID(budget_id)
        ).first()

    def list_budgets(
        self,
        tenant_id: str,
        budget_type: Optional[str] = None,
        allocated_to_type: Optional[str] = None,
        allocated_to_id: Optional[str] = None,
        active_only: bool = False,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[List[BudgetDefinition], int]:
        """
        List budgets for tenant with filtering and pagination.

        Args:
            tenant_id: Tenant identifier
            budget_type: Optional budget type filter
            allocated_to_type: Optional allocated to type filter
            allocated_to_id: Optional allocated to ID filter
            active_only: Whether to return only active budgets
            page: Page number
            page_size: Page size

        Returns:
            Tuple of (budgets list, total count)
        """
        query = self.db.query(BudgetDefinition).filter(
            BudgetDefinition.tenant_id == uuid.UUID(tenant_id)
        )

        if budget_type:
            query = query.filter(BudgetDefinition.budget_type == budget_type)
        if allocated_to_type:
            query = query.filter(BudgetDefinition.allocated_to_type == allocated_to_type)
        if allocated_to_id:
            query = query.filter(BudgetDefinition.allocated_to_id == uuid.UUID(allocated_to_id))
        if active_only:
            now = datetime.utcnow()
            query = query.filter(
                or_(
                    BudgetDefinition.end_date.is_(None),
                    BudgetDefinition.end_date > now
                )
            )

        total_count = query.count()
        budgets = query.offset((page - 1) * page_size).limit(page_size).all()

        return budgets, total_count

    def _get_budget_utilization(
        self,
        budget_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime
    ) -> Decimal:
        """
        Get budget utilization for period.

        Args:
            budget_id: Budget identifier
            period_start: Period start
            period_end: Period end

        Returns:
            Spent amount
        """
        utilization = self.db.query(BudgetUtilization).filter(
            and_(
                BudgetUtilization.budget_id == budget_id,
                BudgetUtilization.period_start == period_start,
                BudgetUtilization.period_end == period_end
            )
        ).first()

        if utilization:
            return utilization.spent_amount
        return Decimal(0)

    def _update_budget_utilization(
        self,
        budget_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
        cost: Decimal,
        tenant_id: uuid.UUID
    ) -> BudgetUtilization:
        """
        Update budget utilization (atomic operation).

        Args:
            budget_id: Budget identifier
            period_start: Period start
            period_end: Period end
            cost: Cost to add
            tenant_id: Tenant identifier

        Returns:
            Updated utilization record
        """
        utilization = self.db.query(BudgetUtilization).filter(
            and_(
                BudgetUtilization.budget_id == budget_id,
                BudgetUtilization.period_start == period_start,
                BudgetUtilization.period_end == period_end
            )
        ).first()

        # Use SERIALIZABLE transaction isolation for budget utilization updates per PRD
        with serializable_transaction(self.db):
            if utilization:
                utilization.spent_amount += cost
                utilization.last_updated = datetime.utcnow()
            else:
                utilization = BudgetUtilization(
                    utilization_id=uuid.uuid4(),
                    budget_id=budget_id,
                    tenant_id=tenant_id,
                    period_start=period_start,
                    period_end=period_end,
                    spent_amount=cost,
                    last_updated=datetime.utcnow()
                )
                self.db.add(utilization)
            # Transaction helper commits automatically
        
        # Refresh after commit to get database-generated values
        self.db.refresh(utilization)
        return utilization

    def check_budget(
        self,
        tenant_id: str,
        resource_type: str,
        estimated_cost: Decimal,
        allocated_to_type: Optional[str] = None,
        allocated_to_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check budget availability per PRD lines 105-122.

        Args:
            tenant_id: Tenant identifier
            resource_type: Resource type
            estimated_cost: Estimated cost
            allocated_to_type: Allocated to type
            allocated_to_id: Allocated to identifier

        Returns:
            Budget check result dictionary
        """
        now = datetime.utcnow()

        # Find applicable budgets
        query = self.db.query(BudgetDefinition).filter(
            BudgetDefinition.tenant_id == uuid.UUID(tenant_id)
        )

        if allocated_to_type and allocated_to_id:
            # Check specific allocation
            query = query.filter(
                and_(
                    BudgetDefinition.allocated_to_type == allocated_to_type,
                    BudgetDefinition.allocated_to_id == uuid.UUID(allocated_to_id)
                )
            )

        # Filter active budgets
        query = query.filter(
            and_(
                BudgetDefinition.start_date <= now,
                or_(
                    BudgetDefinition.end_date.is_(None),
                    BudgetDefinition.end_date > now
                )
            )
        )

        budgets = query.all()

        if not budgets:
            # No budget found - allow by default (or could be configured)
            return {
                "allowed": True,
                "remaining_budget": Decimal("999999999"),
                "budget_id": None,
                "enforcement_action": None,
                "utilization_ratio": 0.0,
                "requires_approval": False,
                "approval_id": None
            }

        # Resolve overlapping budgets
        budget = self._resolve_overlapping_budgets(budgets)

        if not budget:
            return {
                "allowed": True,
                "remaining_budget": Decimal("999999999"),
                "budget_id": None,
                "enforcement_action": None,
                "utilization_ratio": 0.0,
                "requires_approval": False,
                "approval_id": None
            }

        # Calculate period
        period_start, period_end = self._calculate_period(
            budget.period_type,
            budget.start_date,
            budget.end_date
        )

        # Get current utilization
        spent = self._get_budget_utilization(budget.budget_id, period_start, period_end)
        remaining = budget.budget_amount - spent
        utilization_ratio = float(spent / budget.budget_amount) if budget.budget_amount > 0 else 0.0

        # Check if operation is allowed
        allowed = True
        requires_approval = False
        approval_id = None

        if remaining < estimated_cost:
            # Budget exhausted
            if budget.enforcement_action == "hard_stop":
                allowed = False
            elif budget.enforcement_action == "escalate":
                allowed = False
                approval_record = self._create_approval_request(
                    budget=budget,
                    estimated_cost=estimated_cost,
                    remaining_budget=remaining
                )
                requires_approval = True
                approval_id = approval_record["approval_id"]

        # Update utilization if allowed
        if allowed:
            self._update_budget_utilization(
                budget.budget_id,
                period_start,
                period_end,
                estimated_cost,
                budget.tenant_id
            )
            remaining -= estimated_cost
            spent += estimated_cost
            utilization_ratio = float(spent / budget.budget_amount) if budget.budget_amount > 0 else 0.0
            self._maybe_emit_threshold_events(
                budget=budget,
                spent_amount=spent,
                remaining_budget=remaining,
                period_start=period_start,
                period_end=period_end
            )
        else:
            # Even if not allowed, emit exhausted event when thresholds enabled
            self._maybe_emit_threshold_events(
                budget=budget,
                spent_amount=spent,
                remaining_budget=remaining,
                period_start=period_start,
                period_end=period_end
            )

        return {
            "allowed": allowed,
            "remaining_budget": max(remaining, Decimal(0)),
            "budget_id": str(budget.budget_id),
            "enforcement_action": budget.enforcement_action,
            "utilization_ratio": utilization_ratio,
            "requires_approval": requires_approval,
            "approval_id": approval_id
        }

    def check_budget_batch(
        self,
        checks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for check in checks:
            result = self.check_budget(
                tenant_id=check["tenant_id"],
                resource_type=check["resource_type"],
                estimated_cost=Decimal(str(check["estimated_cost"])),
                allocated_to_type=check.get("allocated_to_type"),
                allocated_to_id=check.get("allocated_to_id")
            )
            results.append(result)
        return results

    def update_budget(
        self,
        budget_id: str,
        **updates
    ) -> Optional[BudgetDefinition]:
        """
        Update budget definition.

        Args:
            budget_id: Budget identifier
            **updates: Fields to update

        Returns:
            Updated budget definition or None
        """
        budget = self.get_budget(budget_id)
        if not budget:
            return None

        for key, value in updates.items():
            if hasattr(budget, key) and value is not None:
                if key in ["tenant_id", "allocated_to_id", "created_by"]:
                    setattr(budget, key, uuid.UUID(value))
                else:
                    setattr(budget, key, value)

        self.db.commit()
        self.db.refresh(budget)
        return budget

    def delete_budget(self, budget_id: str) -> bool:
        """
        Delete budget definition.

        Args:
            budget_id: Budget identifier

        Returns:
            True if deleted, False if not found
        """
        budget = self.get_budget(budget_id)
        if not budget:
            return False

        # Check if there's active utilization
        utilization = self.db.query(BudgetUtilization).filter(
            BudgetUtilization.budget_id == uuid.UUID(budget_id)
        ).first()

        if utilization and utilization.spent_amount > 0:
            raise ValueError("Cannot delete budget with active utilization")

        self.db.delete(budget)
        self.db.commit()
        return True

