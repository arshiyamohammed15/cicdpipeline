"""
Event Subscription Service for M35.

What: Manages CRUD operations for event subscriptions.
Why: Supports Event Subscription API per PRD.
Reads/Writes: Stores subscription metadata (mock in-memory / M29-backed).
Contracts: Event subscription API contract.
Risks: Missing persistence, invalid webhook configuration.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from ..dependencies import MockM29DataPlane


class EventSubscriptionService:
    """Service handling event subscription CRUD operations."""

    def __init__(self, data_plane: Optional[MockM29DataPlane] = None):
        self.data_plane = data_plane
        self._subscriptions: Dict[str, Dict[str, Any]] = {}

    def _store_subscription(self, subscription: Dict[str, Any]) -> None:
        self._subscriptions[subscription["subscription_id"]] = subscription
        if self.data_plane:
            self.data_plane.store(
                f"event_subscription:{subscription['subscription_id']}",
                subscription
            )

    def create_subscription(
        self,
        tenant_id: str,
        event_types: List[str],
        webhook_url: str,
        filters: Optional[Dict[str, Any]] = None,
        enabled: bool = True
    ) -> Dict[str, Any]:
        subscription_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        subscription = {
            "subscription_id": subscription_id,
            "tenant_id": tenant_id,
            "event_types": event_types,
            "webhook_url": webhook_url,
            "filters": filters or {},
            "enabled": enabled,
            "created_at": now,
            "updated_at": now
        }
        self._store_subscription(subscription)
        return subscription

    def list_subscriptions(
        self,
        tenant_id: str,
        page: int,
        page_size: int
    ) -> Tuple[List[Dict[str, Any]], int]:
        subs = [
            sub for sub in self._subscriptions.values()
            if sub["tenant_id"] == tenant_id
        ]
        total = len(subs)
        start = (page - 1) * page_size
        end = start + page_size
        return subs[start:end], total

    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        if subscription_id in self._subscriptions:
            return self._subscriptions[subscription_id]
        if self.data_plane:
            stored = self.data_plane.get(f"event_subscription:{subscription_id}")
            if stored:
                self._subscriptions[subscription_id] = stored
            return stored
        return None

    def update_subscription(
        self,
        subscription_id: str,
        **updates: Any
    ) -> Optional[Dict[str, Any]]:
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return None
        for key, value in updates.items():
            if value is not None:
                subscription[key] = value
        subscription["updated_at"] = datetime.utcnow().isoformat() + "Z"
        self._store_subscription(subscription)
        return subscription

    def delete_subscription(self, subscription_id: str) -> bool:
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return False
        self._subscriptions.pop(subscription_id, None)
        if self.data_plane:
            self.data_plane.store(f"event_subscription:{subscription_id}", None)
        return True

