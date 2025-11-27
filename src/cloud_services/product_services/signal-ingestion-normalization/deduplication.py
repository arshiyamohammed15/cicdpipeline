"""
Deduplication store for Signal Ingestion & Normalization (SIN) Module.

What: Idempotency and deduplication engine per PRD F7
Why: Process signals safely in at-least-once delivery environment
Reads/Writes: In-memory deduplication store (time-bounded)
Contracts: PRD §4.7 (F7)
Risks: Memory growth if deduplication window too long, requires distributed store for horizontal scaling
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set, Tuple, Any

from .models import SignalEnvelope

logger = logging.getLogger(__name__)

# Per PRD §7.1: Minimum 24-hour deduplication window
DEFAULT_DEDUP_WINDOW_HOURS = 24


class DeduplicationStore:
    """
    Deduplication store for signal idempotency per F7.

    Per PRD F7:
    - Treat signal_id + producer_id as idempotency key (plus optional sequence_no)
    - Maintain short-term deduplication store (time-bounded)
    - Preserve ordering per producer/stream where required
    """

    def __init__(self, dedup_window_hours: int = DEFAULT_DEDUP_WINDOW_HOURS):
        """
        Initialize deduplication store.

        Args:
            dedup_window_hours: Deduplication window in hours (default: 24)
        """
        self.dedup_window_hours = dedup_window_hours
        # Store: key -> (processed_at, sequence_no)
        self.processed_keys: Dict[str, Tuple[datetime, Optional[int]]] = {}
        # Track sequence numbers per producer for ordering
        self.producer_sequences: Dict[str, int] = {}
        # Metrics
        self.duplicates_received = 0
        self.duplicates_discarded = 0

    def _make_key(self, signal_id: str, producer_id: str, sequence_no: Optional[int] = None) -> str:
        """
        Create idempotency key.

        Args:
            signal_id: Signal ID
            producer_id: Producer ID
            sequence_no: Optional sequence number

        Returns:
            Idempotency key string
        """
        if sequence_no is not None:
            return f"{signal_id}:{producer_id}:{sequence_no}"
        return f"{signal_id}:{producer_id}"

    def _cleanup_expired(self):
        """Remove expired entries from deduplication store."""
        now = datetime.utcnow()
        expired_keys = [
            key for key, (processed_at, _) in self.processed_keys.items()
            if now - processed_at > timedelta(hours=self.dedup_window_hours)
        ]
        for key in expired_keys:
            del self.processed_keys[key]

    def is_duplicate(self, signal: SignalEnvelope) -> bool:
        """
        Check if signal is a duplicate.

        Args:
            signal: SignalEnvelope to check

        Returns:
            True if duplicate, False otherwise
        """
        self._cleanup_expired()

        key = self._make_key(signal.signal_id, signal.producer_id, signal.sequence_no)

        if key in self.processed_keys:
            self.duplicates_received += 1
            self.duplicates_discarded += 1
            logger.debug(f"Duplicate signal detected: {key}")
            return True

        return False

    def mark_processed(self, signal: SignalEnvelope) -> None:
        """
        Mark signal as processed.

        Args:
            signal: SignalEnvelope that was processed
        """
        self._cleanup_expired()

        key = self._make_key(signal.signal_id, signal.producer_id, signal.sequence_no)
        now = datetime.utcnow()

        self.processed_keys[key] = (now, signal.sequence_no)

        # Track sequence numbers for ordering
        if signal.sequence_no is not None:
            producer_key = signal.producer_id
            if producer_key not in self.producer_sequences:
                self.producer_sequences[producer_key] = signal.sequence_no
            else:
                # Update to latest sequence number seen
                if signal.sequence_no > self.producer_sequences[producer_key]:
                    self.producer_sequences[producer_key] = signal.sequence_no

    def check_ordering(self, signal: SignalEnvelope) -> Tuple[bool, Optional[str]]:
        """
        Check if signal is in order (if sequence_no is provided).

        Args:
            signal: SignalEnvelope to check

        Returns:
            (in_order, warning_message) tuple
        """
        if signal.sequence_no is None:
            return True, None

        # Validate sequence number is positive
        if signal.sequence_no < 0:
            warning = f"Invalid sequence_no: {signal.sequence_no} is negative"
            logger.warning(warning)
            return False, warning

        # Validate sequence number is within reasonable range (prevent overflow issues)
        # Maximum sequence number: 2^63 - 1 (signed 64-bit integer)
        MAX_SEQUENCE_NO = 9223372036854775807
        if signal.sequence_no > MAX_SEQUENCE_NO:
            warning = f"Invalid sequence_no: {signal.sequence_no} exceeds maximum {MAX_SEQUENCE_NO}"
            logger.warning(warning)
            return False, warning

        producer_key = signal.producer_id
        last_sequence = self.producer_sequences.get(producer_key)

        if last_sequence is None:
            # First signal from this producer
            return True, None

        if signal.sequence_no <= last_sequence:
            warning = f"Out-of-order signal: sequence_no {signal.sequence_no} <= last {last_sequence}"
            return False, warning

        return True, None

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get deduplication metrics.

        Returns:
            Metrics dictionary
        """
        self._cleanup_expired()
        return {
            'processed_keys_count': len(self.processed_keys),
            'duplicates_received': self.duplicates_received,
            'duplicates_discarded': self.duplicates_discarded,
            'producer_sequences_tracked': len(self.producer_sequences),
            'dedup_window_hours': self.dedup_window_hours
        }

    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self.duplicates_received = 0
        self.duplicates_discarded = 0

