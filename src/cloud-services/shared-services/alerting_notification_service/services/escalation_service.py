"""Escalation policy execution engine."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..clients import IAMClient, PolicyClient
from ..database.models import Alert, Incident, Notification
from ..repositories import NotificationRepository
from ..observability.metrics import NOTIFICATION_COUNTER, QUEUE_DEPTH


class EscalationService:
    """Executes escalation policies with delays and step-based notifications."""

    def __init__(
        self,
        session: AsyncSession,
        policy_client: Optional[PolicyClient] = None,
        iam_client: Optional[IAMClient] = None,
        notification_repo: Optional[NotificationRepository] = None,
    ):
        self.session = session
        self.policy_client = policy_client or PolicyClient()
        self.iam_client = iam_client or IAMClient()
        self.notification_repo = notification_repo or NotificationRepository(session)

    async def execute_escalation(
        self,
        alert: Alert,
        policy_id: Optional[str] = None,
        current_step: int = 1,
    ) -> List[Notification]:
        """
        Execute escalation policy for an alert.
        
        Args:
            alert: The alert to escalate
            policy_id: Escalation policy ID (defaults to policy from routing)
            current_step: Current escalation step (1-based)
        
        Returns:
            List of notifications created for this escalation step
        """
        # Get escalation policy
        if not policy_id:
            routing = await self.policy_client.resolve_routing(
                {
                    "tenant_id": alert.tenant_id,
                    "severity": alert.severity,
                    "category": alert.category,
                }
            )
            policy_id = routing.get("policy_id", "default")

        policy = self.policy_client.get_escalation_policy(policy_id)
        if not policy:
            policy = self.policy_client.get_default_escalation_policy()

        steps = policy.get("steps", [])
        if not steps or current_step > len(steps):
            # No more steps or policy exhausted
            return []

        step = steps[current_step - 1]
        delay_seconds = step.get("delay_seconds", 0)
        channels = step.get("channels", [])
        target_group = step.get("target_group_id") or step.get("schedule_id")

        # Check if we should skip this step (e.g., alert already ACK'd)
        if await self._should_skip_escalation(alert, policy):
            return []

        # Wait for delay if needed (in real implementation, this would be async scheduled)
        if delay_seconds > 0:
            # In production, this would be handled by a background task scheduler
            # For now, we create notifications with next_attempt_at set
            pass

        # Resolve targets for this step
        if target_group:
            targets = await self.iam_client.expand_targets([target_group])
        else:
            # Fallback to default routing targets
            routing = await self.policy_client.resolve_routing(
                {
                    "tenant_id": alert.tenant_id,
                    "severity": alert.severity,
                    "category": alert.category,
                }
            )
            targets = routing["targets"]
            targets = await self.iam_client.expand_targets(targets)

        # Create notifications for this escalation step
        notifications = []
        for target in targets:
            for channel in channels:
                notification = Notification(
                    notification_id=f"escal-{alert.alert_id}-step{current_step}-{target}-{channel}-{datetime.utcnow().timestamp()}",
                    tenant_id=alert.tenant_id,
                    alert_id=alert.alert_id,
                    target_id=target,
                    channel=channel,
                    status="pending",
                    policy_id=policy_id,
                    next_attempt_at=datetime.utcnow() + timedelta(seconds=delay_seconds) if delay_seconds > 0 else None,
                )
                saved = await self.notification_repo.save(notification)
                notifications.append(saved)
                QUEUE_DEPTH.inc()

        return notifications

    async def _should_skip_escalation(self, alert: Alert, policy: Dict) -> bool:
        """
        Determine if escalation should be skipped.
        
        Escalation is skipped if:
        - Alert is acknowledged and policy says to stop on ACK
        - Alert is resolved
        - Alert is snoozed
        - Incident is mitigated (partial resolution)
        """
        if alert.status == "resolved":
            return True

        if alert.status == "acknowledged":
            # Check if policy allows escalation after ACK
            continue_after_ack = policy.get("continue_after_ack", False)
            return not continue_after_ack

        if alert.status == "snoozed":
            return True

        # Check if incident is mitigated
        if alert.incident_id:
            from ..repositories import IncidentRepository
            incident_repo = IncidentRepository(self.session)
            incident = await incident_repo.fetch(alert.incident_id)
            if incident and incident.status == "mitigated":
                return True

        return False

    async def schedule_next_escalation_step(
        self,
        alert: Alert,
        policy_id: str,
        current_step: int,
    ) -> None:
        """
        Schedule the next escalation step after the delay.
        
        In production, this would integrate with a task scheduler (e.g., Celery, APScheduler).
        For now, this is a placeholder that would be called by a background worker.
        """
        # This would be implemented by a background task that:
        # 1. Waits for delay_seconds
        # 2. Checks if escalation should still proceed
        # 3. Calls execute_escalation with current_step + 1
        pass

    async def get_pending_escalations(self, alert_id: Optional[str] = None) -> List[Notification]:
        """Get notifications that are pending escalation (next_attempt_at in the past)."""
        now = datetime.utcnow()
        statement = select(Notification).where(
            Notification.status == "pending",
            Notification.next_attempt_at <= now,
        )
        if alert_id:
            statement = statement.where(Notification.alert_id == alert_id)

        result = await self.session.exec(statement)
        return list(result.scalars().all())

