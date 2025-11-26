"""Evidence and receipt emission helpers."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from ..clients import ErisClient


class EvidenceService:
    """Wrapper around ERIS receipts to centralise evidence emission."""

    def __init__(self, eris_client: Optional[ErisClient] = None):
        self.eris = eris_client or ErisClient()

    async def record_event(
        self,
        event_type: str,
        tenant_id: str,
        actor: Optional[str] = None,
        alert_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit an evidence receipt for a lifecycle event."""
        payload: Dict[str, Any] = {
            "type": event_type,
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if actor:
            payload["actor"] = actor
        if alert_id:
            payload["alert_id"] = alert_id
        if metadata:
            payload["metadata"] = metadata
        try:
            await self.eris.emit_receipt(payload)
        except Exception:
            # ERIS failures should not block alert processing
            # Log error but don't raise
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to emit ERIS receipt (non-blocking)", exc_info=True)

    async def record_meta_access(
        self,
        actor: str,
        actor_roles: list[str],
        tenant_id: str,
        endpoint: str,
        method: str,
    ) -> None:
        """Emit meta-receipt for cross-tenant access."""
        payload = {
            "type": "meta_access",
            "actor": actor,
            "actor_roles": actor_roles,
            "tenant_id": tenant_id,
            "endpoint": endpoint,
            "method": method,
            "timestamp": datetime.utcnow().isoformat(),
        }
        try:
            await self.eris.emit_receipt(payload)
        except Exception:
            # ERIS failures should not block alert processing
            # Log error but don't raise
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to emit ERIS meta-receipt (non-blocking)", exc_info=True)

