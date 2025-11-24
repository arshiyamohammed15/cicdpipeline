"""
Event publishing helpers for Health & Reliability Monitoring.

Wraps alerting + ERIS clients to emit health transitions and evidence receipts.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict

from ..dependencies import AlertingClient, ERISClient

logger = logging.getLogger(__name__)


class EventBusService:
    """Facilitates publishing events to EPC-4 and ERIS."""

    def __init__(self, alerting_client: AlertingClient, eris_client: ERISClient) -> None:
        self._alerting = alerting_client
        self._eris = eris_client

    async def emit_health_transition(self, snapshot: Dict[str, str]) -> None:
        """Send health state change event."""
        payload = {
            "occurred_at": datetime.utcnow().isoformat(),
            **snapshot,
        }
        await self._alerting.publish(payload)

    async def emit_receipt(self, snapshot: Dict[str, str], action: str) -> str:
        """Emit ERIS receipt for audit events."""
        receipt = {
            "action": action,
            "snapshot": snapshot,
            "issued_at": datetime.utcnow().isoformat(),
        }
        receipt_id = await self._eris.emit_receipt(receipt)
        logger.debug("Emitted receipt", extra={"receipt_id": receipt_id})
        return receipt_id

