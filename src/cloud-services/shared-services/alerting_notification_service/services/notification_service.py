"""Notification delivery implementations."""
from __future__ import annotations

import asyncio
from contextlib import nullcontext
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

try:  # pragma: no cover
    from opentelemetry import trace
except ImportError:  # pragma: no cover
    trace = None

from ..clients import PolicyClient
from ..config import get_settings
from ..database.models import Alert, Notification
from ..observability.metrics import NOTIFICATION_COUNTER
from ..repositories import AlertRepository, NotificationRepository
from .preference_service import UserPreferenceService

settings = get_settings()
tracer = trace.get_tracer(__name__) if trace else None


class NotificationChannel:
    async def send(self, notification: Notification) -> str:
        raise NotImplementedError


class EmailChannel(NotificationChannel):
    async def send(self, notification: Notification) -> str:
        await asyncio.sleep(0)
        return "sent"


class SmsChannel(NotificationChannel):
    async def send(self, notification: Notification) -> str:
        await asyncio.sleep(0)
        return "sent"


class VoiceChannel(NotificationChannel):
    async def send(self, notification: Notification) -> str:
        await asyncio.sleep(0)
        return "sent"


class WebhookChannel(NotificationChannel):
    async def send(self, notification: Notification) -> str:
        await asyncio.sleep(0)
        return "sent"


class NotificationDispatcher:
    """Enhanced notification dispatcher with retry, backoff, and fallback support."""

    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        policy_client: Optional[PolicyClient] = None,
        preference_service: Optional[UserPreferenceService] = None,
    ):
        self.channels: Dict[str, NotificationChannel] = {
            "email": EmailChannel(),
            "sms": SmsChannel(),
            "voice": VoiceChannel(),
            "webhook": WebhookChannel(),
        }
        self.session = session
        self.policy_client = policy_client or PolicyClient()
        self.preference_service = preference_service

    async def dispatch(
        self,
        notification: Notification,
        alert: Optional[Alert] = None,
    ) -> str:
        """
        Dispatch notification with retry and fallback support.
        
        Returns:
            "sent" if successfully sent
            "failed" if all attempts and fallbacks exhausted
            "pending" if scheduled for retry
        """
        span_context = (
            tracer.start_as_current_span("notification_dispatch")
            if tracer
            else nullcontext()  # type: ignore[attr-defined]
        )
        with span_context as span:
            if span and trace:  # pragma: no cover
                span.set_attribute("notification.channel", notification.channel)
                span.set_attribute("notification.target", notification.target_id)

            # Check user preferences and quiet hours
            if self.preference_service and alert:
                should_notify = await self.preference_service.should_notify(
                    notification.target_id,
                    alert.severity,
                    notification.channel,
                )
                if not should_notify:
                    notification.status = "cancelled"
                    notification.failure_reason = "quiet_hours_or_preference"
                    if self.session:
                        from ..repositories import NotificationRepository

                        repo = NotificationRepository(self.session)
                        await repo.save(notification)
                    NOTIFICATION_COUNTER.labels(channel=notification.channel, status="cancelled").inc()
                    return "cancelled"

            # Get retry policy
            severity = alert.severity if alert else "P2"
            retry_policy = self.policy_client.get_retry_policy(notification.channel, severity)
            max_attempts = retry_policy["max_attempts"]
            backoff_intervals = retry_policy["backoff_intervals"]

            # Try sending with retries
            attempt = notification.attempts or 0
            while attempt < max_attempts:
                try:
                    channel = self.channels.get(notification.channel, EmailChannel())
                    status = await channel.send(notification)
                    notification.status = status
                    notification.attempts = attempt + 1
                    notification.last_attempt_at = datetime.utcnow()

                    if status == "sent":
                        NOTIFICATION_COUNTER.labels(channel=notification.channel, status="sent").inc()
                        if self.session:
                            from ..repositories import NotificationRepository

                            repo = NotificationRepository(self.session)
                            await repo.save(notification)
                        return "sent"
                    else:
                        # Channel returned failure, try next attempt
                        attempt += 1
                        if attempt < max_attempts:
                            # Schedule retry
                            backoff_seconds = backoff_intervals[min(attempt - 1, len(backoff_intervals) - 1)]
                            notification.next_attempt_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)
                            notification.status = "pending"
                            if self.session:
                                from ..repositories import NotificationRepository

                                repo = NotificationRepository(self.session)
                                await repo.save(notification)
                            return "pending"

                except Exception as e:
                    # Exception during send, try next attempt
                    attempt += 1
                    notification.failure_reason = str(e)
                    if attempt < max_attempts:
                        backoff_seconds = backoff_intervals[min(attempt - 1, len(backoff_intervals) - 1)]
                        notification.next_attempt_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)
                        notification.status = "pending"
                        if self.session:
                            from ..repositories import NotificationRepository

                            repo = NotificationRepository(self.session)
                            await repo.save(notification)
                        return "pending"

        # All retries exhausted, try fallback channels
        if alert and self.session:
            fallback_channels = self.policy_client.get_fallback_channels(alert.severity, notification.channel)
            if fallback_channels:
                # Create fallback notifications
                from ..repositories import NotificationRepository

                repo = NotificationRepository(self.session)
                fallback_notifications = []
                for fallback_channel in fallback_channels:
                    fallback_notification = Notification(
                        notification_id=f"fallback-{notification.notification_id}-{fallback_channel}",
                        tenant_id=notification.tenant_id,
                        alert_id=notification.alert_id,
                        incident_id=notification.incident_id,
                        target_id=notification.target_id,
                        channel=fallback_channel,
                        status="pending",
                        policy_id=notification.policy_id,
                    )
                    saved = await repo.save(fallback_notification)
                    fallback_notifications.append(saved)

                # Mark original as failed
                notification.status = "failed"
                notification.failure_reason = "exhausted_retries_fallback_created"
                await repo.save(notification)
                NOTIFICATION_COUNTER.labels(channel=notification.channel, status="failed").inc()

                # Try first fallback immediately
                if fallback_notifications:
                    return await self.dispatch(fallback_notifications[0], alert)

        # No fallbacks or all exhausted
        notification.status = "failed"
        notification.failure_reason = "exhausted_retries_no_fallback"
        if self.session:
            from ..repositories import NotificationRepository

            repo = NotificationRepository(self.session)
            await repo.save(notification)
        NOTIFICATION_COUNTER.labels(channel=notification.channel, status="failed").inc()
        return "failed"
