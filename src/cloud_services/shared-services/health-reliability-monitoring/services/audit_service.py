"""
Audit and meta-receipt utilities for Health & Reliability Monitoring.

Ensures sensitive queries are captured and relayed to ERIS.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from .event_bus_service import EventBusService


class AuditService:
    """Provides helper for emitting meta-audit receipts."""

    def __init__(self, event_bus: EventBusService) -> None:
        self._event_bus = event_bus

    async def record_access(self, actor: Dict[str, str], resource: str, action: str) -> None:
        """Emit meta-audit record per FR-9."""
        payload = {
            "actor": actor,
            "resource": resource,
            "action": action,
            "observed_at": datetime.utcnow().isoformat(),
        }
        await self._event_bus.emit_receipt(payload, action="meta_audit")

