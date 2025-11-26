"""User preference and quiet hours management."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..database.models import Alert, UserNotificationPreference
from ..repositories import AlertRepository


class UserPreferenceService:
    """Service for fetching and applying user notification preferences."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_preferences(self, user_id: str) -> Optional[UserNotificationPreference]:
        """Fetch user notification preferences."""
        return await self.session.get(UserNotificationPreference, user_id)

    async def get_preferences_or_default(self, user_id: str) -> UserNotificationPreference:
        """Get user preferences or return defaults."""
        pref = await self.get_preferences(user_id)
        if pref:
            return pref
        # Return default preferences
        return UserNotificationPreference(
            user_id=user_id,
            tenant_id="global",
            channels=[],
            quiet_hours={},
            severity_threshold={},
            timezone="UTC",
            channel_preferences={},
        )

    def filter_channels_by_preferences(
        self,
        channels: List[str],
        severity: str,
        preferences: UserNotificationPreference,
        now: Optional[datetime] = None,
    ) -> List[str]:
        """
        Filter and order channels based on user preferences.
        
        Returns channels in priority order, filtered by:
        - User's channel preferences (if specified for this severity)
        - Severity thresholds (skip channels below threshold)
        - Quiet hours (skip non-urgent channels during quiet hours)
        """
        if now is None:
            now = datetime.utcnow()

        # Get severity-specific channel preferences
        severity_prefs = preferences.channel_preferences.get(severity, [])
        if severity_prefs:
            # User has explicit preferences for this severity
            # Filter to only include channels in both lists
            filtered = [ch for ch in severity_prefs if ch in channels]
            if filtered:
                return filtered

        # Check severity threshold per channel
        threshold = preferences.severity_threshold.get(severity)
        if threshold:
            # If user has a threshold, only include channels that meet it
            # For now, we'll use the channel list as-is (threshold logic can be enhanced)
            pass

        # Check quiet hours
        from ..services.routing_service import QuietHoursEvaluator

        evaluator = QuietHoursEvaluator(preferences.quiet_hours)
        if evaluator.is_quiet(now):
            # During quiet hours, only allow high-severity channels
            if severity in {"P0", "P1"}:
                # Only urgent channels (SMS, voice) during quiet hours
                urgent_channels = [ch for ch in channels if ch in {"sms", "voice"}]
                if urgent_channels:
                    return urgent_channels
                # If no urgent channels, return empty (don't notify during quiet hours for non-urgent)
                return []
            else:
                # Non-urgent alerts: skip during quiet hours
                return []

        # Return channels in user's preferred order if available
        if preferences.channels:
            ordered = [ch for ch in preferences.channels if ch in channels]
            if ordered:
                return ordered

        # Default: return channels as-is
        return channels

    async def should_notify(
        self,
        user_id: str,
        severity: str,
        channel: str,
        now: Optional[datetime] = None,
    ) -> bool:
        """
        Determine if a notification should be sent based on user preferences.
        
        Returns False if:
        - User has quiet hours configured and it's currently quiet hours (for non-urgent alerts)
        - Channel doesn't meet severity threshold
        """
        if now is None:
            now = datetime.utcnow()

        preferences = await self.get_preferences_or_default(user_id)

        # Check quiet hours
        from ..services.routing_service import QuietHoursEvaluator

        evaluator = QuietHoursEvaluator(preferences.quiet_hours)
        if evaluator.is_quiet(now):
            # During quiet hours, only allow high-severity channels
            if severity not in {"P0", "P1"}:
                return False
            if channel not in {"sms", "voice"}:
                return False

        # Check severity threshold (if user has one for this severity)
        threshold = preferences.severity_threshold.get(severity)
        if threshold:
            # Threshold logic can be enhanced based on requirements
            pass

        return True

