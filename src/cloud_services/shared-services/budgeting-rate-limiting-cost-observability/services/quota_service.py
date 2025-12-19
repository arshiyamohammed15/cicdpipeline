"""
Quota Management Service for EPC-13 (Budgeting, Rate-Limiting & Cost Observability).

What: Manages quota allocations, enforcement, renewal, and usage tracking
Why: Provides resource quota controls per PRD lines 246-300
Reads/Writes: Reads/writes quota allocations and usage history to database
Contracts: Quota management API per PRD
Risks: Quota exhaustion, race conditions, renewal failures
"""

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database.models import QuotaAllocation, QuotaUsageHistory
from ..utils.transactions import serializable_transaction

logger = logging.getLogger(__name__)


class QuotaService:
    """
    Quota Management Service per EPC-13 PRD Functional Components section 4.

    Handles: Quota CRUD, allocation strategies, enforcement, renewal automation.
    """

    def __init__(self, db: Session):
        """
        Initialize quota service.

        Args:
            db: Database session
        """
        self.db = db

    def allocate_quota(
        self,
        tenant_id: str,
        resource_type: str,
        allocated_amount: Decimal,
        period_start: datetime,
        period_end: datetime,
        allocation_type: str,
        max_burst_amount: Optional[Decimal] = None,
        auto_renew: bool = True
    ) -> QuotaAllocation:
        """
        Allocate quota per PRD lines 255-274.

        Args:
            tenant_id: Tenant identifier
            resource_type: Resource type
            allocated_amount: Allocated amount
            period_start: Period start
            period_end: Period end
            allocation_type: Allocation type
            max_burst_amount: Max burst amount
            auto_renew: Auto renew flag

        Returns:
            Created quota allocation
        """
        quota = QuotaAllocation(
            quota_id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            resource_type=resource_type,
            allocated_amount=allocated_amount,
            used_amount=Decimal(0),
            period_start=period_start,
            period_end=period_end,
            allocation_type=allocation_type,
            max_burst_amount=max_burst_amount,
            auto_renew=auto_renew
        )

        # Use SERIALIZABLE transaction isolation for quota allocation per PRD
        with serializable_transaction(self.db):
            self.db.add(quota)
            # Transaction helper commits automatically
        
        # Refresh after commit to get database-generated values
        self.db.refresh(quota)
        logger.info(f"Allocated quota {allocated_amount} for tenant {tenant_id}, resource {resource_type}")
        return quota

    def get_quota(self, quota_id: str) -> Optional[QuotaAllocation]:
        """
        Get quota by ID.

        Args:
            quota_id: Quota identifier

        Returns:
            Quota allocation or None
        """
        return self.db.query(QuotaAllocation).filter(
            QuotaAllocation.quota_id == uuid.UUID(quota_id)
        ).first()

    def list_quotas(
        self,
        tenant_id: str,
        resource_type: Optional[str] = None,
        allocation_type: Optional[str] = None,
        active_only: bool = False,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[List[QuotaAllocation], int]:
        """
        List quotas with filtering and pagination.

        Args:
            tenant_id: Tenant identifier
            resource_type: Optional resource type filter
            allocation_type: Optional allocation type filter
            active_only: Whether to return only active quotas
            page: Page number
            page_size: Page size

        Returns:
            Tuple of (quotas list, total count)
        """
        query = self.db.query(QuotaAllocation).filter(
            QuotaAllocation.tenant_id == uuid.UUID(tenant_id)
        )

        if resource_type:
            query = query.filter(QuotaAllocation.resource_type == resource_type)
        if allocation_type:
            query = query.filter(QuotaAllocation.allocation_type == allocation_type)
        if active_only:
            now = datetime.utcnow()
            query = query.filter(
                and_(
                    QuotaAllocation.period_start <= now,
                    QuotaAllocation.period_end > now
                )
            )

        total_count = query.count()
        quotas = query.offset((page - 1) * page_size).limit(page_size).all()

        return quotas, total_count

    def check_quota(
        self,
        tenant_id: str,
        resource_type: str,
        required_amount: Decimal
    ) -> Dict[str, Any]:
        """
        Check quota availability per PRD lines 275-295.

        Args:
            tenant_id: Tenant identifier
            resource_type: Resource type
            required_amount: Required quota amount

        Returns:
            Quota check result dictionary
        """
        now = datetime.utcnow()

        # Find active quota
        quota = self.db.query(QuotaAllocation).filter(
            and_(
                QuotaAllocation.tenant_id == uuid.UUID(tenant_id),
                QuotaAllocation.resource_type == resource_type,
                QuotaAllocation.period_start <= now,
                QuotaAllocation.period_end > now
            )
        ).first()

        if not quota:
            # No quota found - allow by default (or could be configured)
            return {
                "allowed": True,
                "remaining_amount": Decimal("999999999"),
                "quota_id": None,
                "used_amount": Decimal(0),
                "allocated_amount": Decimal(0)
            }

        # Calculate available amount (including burst)
        max_available = quota.allocated_amount + (quota.max_burst_amount or Decimal(0))
        available = max_available - quota.used_amount

        # Check if operation is allowed
        allowed = available >= required_amount

        if allowed:
            # Update used amount with SERIALIZABLE isolation to prevent race conditions
            with serializable_transaction(self.db):
                # Re-fetch inside txn to avoid stale reads
                locked_quota = self.db.query(QuotaAllocation).with_for_update().filter(
                    QuotaAllocation.quota_id == quota.quota_id
                ).one()
                locked_available = (locked_quota.allocated_amount + (locked_quota.max_burst_amount or Decimal(0))) - locked_quota.used_amount
                if locked_available < required_amount:
                    allowed = False
                else:
                    locked_quota.used_amount += required_amount
                    locked_quota.last_updated = datetime.utcnow()
                    usage_history = QuotaUsageHistory(
                        usage_id=uuid.uuid4(),
                        quota_id=locked_quota.quota_id,
                        tenant_id=locked_quota.tenant_id,
                        usage_timestamp=now,
                        usage_amount=required_amount,
                        operation_type="quota_consumption"
                    )
                    self.db.add(usage_history)
            # Refresh after txn if still allowed
            if allowed:
                self.db.refresh(quota)

        # Check thresholds for warnings
        utilization_ratio = float(quota.used_amount / quota.allocated_amount) if quota.allocated_amount > 0 else 0.0
        if utilization_ratio >= 0.9:
            severity = "critical"
        elif utilization_ratio >= 0.8:
            severity = "warning"
        else:
            severity = None

        return {
            "allowed": allowed,
            "remaining_amount": max(available - required_amount if allowed else available, Decimal(0)),
            "quota_id": str(quota.quota_id),
            "used_amount": quota.used_amount,
            "allocated_amount": quota.allocated_amount,
            "utilization_ratio": utilization_ratio,
            "severity": severity
        }

    def update_quota(
        self,
        quota_id: str,
        **updates
    ) -> Optional[QuotaAllocation]:
        """
        Update quota allocation.

        Args:
            quota_id: Quota identifier
            **updates: Fields to update

        Returns:
            Updated quota or None
        """
        quota = self.get_quota(quota_id)
        if not quota:
            return None

        for key, value in updates.items():
            if hasattr(quota, key) and value is not None:
                if key in ["tenant_id"]:
                    setattr(quota, key, uuid.UUID(value))
                else:
                    setattr(quota, key, value)

        self.db.commit()
        self.db.refresh(quota)
        return quota

    def delete_quota(self, quota_id: str) -> bool:
        """
        Delete quota allocation.

        Args:
            quota_id: Quota identifier

        Returns:
            True if deleted, False if not found
        """
        quota = self.get_quota(quota_id)
        if not quota:
            return False

        # Check if there's active usage
        if quota.used_amount > 0:
            raise ValueError("Cannot delete quota with active usage")

        self.db.delete(quota)
        self.db.commit()
        return True

    def allocate_quota_batch(
        self,
        allocations: List[Dict[str, Any]]
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        successful = 0
        failed = 0
        failures: List[Dict[str, Any]] = []
        for allocation in allocations:
            try:
                self.allocate_quota(
                    tenant_id=allocation["tenant_id"],
                    resource_type=allocation["resource_type"],
                    allocated_amount=Decimal(str(allocation["allocated_amount"])),
                    period_start=datetime.fromisoformat(allocation["period_start"].replace("Z", "+00:00")),
                    period_end=datetime.fromisoformat(allocation["period_end"].replace("Z", "+00:00")),
                    allocation_type=allocation["allocation_type"],
                    max_burst_amount=Decimal(str(allocation["max_burst_amount"])) if allocation.get("max_burst_amount") is not None else None,
                    auto_renew=allocation.get("auto_renew", True)
                )
                successful += 1
            except Exception as exc:  # pragma: no cover - aggregation only
                failed += 1
                failures.append(
                    {
                        "tenant_id": allocation.get("tenant_id"),
                        "resource_type": allocation.get("resource_type"),
                        "error": str(exc),
                    }
                )
        return successful, failed, failures

    def renew_expired_quotas(self) -> int:
        """
        Renew expired quotas with auto_renew=True per PRD lines 289-300.

        Returns:
            Number of quotas renewed
        """
        now = datetime.utcnow()
        expired_quotas = self.db.query(QuotaAllocation).filter(
            and_(
                QuotaAllocation.period_end <= now,
                QuotaAllocation.auto_renew == True
            )
        ).all()

        renewed_count = 0
        for quota in expired_quotas:
            # Calculate new period (same duration as original)
            period_duration = quota.period_end - quota.period_start
            new_period_start = now
            new_period_end = now + period_duration

            # Create new quota allocation
            new_quota = QuotaAllocation(
                quota_id=uuid.uuid4(),
                tenant_id=quota.tenant_id,
                resource_type=quota.resource_type,
                allocated_amount=quota.allocated_amount,
                used_amount=Decimal(0),  # Reset usage for new period
                period_start=new_period_start,
                period_end=new_period_end,
                allocation_type=quota.allocation_type,
                max_burst_amount=quota.max_burst_amount,
                auto_renew=quota.auto_renew
            )
            self.db.add(new_quota)
            renewed_count += 1

        if renewed_count > 0:
            self.db.commit()

        logger.info(f"Renewed {renewed_count} expired quotas")
        return renewed_count

