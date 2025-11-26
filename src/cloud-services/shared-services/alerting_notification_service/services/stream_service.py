"""Alert streaming service for agent consumption."""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from ..database.models import Alert
from ..observability.metrics import STREAM_SUBSCRIBERS


class StreamFilter:
    """Filter criteria for alert streams."""

    def __init__(
        self,
        tenant_ids: Optional[List[str]] = None,
        component_ids: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        severities: Optional[List[str]] = None,
        labels: Optional[Dict[str, str]] = None,
        event_types: Optional[List[str]] = None,
    ):
        self.tenant_ids = set(tenant_ids) if tenant_ids else None
        self.component_ids = set(component_ids) if component_ids else None
        self.categories = set(categories) if categories else None
        self.severities = set(severities) if severities else None
        self.labels = labels or {}
        self.event_types = set(event_types) if event_types else None

    def matches(self, alert: Alert, event_type: str = "alert.created") -> bool:
        """Check if alert matches filter criteria."""
        if self.tenant_ids and alert.tenant_id not in self.tenant_ids:
            return False
        if self.component_ids and alert.component_id not in self.component_ids:
            return False
        if self.categories and alert.category not in self.categories:
            return False
        if self.severities and alert.severity not in self.severities:
            return False
        if self.event_types and event_type not in self.event_types:
            return False
        if self.labels:
            alert_labels = alert.labels or {}
            for key, value in self.labels.items():
                if alert_labels.get(key) != value:
                    return False
        return True

    def matches_dict(self, alert_dict: Dict[str, Any], event_type: str = "alert.created") -> bool:
        """Check if alert dict matches filter criteria."""
        if self.tenant_ids and alert_dict.get("tenant_id") not in self.tenant_ids:
            return False
        if self.component_ids and alert_dict.get("component_id") not in self.component_ids:
            return False
        if self.categories and alert_dict.get("category") not in self.categories:
            return False
        if self.severities and alert_dict.get("severity") not in self.severities:
            return False
        if self.event_types and event_type not in self.event_types:
            return False
        if self.labels:
            alert_labels = alert_dict.get("labels", {})
            for key, value in self.labels.items():
                if alert_labels.get(key) != value:
                    return False
        return True


class AlertStreamService:
    """Service for publishing alerts to streams for agent consumption."""

    def __init__(self):
        # In-memory subscribers (in production, this would use a message bus)
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()
        STREAM_SUBSCRIBERS.set(0)

    async def subscribe(
        self,
        subscription_id: str,
        filter_criteria: Optional[StreamFilter] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Subscribe to alert stream with optional filtering.
        
        Args:
            subscription_id: Unique identifier for this subscription
            filter_criteria: Optional filter to apply to alerts
        
        Yields:
            Alert events in machine-readable JSON format
        """
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subscribers[subscription_id].append(queue)
            STREAM_SUBSCRIBERS.inc()

        try:
            while True:
                try:
                    # Wait for alert event with timeout for heartbeat
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    if event is None:  # Shutdown signal
                        break

                    # Apply filter if provided
                    if filter_criteria:
                        alert_dict = event.get("alert")
                        event_type = event.get("event_type", "alert.created")
                        if alert_dict and not filter_criteria.matches_dict(alert_dict, event_type):
                            continue

                    yield event
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield {
                        "event_type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
        finally:
            async with self._lock:
                if subscription_id in self._subscribers:
                    self._subscribers[subscription_id].remove(queue)
                    if not self._subscribers[subscription_id]:
                        del self._subscribers[subscription_id]
                    STREAM_SUBSCRIBERS.dec()

    async def publish_alert(self, alert: Alert, event_type: str = "alert.created", metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Publish alert event to all subscribers.
        
        Args:
            alert: Alert to publish
            event_type: Type of event (alert.created, alert.updated, alert.acknowledged, alert.resolved, etc.)
            metadata: Optional additional metadata
        """
        event = self._format_alert_event(alert, event_type, metadata)
        async with self._lock:
            for queues in self._subscribers.values():
                for queue in queues:
                    try:
                        queue.put_nowait(event)
                    except asyncio.QueueFull:
                        # Skip if queue is full (backpressure)
                        pass

    def _format_alert_event(self, alert: Alert, event_type: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format alert as machine-readable event."""
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "alert": {
                "alert_id": alert.alert_id,
                "schema_version": alert.schema_version,
                "tenant_id": alert.tenant_id,
                "source_module": alert.source_module,
                "plane": alert.plane,
                "environment": alert.environment,
                "component_id": alert.component_id,
                "severity": alert.severity,
                "priority": alert.priority,
                "category": alert.category,
                "summary": alert.summary,
                "description": alert.description,
                "labels": alert.labels or {},
                "started_at": alert.started_at.isoformat() if alert.started_at else None,
                "ended_at": alert.ended_at.isoformat() if alert.ended_at else None,
                "last_seen_at": alert.last_seen_at.isoformat() if alert.last_seen_at else None,
                "dedup_key": alert.dedup_key,
                "incident_id": alert.incident_id,
                "policy_refs": alert.policy_refs or [],
                "status": alert.status,
                "links": alert.links or [],
                "runbook_refs": alert.runbook_refs or [],
                "automation_hooks": alert.automation_hooks or [],
                "component_metadata": alert.component_metadata or {},
                "slo_snapshot_url": alert.slo_snapshot_url,
            },
        }
        if metadata:
            event["metadata"] = metadata
        return event

    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from alert stream."""
        async with self._lock:
            if subscription_id in self._subscribers:
                # Send shutdown signal to all queues
                for queue in self._subscribers[subscription_id]:
                    try:
                        queue.put_nowait(None)
                    except asyncio.QueueFull:
                        pass
                del self._subscribers[subscription_id]

    def subscriber_count(self) -> int:
        """Return number of active subscribers."""
        return sum(len(queues) for queues in self._subscribers.values())


# Global stream service instance
_stream_service: Optional[AlertStreamService] = None


def get_stream_service() -> AlertStreamService:
    """Get or create global stream service instance."""
    global _stream_service
    if _stream_service is None:
        _stream_service = AlertStreamService()
    return _stream_service

