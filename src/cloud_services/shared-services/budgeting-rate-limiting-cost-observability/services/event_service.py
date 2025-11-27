"""
Event Service for M35.

What: Publishes events to M31 Notification Engine using common event envelope
Why: Provides alerting and notification integration per PRD
Reads/Writes: Publishes events to M31 via dependencies
Contracts: Event contracts per PRD lines 2706-2803
Risks: Event delivery failures, M31 unavailability
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

from ..dependencies import MockM31NotificationEngine

logger = logging.getLogger(__name__)


class EventService:
    """
    Event Service per M35 PRD Notification Engine Integration section.

    Handles: Event publishing to M31 using common event envelope.
    """

    def __init__(self, notification_engine: MockM31NotificationEngine):
        """
        Initialize event service.

        Args:
            notification_engine: M31 notification engine
        """
        self.notification_engine = notification_engine

    def _create_event_envelope(
        self,
        event_type: str,
        tenant_id: str,
        payload: Dict[str, Any],
        environment: str = "production",
        plane: str = "tenant"
    ) -> Dict[str, Any]:
        """
        Create common event envelope per PRD lines 2709-2720.

        Args:
            event_type: Event type
            tenant_id: Tenant identifier
            payload: Event payload
            environment: Environment
            plane: Plane

        Returns:
            Event envelope dictionary
        """
        return {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "ts": datetime.utcnow().isoformat() + 'Z',
            "tenant_id": tenant_id,
            "environment": environment,
            "plane": plane,
            "source_module": "M35",
            "payload": payload
        }

    def publish_budget_threshold_exceeded(
        self,
        tenant_id: str,
        budget_id: str,
        threshold: str,
        utilization_ratio: float,
        spent_amount: Decimal,
        remaining_budget: Decimal,
        enforcement_action: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Publish budget threshold exceeded event per PRD lines 2725-2737.

        Args:
            tenant_id: Tenant identifier
            budget_id: Budget identifier
            threshold: Threshold (warning_80, critical_90, exhausted_100)
            utilization_ratio: Utilization ratio
            spent_amount: Spent amount
            remaining_budget: Remaining budget
            enforcement_action: Enforcement action
            correlation_id: Correlation ID

        Returns:
            Event ID
        """
        payload = {
            "budget_id": budget_id,
            "threshold": threshold,
            "utilization_ratio": utilization_ratio,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "spent_amount": str(spent_amount),
            "remaining_budget": str(remaining_budget),
            "enforcement_action": enforcement_action
        }

        envelope = self._create_event_envelope(
            event_type="budget_threshold_exceeded",
            tenant_id=tenant_id,
            payload=payload
        )

        return self.notification_engine.publish_event(envelope)

    def publish_rate_limit_violated(
        self,
        tenant_id: str,
        policy_id: str,
        resource_key: str,
        current_rate: int,
        limit: int,
        reset_time: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Publish rate limit violated event per PRD lines 2738-2750.

        Args:
            tenant_id: Tenant identifier
            policy_id: Policy identifier
            resource_key: Resource key
            current_rate: Current rate
            limit: Limit value
            reset_time: Reset time
            correlation_id: Correlation ID

        Returns:
            Event ID
        """
        payload = {
            "policy_id": policy_id,
            "resource_key": resource_key,
            "current_rate": current_rate,
            "limit": limit,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "reset_time": reset_time,
            "retry_after": None  # Would calculate from reset_time
        }

        envelope = self._create_event_envelope(
            event_type="rate_limit_violated",
            tenant_id=tenant_id,
            payload=payload
        )

        return self.notification_engine.publish_event(envelope)

    def publish_cost_anomaly_detected(
        self,
        tenant_id: str,
        anomaly_id: str,
        dimension: str,
        expected_cost: float,
        observed_cost: float,
        severity: str,
        deviation_percentage: float,
        time_period: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Publish cost anomaly detected event per PRD lines 2751-2764.

        Args:
            tenant_id: Tenant identifier
            anomaly_id: Anomaly identifier
            dimension: Dimension
            expected_cost: Expected cost
            observed_cost: Observed cost
            severity: Severity
            deviation_percentage: Deviation percentage
            time_period: Time period
            correlation_id: Correlation ID

        Returns:
            Event ID
        """
        payload = {
            "anomaly_id": anomaly_id,
            "dimension": dimension,
            "expected_cost": expected_cost,
            "observed_cost": observed_cost,
            "severity": severity,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "deviation_percentage": deviation_percentage,
            "time_period": time_period
        }

        envelope = self._create_event_envelope(
            event_type="cost_anomaly_detected",
            tenant_id=tenant_id,
            payload=payload
        )

        return self.notification_engine.publish_event(envelope)

    def publish_quota_exhausted(
        self,
        tenant_id: str,
        quota_id: str,
        resource_type: str,
        used_amount: Decimal,
        allocated_amount: Decimal,
        remaining_amount: Decimal,
        period_end: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Publish quota exhausted event per PRD lines 2779-2791.

        Args:
            tenant_id: Tenant identifier
            quota_id: Quota identifier
            resource_type: Resource type
            used_amount: Used amount
            allocated_amount: Allocated amount
            remaining_amount: Remaining amount
            period_end: Period end
            correlation_id: Correlation ID

        Returns:
            Event ID
        """
        payload = {
            "quota_id": quota_id,
            "resource_type": resource_type,
            "used_amount": str(used_amount),
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "allocated_amount": str(allocated_amount),
            "remaining_amount": str(remaining_amount),
            "period_end": period_end
        }

        envelope = self._create_event_envelope(
            event_type="quota_exhausted",
            tenant_id=tenant_id,
            payload=payload
        )

        return self.notification_engine.publish_event(envelope)

