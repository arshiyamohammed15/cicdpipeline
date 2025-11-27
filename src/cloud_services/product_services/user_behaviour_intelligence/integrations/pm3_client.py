"""
PM-3 (Signal Ingestion & Normalization) Integration Client for UBI Module (EPC-9).

What: Client for subscribing to PM-3 routing classes and consuming SignalEnvelope events
Why: Enable event consumption per PRD FR-1
Reads/Writes: Event consumption from PM-3 routing classes
Contracts: PM-3 PRD Section 4.6 (F6) - Routing & Fan-Out
Risks: PM-3 unavailability, event ordering issues, duplicate events
"""

import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


class PM3Client:
    """
    PM-3 client for event consumption.

    Per UBI PRD FR-1:
    - Subscribe to PM-3 routing classes (realtime_detection or analytics_store)
    - Handle at-least-once delivery
    - Handle out-of-order events
    - Use signal_id as idempotency key
    """

    def __init__(
        self,
        routing_class: str = "analytics_store",
        dedup_window_hours: int = 24
    ):
        """
        Initialize PM-3 client.

        Args:
            routing_class: PM-3 routing class to subscribe to (realtime_detection or analytics_store)
            dedup_window_hours: Deduplication window in hours
        """
        self.routing_class = routing_class
        self.dedup_window_hours = dedup_window_hours
        
        # Deduplication store: signal_id -> processed_at
        self.processed_signals: Dict[str, datetime] = {}
        
        # Out-of-order event buffer: keyed by occurred_at timestamp
        self.event_buffer: deque = deque()
        self.buffer_window_seconds = 300  # 5 minutes buffer for out-of-order events
        
        # Event handler callback
        self.event_handler: Optional[Callable] = None
        
        # Metrics
        self.events_received = 0
        self.events_processed = 0
        self.duplicates_discarded = 0
        self.out_of_order_handled = 0

    def subscribe(
        self,
        handler: Callable[[Dict[str, Any]], bool],
        routing_class: Optional[str] = None
    ) -> None:
        """
        Subscribe to PM-3 routing class.

        Args:
            handler: Event handler function that takes SignalEnvelope dict and returns success bool
            routing_class: Override default routing class
        """
        self.event_handler = handler
        if routing_class:
            self.routing_class = routing_class
        
        logger.info(f"Subscribed to PM-3 routing class: {self.routing_class}")

    def consume_signal(self, signal_envelope: Dict[str, Any]) -> bool:
        """
        Consume SignalEnvelope from PM-3.

        Args:
            signal_envelope: SignalEnvelope dictionary from PM-3

        Returns:
            True if processed successfully, False otherwise
        """
        self.events_received += 1
        
        signal_id = signal_envelope.get("signal_id")
        if not signal_id:
            logger.error("SignalEnvelope missing signal_id")
            return False
        
        # Check for duplicates (idempotency)
        if self._is_duplicate(signal_id):
            self.duplicates_discarded += 1
            logger.debug(f"Duplicate signal discarded: {signal_id}")
            return True  # Return True because duplicate handling is successful
        
        # Handle out-of-order events
        occurred_at_str = signal_envelope.get("occurred_at")
        if occurred_at_str:
            try:
                occurred_at = datetime.fromisoformat(occurred_at_str.replace('Z', '+00:00'))
                if self._is_out_of_order(occurred_at):
                    self._buffer_event(signal_envelope)
                    self.out_of_order_handled += 1
                    return True  # Buffered for later processing
            except Exception as e:
                logger.warning(f"Error parsing occurred_at: {e}")
        
        # Process event
        return self._process_event(signal_envelope)

    def _is_duplicate(self, signal_id: str) -> bool:
        """
        Check if signal is duplicate.

        Args:
            signal_id: Signal identifier

        Returns:
            True if duplicate, False otherwise
        """
        # Cleanup expired entries
        self._cleanup_expired()
        
        if signal_id in self.processed_signals:
            return True
        
        return False

    def _cleanup_expired(self) -> None:
        """Remove expired entries from deduplication store."""
        now = datetime.utcnow()
        expired_keys = [
            key for key, processed_at in self.processed_signals.items()
            if now - processed_at > timedelta(hours=self.dedup_window_hours)
        ]
        for key in expired_keys:
            del self.processed_signals[key]

    def _is_out_of_order(self, occurred_at: datetime) -> bool:
        """
        Check if event is out of order.

        Args:
            occurred_at: Event occurred timestamp

        Returns:
            True if out of order, False otherwise
        """
        now = datetime.utcnow(occurred_at.tzinfo) if occurred_at.tzinfo else datetime.utcnow()
        time_diff = (now - occurred_at).total_seconds()
        
        # If event is more than buffer_window_seconds in the future, it's out of order
        return time_diff < -self.buffer_window_seconds

    def _buffer_event(self, signal_envelope: Dict[str, Any]) -> None:
        """
        Buffer out-of-order event for later processing.

        Args:
            signal_envelope: SignalEnvelope dictionary
        """
        occurred_at_str = signal_envelope.get("occurred_at")
        if occurred_at_str:
            try:
                occurred_at = datetime.fromisoformat(occurred_at_str.replace('Z', '+00:00'))
                self.event_buffer.append((occurred_at, signal_envelope))
                # Sort buffer by occurred_at
                self.event_buffer = deque(sorted(self.event_buffer, key=lambda x: x[0]))
                logger.debug(f"Buffered out-of-order event: {signal_envelope.get('signal_id')}")
            except Exception as e:
                logger.warning(f"Error buffering event: {e}")

    def _process_event(self, signal_envelope: Dict[str, Any]) -> bool:
        """
        Process event through handler.

        Args:
            signal_envelope: SignalEnvelope dictionary

        Returns:
            True if processed successfully, False otherwise
        """
        if not self.event_handler:
            logger.error("No event handler registered")
            return False
        
        try:
            success = self.event_handler(signal_envelope)
            if success:
                signal_id = signal_envelope.get("signal_id")
                if signal_id:
                    self.processed_signals[signal_id] = datetime.utcnow()
                self.events_processed += 1
            return success
        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)
            return False

    def process_buffered_events(self) -> int:
        """
        Process buffered events that are now in order.

        Returns:
            Number of events processed
        """
        now = datetime.utcnow()
        processed_count = 0
        
        while self.event_buffer:
            occurred_at, signal_envelope = self.event_buffer[0]
            
            # Check if event is now in order (not too far in the future)
            time_diff = (now - occurred_at).total_seconds()
            if time_diff >= -self.buffer_window_seconds:
                self.event_buffer.popleft()
                if self._process_event(signal_envelope):
                    processed_count += 1
            else:
                # Remaining events are still out of order
                break
        
        return processed_count

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get client metrics.

        Returns:
            Metrics dictionary
        """
        self._cleanup_expired()
        return {
            "routing_class": self.routing_class,
            "events_received": self.events_received,
            "events_processed": self.events_processed,
            "duplicates_discarded": self.duplicates_discarded,
            "out_of_order_handled": self.out_of_order_handled,
            "buffered_events": len(self.event_buffer),
            "processed_signals_count": len(self.processed_signals),
            "dedup_window_hours": self.dedup_window_hours
        }

