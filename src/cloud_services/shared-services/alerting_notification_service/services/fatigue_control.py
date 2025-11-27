"""Alert fatigue control services: rate limiting, maintenance windows, suppression."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..clients import PolicyClient
from ..database.models import Alert, Incident, Notification
from ..repositories import AlertRepository, IncidentRepository, NotificationRepository


class RateLimiter:
    """Rate limiter for notifications per alert and per user."""

    def __init__(self, session: AsyncSession, policy_client: Optional[PolicyClient] = None):
        self.session = session
        self.policy_client = policy_client or PolicyClient()
        self.notification_repo = NotificationRepository(session)
        self._rate_limit_config = None

    def _get_config(self) -> Dict[str, Any]:
        """Get rate limit configuration from policy."""
        if self._rate_limit_config is None:
            self._rate_limit_config = self.policy_client.get_rate_limit_config()
        return self._rate_limit_config

    async def check_alert_rate_limit(self, alert_id: str) -> bool:
        """
        Check if alert has exceeded rate limit for notifications.
        
        Returns:
            True if within limit (can send), False if exceeded
        """
        config = self._get_config()
        alert_config = config.get("per_alert", {})
        max_notifications = alert_config.get("max_notifications", 5)
        window_minutes = alert_config.get("window_minutes", 60)

        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
        statement = select(Notification).where(
            Notification.alert_id == alert_id,
            Notification.created_at >= window_start,
            Notification.status.in_(["sent", "pending"]),  # Count sent and pending
        )
        result = await self.session.exec(statement)
        notifications = list(result.scalars().all())
        count = len(notifications)

        # Allow if count is less than max (not equal)
        return count < max_notifications

    async def check_user_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit for notifications.
        
        Returns:
            True if within limit (can send), False if exceeded
        """
        config = self._get_config()
        user_config = config.get("per_user", {})
        max_notifications = user_config.get("max_notifications", 20)
        window_minutes = user_config.get("window_minutes", 60)

        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
        statement = select(Notification).where(
            Notification.target_id == user_id,
            Notification.created_at >= window_start,
            Notification.status.in_(["sent", "pending"]),  # Count sent and pending
        )
        result = await self.session.exec(statement)
        notifications = list(result.scalars().all())
        count = len(notifications)

        # Allow if count is less than max (not equal)
        return count < max_notifications

    async def get_alert_notification_count(self, alert_id: str, window_minutes: int = 60) -> int:
        """Get count of notifications for an alert in the time window."""
        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
        statement = select(Notification).where(
            Notification.alert_id == alert_id,
            Notification.created_at >= window_start,
        )
        result = await self.session.exec(statement)
        return len(list(result.scalars().all()))

    async def get_user_notification_count(self, user_id: str, window_minutes: int = 60) -> int:
        """Get count of notifications for a user in the time window."""
        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
        statement = select(Notification).where(
            Notification.target_id == user_id,
            Notification.created_at >= window_start,
        )
        result = await self.session.exec(statement)
        return len(list(result.scalars().all()))


