"""Background task scheduler for escalation steps with delays."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from ..clients import PolicyClient
from ..repositories import AlertRepository, NotificationRepository
from .escalation_service import EscalationService

logger = logging.getLogger(__name__)


class EscalationScheduler:
    """Background worker that processes pending escalation steps."""

    def __init__(
        self,
        session_factory,
        policy_client: Optional[PolicyClient] = None,
        check_interval_seconds: int = 30,
    ):
        """
        Initialize escalation scheduler.
        
        Args:
            session_factory: Factory function that returns an AsyncSession
            policy_client: Policy client instance
            check_interval_seconds: How often to check for pending escalations
        """
        self.session_factory = session_factory
        self.policy_client = policy_client or PolicyClient()
        self.check_interval_seconds = check_interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._stop_event: Optional[asyncio.Event] = None

    async def start(self) -> None:
        """Start the escalation scheduler background task."""
        if self._task:
            logger.warning("Escalation scheduler already running")
            return

        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run(), name="escalation-scheduler")
        logger.info("Escalation scheduler started", extra={"check_interval_seconds": self.check_interval_seconds})

    async def stop(self) -> None:
        """Stop the escalation scheduler."""
        if not self._task:
            return

        self._stop_event.set()
        try:
            await asyncio.wait_for(self._task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Escalation scheduler stop timeout")
        except Exception as exc:
            logger.error("Error stopping escalation scheduler: %s", exc)
        finally:
            self._task = None
            self._stop_event = None
            logger.info("Escalation scheduler stopped")

    async def _run(self) -> None:
        """Main scheduler loop."""
        while not self._stop_event.is_set():
            try:
                await self._process_pending_escalations()
            except Exception as exc:
                logger.error("Error in escalation scheduler loop: %s", exc, exc_info=True)

            # Wait for next check interval or stop signal
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.check_interval_seconds
                )
                # Stop event was set, exit loop
                break
            except asyncio.TimeoutError:
                # Timeout is expected, continue loop
                continue

    async def _process_pending_escalations(self) -> None:
        """Process all pending escalation steps that are due."""
        async with self.session_factory() as session:
            escalation_service = EscalationService(
                session=session,
                policy_client=self.policy_client,
            )

            # Get all pending escalations (notifications with next_attempt_at in the past)
            pending_notifications = await escalation_service.get_pending_escalations()

            if not pending_notifications:
                return

            logger.info(
                "Processing pending escalations",
                extra={"count": len(pending_notifications)}
            )

            # Group by alert_id to process escalations per alert
            alerts_to_escalate = {}
            for notification in pending_notifications:
                alert_id = notification.alert_id
                if alert_id not in alerts_to_escalate:
                    alerts_to_escalate[alert_id] = {
                        "alert": None,
                        "policy_id": notification.policy_id,
                        "current_step": self._extract_step_from_notification(notification),
                    }
                    # Fetch alert
                    alert_repo = AlertRepository(session)
                    alert = await alert_repo.fetch(alert_id)
                    if alert:
                        alerts_to_escalate[alert_id]["alert"] = alert

            # Process each alert's escalation
            for alert_id, escalation_info in alerts_to_escalate.items():
                if not escalation_info["alert"]:
                    logger.warning("Alert not found for escalation: %s", alert_id)
                    continue

                try:
                    # Execute next escalation step
                    next_step = escalation_info["current_step"] + 1
                    notifications = await escalation_service.execute_escalation(
                        alert=escalation_info["alert"],
                        policy_id=escalation_info["policy_id"],
                        current_step=next_step,
                    )

                    if notifications:
                        logger.info(
                            "Executed escalation step",
                            extra={
                                "alert_id": alert_id,
                                "step": next_step,
                                "notifications_created": len(notifications),
                            }
                        )
                        await session.commit()
                    else:
                        logger.debug(
                            "Escalation step skipped or exhausted",
                            extra={"alert_id": alert_id, "step": next_step}
                        )

                except Exception as exc:
                    logger.error(
                        "Error processing escalation for alert %s: %s",
                        alert_id,
                        exc,
                        exc_info=True
                    )
                    await session.rollback()

    def _extract_step_from_notification(self, notification) -> int:
        """
        Extract current escalation step from notification.
        
        This is a heuristic based on notification ID format:
        escal-{alert_id}-step{step}-...
        """
        notification_id = notification.notification_id
        try:
            if "-step" in notification_id:
                parts = notification_id.split("-step")
                if len(parts) > 1:
                    step_part = parts[1].split("-")[0]
                    return int(step_part)
        except (ValueError, IndexError):
            pass

        # Default to step 1 if we can't determine
        return 1

