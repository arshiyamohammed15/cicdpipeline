"""
Signal bus client abstraction for MMM Engine.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable, Deque, Dict, Optional, Any

from ..models import MMMSignalInput, ActorType

logger = logging.getLogger(__name__)

SignalHandler = Callable[[MMMSignalInput], Awaitable[None]]


@dataclass
class SignalEnvelope:
    signal_id: str
    tenant_id: str
    source: str
    event_type: str
    occurred_at: datetime
    payload: Dict
    actor_id: Optional[str] = None
    actor_type: Optional[str] = None
    severity: Optional[str] = None

    def to_mmm_signal(self) -> MMMSignalInput:
        return MMMSignalInput(
            signal_id=self.signal_id,
            tenant_id=self.tenant_id,
            actor_id=self.actor_id,
            actor_type=ActorType(self.actor_type) if self.actor_type else ActorType.HUMAN,
            source=self.source,
            event_type=self.event_type,
            severity=self.severity,
            occurred_at=self.occurred_at,
            payload=self.payload,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignalEnvelope":
        """Create envelope from PM-3 normalized signal payload."""
        return cls(
            signal_id=str(data.get("signal_id") or data.get("id") or data.get("uuid")),
            tenant_id=data.get("tenant_id") or data.get("tenant", ""),
            source=data.get("source") or data.get("source_system") or "pm3",
            event_type=data.get("event_type") or data.get("signal_type") or "unknown",
            occurred_at=datetime.fromisoformat(
                (data.get("occurred_at") or data.get("timestamp") or datetime.utcnow().isoformat())
                .replace("Z", "+00:00")
            ),
            payload=data.get("payload") or data,
            actor_id=data.get("actor_id"),
            actor_type=data.get("actor_type"),
            severity=data.get("severity"),
        )


class SignalBusClient:
    """
    In-memory signal bus abstraction. Production deployments will replace this with Kafka/RabbitMQ integrations.
    """

    def __init__(self) -> None:
        self.queue: Deque[SignalEnvelope] = deque()
        self.handlers: list[SignalHandler] = []

    def register_handler(self, handler: SignalHandler) -> None:
        self.handlers.append(handler)

    async def publish(self, envelope: SignalEnvelope) -> None:
        logger.debug("SignalBus publish %s", envelope.signal_id)
        self.queue.append(envelope)
        await self._drain()

    async def _drain(self) -> None:
        while self.queue:
            envelope = self.queue.popleft()
            signal = envelope.to_mmm_signal()
            for handler in self.handlers:
                try:
                    await handler(signal)
                except Exception as exc:  # pragma: no cover
                    logger.exception("Signal handler failed: %s", exc)


