"""
Cost Calculation Service for EPC-13 (Budgeting, Rate-Limiting & Cost Observability).

What: Manages cost recording, attribution, aggregation, and anomaly detection
Why: Provides cost transparency per PRD lines 189-245
Reads/Writes: Reads/writes cost records to database
Contracts: Cost tracking API per PRD
Risks: Cost calculation errors, attribution mistakes, data loss
"""

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from ..database.models import CostRecord
from ..utils.transactions import read_committed_transaction

logger = logging.getLogger(__name__)


class CostService:
    """
    Cost Calculation Service per M35 PRD Functional Components section 3.

    Handles: Cost recording, attribution, aggregation, anomaly detection.
    """

    def __init__(self, db: Session):
        """
        Initialize cost service.

        Args:
            db: Database session
        """
        self.db = db

    def record_cost(
        self,
        tenant_id: str,
        resource_type: str,
        cost_amount: Decimal,
        usage_quantity: Decimal,
        attributed_to_type: str,
        attributed_to_id: str,
        resource_id: Optional[str] = None,
        usage_unit: Optional[str] = None,
        service_name: Optional[str] = None,
        region: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        currency: str = "USD",
        timestamp: Optional[datetime] = None
    ) -> CostRecord:
        """
        Record cost per PRD lines 197-202 (real-time resource metering).

        Args:
            tenant_id: Tenant identifier
            resource_type: Resource type
            cost_amount: Cost amount
            usage_quantity: Usage quantity
            attributed_to_type: Attributed to type
            attributed_to_id: Attributed to identifier
            resource_id: Resource identifier
            usage_unit: Usage unit
            service_name: Service name
            region: Region
            tags: Tags
            currency: Currency code
            timestamp: Optional timestamp (defaults to current UTC time)

        Returns:
            Created cost record
        """
        cost_record = CostRecord(
            cost_id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            resource_id=uuid.UUID(resource_id) if resource_id else uuid.uuid4(),
            resource_type=resource_type,
            cost_amount=cost_amount,
            currency=currency,
            usage_quantity=usage_quantity,
            usage_unit=usage_unit,
            timestamp=timestamp or datetime.utcnow(),
            attributed_to_type=attributed_to_type,
            attributed_to_id=uuid.UUID(attributed_to_id),
            service_name=service_name or "unknown",
            region=region,
            tags=tags or {}
        )

        # Use READ COMMITTED transaction isolation for cost recording per PRD
        with read_committed_transaction(self.db):
            self.db.add(cost_record)
            # Transaction helper commits automatically

        # Refresh after commit to get database-generated values
        self.db.refresh(cost_record)
        logger.info(f"Recorded cost {cost_amount} for tenant {tenant_id}, resource {resource_type}")
        return cost_record

    def get_cost_record(self, record_id: str) -> Optional[CostRecord]:
        """
        Get cost record by ID.

        Args:
            record_id: Record identifier

        Returns:
            Cost record or None
        """
        return self.db.query(CostRecord).filter(
            CostRecord.cost_id == uuid.UUID(record_id)
        ).first()

    def query_cost_records(
        self,
        tenant_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        resource_type: Optional[str] = None,
        attributed_to_type: Optional[str] = None,
        attributed_to_id: Optional[str] = None,
        service_name: Optional[str] = None,
        group_by: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[List[CostRecord], int, Dict[str, Any]]:
        """
        Query cost records with filtering and aggregation per PRD.

        Args:
            tenant_id: Tenant identifier
            start_time: Start time filter
            end_time: End time filter
            resource_type: Resource type filter
            attributed_to_type: Attributed to type filter
            attributed_to_id: Attributed to ID filter
            service_name: Service name filter
            group_by: Group by dimensions
            page: Page number
            page_size: Page size

        Returns:
            Tuple of (records list, total count, aggregated data)
        """
        query = self.db.query(CostRecord).filter(
            CostRecord.tenant_id == uuid.UUID(tenant_id)
        )

        if start_time:
            query = query.filter(CostRecord.timestamp >= start_time)
        if end_time:
            query = query.filter(CostRecord.timestamp <= end_time)
        if resource_type:
            query = query.filter(CostRecord.resource_type == resource_type)
        if attributed_to_type:
            query = query.filter(CostRecord.attributed_to_type == attributed_to_type)
        if attributed_to_id:
            query = query.filter(CostRecord.attributed_to_id == uuid.UUID(attributed_to_id))
        if service_name:
            query = query.filter(CostRecord.service_name == service_name)

        total_count = query.count()
        records = query.order_by(desc(CostRecord.timestamp)).offset((page - 1) * page_size).limit(page_size).all()

        # Calculate aggregated totals
        aggregated_query = self.db.query(
            func.sum(CostRecord.cost_amount).label('total_cost'),
            func.sum(CostRecord.usage_quantity).label('total_usage')
        ).filter(
            CostRecord.tenant_id == uuid.UUID(tenant_id)
        )

        if start_time:
            aggregated_query = aggregated_query.filter(CostRecord.timestamp >= start_time)
        if end_time:
            aggregated_query = aggregated_query.filter(CostRecord.timestamp <= end_time)

        aggregated_result = aggregated_query.first()
        aggregated = {
            "total_cost": float(aggregated_result.total_cost) if aggregated_result.total_cost else 0.0,
            "total_usage": float(aggregated_result.total_usage) if aggregated_result.total_usage else 0.0,
            "currency": "USD"
        }

        return records, total_count, aggregated

    def generate_cost_report(
        self,
        tenant_id: str,
        report_type: str,
        start_time: datetime,
        end_time: datetime,
        group_by: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate cost report per PRD lines 1908-1977.

        Args:
            tenant_id: Tenant identifier
            report_type: Report type
            start_time: Start time
            end_time: End time
            group_by: Group by dimensions

        Returns:
            Cost report dictionary
        """
        records, total_count, aggregated = self.query_cost_records(
            tenant_id=tenant_id,
            start_time=start_time,
            end_time=end_time,
            group_by=group_by,
            page=1,
            page_size=10000  # Large page size for reports
        )

        breakdown = []
        if group_by:
            # Group records by specified dimensions
            grouped = {}
            for record in records:
                key_parts = []
                for dim in group_by:
                    if dim == "resource_type":
                        key_parts.append(record.resource_type)
                    elif dim == "service_name":
                        key_parts.append(record.service_name)
                    elif dim == "region":
                        key_parts.append(record.region or "unknown")
                    elif dim == "attributed_to_type":
                        key_parts.append(record.attributed_to_type)
                key = ":".join(key_parts)

                if key not in grouped:
                    grouped[key] = {
                        "dimensions": {dim: key_parts[i] for i, dim in enumerate(group_by)},
                        "total_cost": Decimal(0),
                        "total_usage": Decimal(0)
                    }

                grouped[key]["total_cost"] += record.cost_amount
                if record.usage_quantity:
                    grouped[key]["total_usage"] += record.usage_quantity

            breakdown = [
                {
                    **group_data["dimensions"],
                    "total_cost": float(group_data["total_cost"]),
                    "total_usage": float(group_data["total_usage"])
                }
                for group_data in grouped.values()
            ]

        return {
            "report_id": str(uuid.uuid4()),
            "report_type": report_type,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "total_cost": aggregated["total_cost"],
            "currency": aggregated["currency"],
            "breakdown": breakdown
        }

    def detect_anomalies(
        self,
        tenant_id: str,
        dimension: str = "tenant"
    ) -> List[Dict[str, Any]]:
        """
        Detect cost anomalies per PRD lines 238-245.

        Args:
            tenant_id: Tenant identifier
            dimension: Dimension to analyze

        Returns:
            List of anomaly dictionaries
        """
        # Calculate baseline (moving average of last 30 days)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=30)

        records, _, _ = self.query_cost_records(
            tenant_id=tenant_id,
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=10000
        )

        # Group by day
        daily_costs = {}
        for record in records:
            day = record.timestamp.date()
            if day not in daily_costs:
                daily_costs[day] = Decimal(0)
            daily_costs[day] += record.cost_amount

        if len(daily_costs) < 7:
            return []  # Not enough data

        # Calculate baseline (average of last 30 days)
        baseline = sum(daily_costs.values()) / len(daily_costs)

        # Check today's cost
        today = datetime.utcnow().date()
        today_cost = daily_costs.get(today, Decimal(0))

        anomalies = []
        if baseline > 0:
            deviation = float((today_cost - baseline) / baseline)

            if abs(deviation) > 0.5:  # Critical threshold
                anomalies.append({
                    "anomaly_id": str(uuid.uuid4()),
                    "dimension": dimension,
                    "expected_cost": float(baseline),
                    "observed_cost": float(today_cost),
                    "severity": "critical",
                    "deviation_percentage": deviation * 100,
                    "time_period": today.isoformat()
                })
            elif abs(deviation) > 0.25:  # Warning threshold
                anomalies.append({
                    "anomaly_id": str(uuid.uuid4()),
                    "dimension": dimension,
                    "expected_cost": float(baseline),
                    "observed_cost": float(today_cost),
                    "severity": "warning",
                    "deviation_percentage": deviation * 100,
                    "time_period": today.isoformat()
                })

        return anomalies

    def record_cost_batch(
        self,
        records: List[Dict[str, Any]]
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        processed = 0
        failed = 0
        failures: List[Dict[str, Any]] = []
        for record in records:
            try:
                self.record_cost(
                    tenant_id=record["tenant_id"],
                    resource_type=record["resource_type"],
                    cost_amount=Decimal(str(record["cost_amount"])),
                    usage_quantity=Decimal(str(record["usage_quantity"])),
                    attributed_to_type=record.get("attributed_to_type") or "tenant",
                    attributed_to_id=record.get("attributed_to_id") or record["tenant_id"],
                    resource_id=record.get("resource_id"),
                    usage_unit=record.get("usage_unit"),
                    service_name=record.get("service_name"),
                    region=record.get("region"),
                    tags=record.get("tags"),
                )
                processed += 1
            except Exception as exc:  # pragma: no cover - simple aggregation
                failed += 1
                failures.append(
                    {
                        "tenant_id": record.get("tenant_id"),
                        "resource_type": record.get("resource_type"),
                        "error": str(exc),
                    }
                )
        return processed, failed, failures

