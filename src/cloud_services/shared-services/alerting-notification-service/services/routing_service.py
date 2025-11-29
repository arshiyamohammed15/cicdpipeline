"""Routing and escalation services."""
from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

try:  # pragma: no cover
    from opentelemetry import trace
except ImportError:  # pragma: no cover
    trace = None

from ..clients import IAMClient, PolicyClient
from ..config import get_settings
from ..database.models import Alert, Notification
from ..repositories import NotificationRepository
from ..observability.metrics import NOTIFICATION_COUNTER, QUEUE_DEPTH
from .fatigue_control import FatigueControlService
from .preference_service import UserPreferenceService

settings = get_settings()
tracer = trace.get_tracer(__name__) if trace else None


@dataclass
class RoutingDecision:
    targets: List[str]
    channels: List[str]
    policy_id: str


class RoutingService:
    def __init__(
        self,
        repo: NotificationRepository,
        policy_client: Optional[PolicyClient] = None,
        iam_client: Optional[IAMClient] = None,
        preference_service: Optional[UserPreferenceService] = None,
        fatigue_control: Optional[FatigueControlService] = None,
    ):
        self.repo = repo
        self.policy_client = policy_client or PolicyClient()
        self.iam_client = iam_client or IAMClient()
        self.preference_service = preference_service
        self.fatigue_control = fatigue_control

    async def route_alert(self, alert: Alert) -> List[Notification]:
        """Route alert using policy-driven routing rules with user preference filtering."""
        span_context = (
            tracer.start_as_current_span("route_alert") if tracer else nullcontext()  # type: ignore[attr-defined]
        )
        with span_context as span:
            if span and trace:  # pragma: no cover
                span.set_attribute("tenant_id", alert.tenant_id)
                span.set_attribute("severity", alert.severity)
            alert_payload = {
                "tenant_id": alert.tenant_id,
                "source_module": alert.source_module,
                "component_id": alert.component_id,
                "severity": alert.severity,
                "category": alert.category,
                "plane": alert.plane,
                "environment": alert.environment,
            }
            routing = await self.policy_client.resolve_routing(alert_payload)
        targets = routing["targets"]
        channels = routing["channels"]
        policy_id = routing["policy_id"]

        # Expand targets via IAM (groups, schedules -> users)
        expanded_targets = await self.iam_client.expand_targets(targets)

        notifications = []
        now = datetime.utcnow()
        for target in expanded_targets:
            # Apply user preferences to filter and order channels
            if self.preference_service:
                user_channels = self.preference_service.filter_channels_by_preferences(
                    channels, alert.severity, await self.preference_service.get_preferences_or_default(target), now
                )
            else:
                user_channels = channels

            # Check fatigue controls before creating notification
            if self.fatigue_control:
                should_suppress, reason = await self.fatigue_control.should_suppress_notification(alert, target, now)
                if should_suppress:
                    # Skip creating notification, but continue with other targets
                    continue

            # Create notifications for each allowed channel
            for channel in user_channels:
                notification = Notification(
                    notification_id=f"notif-{alert.alert_id}-{target}-{channel}-{now.timestamp()}",
                    tenant_id=alert.tenant_id,
                    alert_id=alert.alert_id,
                    target_id=target,
                    channel=channel,
                    status="pending",
                    policy_id=policy_id,
                )
                saved = await self.repo.save(notification)
                notifications.append(saved)
                QUEUE_DEPTH.inc()
        return notifications

    async def record_delivery(self, notification: Notification, status: str) -> None:
        notification.status = status
        notification.attempts += 1
        notification.last_attempt_at = datetime.utcnow()
        await self.repo.save(notification)
        NOTIFICATION_COUNTER.labels(channel=notification.channel, status=status).inc()
        if status in {"sent", "failed"}:
            QUEUE_DEPTH.dec()


class QuietHoursEvaluator:
    def __init__(self, quiet_hours: dict[str, str]):
        self.quiet_hours = quiet_hours

    def is_quiet(self, now: datetime) -> bool:
        window = self.quiet_hours.get(now.strftime("%a"))
        if not window:
            return False
        start_str, end_str = window.split("-")
        start = datetime.strptime(start_str, "%H:%M").time()
        end = datetime.strptime(end_str, "%H:%M").time()
        current = now.time()
        if start <= end:
            return start <= current <= end
        return current >= start or current <= end