class MaintenanceWindowService:
    """Service for checking maintenance windows and suppressing alerts."""

    def __init__(self, policy_client: Optional[PolicyClient] = None):
        self.policy_client = policy_client or PolicyClient()
        self._maintenance_windows = None

    def _get_windows(self) -> List[Dict[str, Any]]:
        """Get maintenance windows from policy."""
        if self._maintenance_windows is None:
            self._maintenance_windows = self.policy_client.get_maintenance_windows()
        return self._maintenance_windows

    def is_in_maintenance(
        self,
        component_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> bool:
        """
        Check if component or tenant is in a maintenance window.
        
        Args:
            component_id: Component to check
            tenant_id: Tenant to check
            now: Current time (defaults to UTC now)
        
        Returns:
            True if in maintenance window, False otherwise
        """
        if now is None:
            now = datetime.utcnow()

        windows = self._get_windows()
        for window in windows:
            start_str = window.get("start")
            end_str = window.get("end")
            if not start_str or not end_str:
                continue

            try:
                start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue

            # Check time range
            if not (start <= now <= end):
                continue

            # Check scope
            window_component = window.get("component_id")
            window_tenant = window.get("tenant_id")

            # If window has specific component/tenant, must match
            if window_component is not None:
                if component_id is None or window_component != component_id:
                    continue
            if window_tenant is not None:
                if tenant_id is None or window_tenant != tenant_id:
                    continue

            # Matches scope (either explicitly matches or window has no scope restrictions)
            return True

        return False


class FatigueControlService:
    """Orchestrates all fatigue control mechanisms."""

    def __init__(
        self,
        session: AsyncSession,
        policy_client: Optional[PolicyClient] = None,
        rate_limiter: Optional[RateLimiter] = None,
        maintenance_service: Optional[MaintenanceWindowService] = None,
    ):
        self.session = session
        self.policy_client = policy_client or PolicyClient()
        self.rate_limiter = rate_limiter or RateLimiter(session, policy_client)
        self.maintenance_service = maintenance_service or MaintenanceWindowService(policy_client)
        self.alert_repo = AlertRepository(session)
        self.incident_repo = IncidentRepository(session)

    async def should_suppress_notification(
        self,
        alert: Alert,
        target_id: str,
        now: Optional[datetime] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if notification should be suppressed.
        
        Returns:
            (should_suppress, reason)
        """
        if now is None:
            now = datetime.utcnow()

        # Check maintenance window
        if self.maintenance_service.is_in_maintenance(alert.component_id, alert.tenant_id, now):
            return True, "maintenance_window"

        # Check rate limits
        if not await self.rate_limiter.check_alert_rate_limit(alert.alert_id):
            return True, "alert_rate_limit_exceeded"

        if not await self.rate_limiter.check_user_rate_limit(target_id):
            return True, "user_rate_limit_exceeded"

        # Check incident suppression
        suppression_config = self.policy_client.get_suppression_config()
        if suppression_config.get("suppress_followup_during_incident", True):
            if alert.incident_id:
                incident = await self.incident_repo.fetch(alert.incident_id)
                if incident and incident.status == "open":
                    # Check if this is a follow-up alert (not the first one)
                    window_minutes = suppression_config.get("suppress_window_minutes", 15)
                    window_start = now - timedelta(minutes=window_minutes)
                    # Count alerts in this incident created before this one
                    from sqlalchemy import select

                    statement = select(Alert).where(
                        Alert.incident_id == alert.incident_id,
                        Alert.started_at < alert.started_at,
                        Alert.started_at >= window_start,
                    )
                    result = await self.session.exec(statement)
                    existing_alerts = list(result.scalars().all())
                    if existing_alerts:
                        return True, "incident_followup_suppressed"

        return False, None

    async def tag_alert_as_noisy(self, alert_id: str, actor: Optional[str] = None) -> Alert:
        """Tag an alert as noisy for review."""
        alert = await self.alert_repo.fetch(alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        # Ensure labels dict exists and update it
        labels = dict(alert.labels) if alert.labels else {}
        labels["noisy"] = "true"
        labels["noisy_tagged_at"] = datetime.utcnow().isoformat()
        if actor:
            labels["noisy_tagged_by"] = actor
        alert.labels = labels

        return await self.alert_repo.upsert_alert(alert)

    async def tag_alert_as_false_positive(self, alert_id: str, actor: Optional[str] = None) -> Alert:
        """Tag an alert as false positive."""
        alert = await self.alert_repo.fetch(alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        # Ensure labels dict exists and update it
        labels = dict(alert.labels) if alert.labels else {}
        labels["false_positive"] = "true"
        labels["false_positive_tagged_at"] = datetime.utcnow().isoformat()
        if actor:
            labels["false_positive_tagged_by"] = actor
        alert.labels = labels

        return await self.alert_repo.upsert_alert(alert)

    async def get_noisy_alerts(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 100,
        days: int = 30,
    ) -> List[Alert]:
        """
        Get top noisy alerts for review.
        
        Args:
            tenant_id: Filter by tenant (optional)
            limit: Maximum number of alerts to return
            days: Look back period in days
        
        Returns:
            List of alerts sorted by notification count (descending)
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        statement = select(Alert).where(Alert.started_at >= cutoff)

        if tenant_id:
            statement = statement.where(Alert.tenant_id == tenant_id)

        result = await self.session.exec(statement)
        alerts = list(result.scalars().all())

        # Calculate notification counts and sort
        alert_counts = []
        for alert in alerts:
            count = await self.rate_limiter.get_alert_notification_count(alert.alert_id, window_minutes=days * 24 * 60)
            alert_counts.append((count, alert))

        # Sort by count descending
        alert_counts.sort(key=lambda x: x[0], reverse=True)

        # Return top N
        return [alert for _, alert in alert_counts[:limit]]

    async def export_noisy_alerts_report(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 100,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Export a report of noisy alerts for review.
        
        Returns:
            Dictionary with report data including alerts, counts, and metadata
        """
        alerts = await self.get_noisy_alerts(tenant_id, limit, days)
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
            "period_days": days,
            "total_alerts": len(alerts),
            "alerts": [],
        }

        for alert in alerts:
            notification_count = await self.rate_limiter.get_alert_notification_count(
                alert.alert_id, window_minutes=days * 24 * 60
            )
            report["alerts"].append(
                {
                    "alert_id": alert.alert_id,
                    "tenant_id": alert.tenant_id,
                    "component_id": alert.component_id,
                    "severity": alert.severity,
                    "category": alert.category,
                    "summary": alert.summary,
                    "notification_count": notification_count,
                    "started_at": alert.started_at.isoformat(),
                    "labels": alert.labels,
                }
            )

        return report

