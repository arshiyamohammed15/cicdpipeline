"""
Dead Letter Queue (DLQ) handler for Signal Ingestion & Normalization (SIN) Module.

What: Error handling and DLQ per PRD F8
Why: Handle permanent failures and provide audit trail
Reads/Writes: DLQ storage (in-memory, can be replaced with persistent storage)
Contracts: PRD §4.8 (F8)
Risks: DLQ growth, reprocessing failures, DecisionReceipt emission failures
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from .models import SignalEnvelope, DLQEntry, ErrorCode
from .dependencies import MockM32Trust

logger = logging.getLogger(__name__)

# Per PRD F8: Maximum retry attempts before routing to DLQ
MAX_RETRY_ATTEMPTS = 3


class DLQHandler:
    """
    Dead Letter Queue handler per F8.

    Per PRD F8:
    - Store permanently failed signals in DLQ
    - Emit DecisionReceipts for governance violations and DLQ threshold crossings
    - Provide DLQ inspection APIs
    - Support reprocessing
    """

    def __init__(self, trust: Optional[MockM32Trust] = None):
        """
        Initialize DLQ handler.

        Args:
            trust: Trust module dependency for DecisionReceipt emission
        """
        self.trust = trust or MockM32Trust()
        # In-memory DLQ storage: dlq_id -> DLQEntry
        self.dlq_entries: Dict[str, DLQEntry] = {}
        # Track retry attempts: signal_id -> retry_count
        self.retry_counts: Dict[str, int] = {}
        # DLQ threshold for DecisionReceipt emission
        self.dlq_threshold = 100  # Emit receipt when DLQ size exceeds this

    def should_retry(self, signal_id: str) -> bool:
        """
        Check if signal should be retried.

        Args:
            signal_id: Signal ID

        Returns:
            True if should retry, False otherwise
        """
        retry_count = self.retry_counts.get(signal_id, 0)
        return retry_count < MAX_RETRY_ATTEMPTS

    def record_retry(self, signal_id: str) -> int:
        """
        Record retry attempt.

        Args:
            signal_id: Signal ID

        Returns:
            New retry count
        """
        self.retry_counts[signal_id] = self.retry_counts.get(signal_id, 0) + 1
        return self.retry_counts[signal_id]

    def add_to_dlq(self, signal: SignalEnvelope, error_code: ErrorCode, error_message: str,
                    original_signal: Optional[Dict[str, Any]] = None) -> str:
        """
        Add signal to DLQ per F8.

        Args:
            signal: SignalEnvelope that failed
            error_code: Error code
            error_message: Error message
            original_signal: Original signal data (already redacted)

        Returns:
            DLQ entry ID
        """
        dlq_id = f"dlq_{uuid.uuid4().hex[:16]}"
        retry_count = self.retry_counts.get(signal.signal_id, 0)

        # Get first failure timestamp (if this is first failure, use now)
        first_failure_timestamp = datetime.utcnow()
        if signal.signal_id in self.retry_counts:
            # Try to get from existing DLQ entry if reprocessed
            existing_entry = self._find_entry_by_signal_id(signal.signal_id)
            if existing_entry:
                first_failure_timestamp = existing_entry.first_failure_timestamp

        # Create DLQ entry
        entry = DLQEntry(
            dlq_id=dlq_id,
            signal_id=signal.signal_id,
            tenant_id=signal.tenant_id,
            producer_id=signal.producer_id,
            signal_type=signal.signal_type,
            original_signal=original_signal or signal.model_dump(),
            error_code=error_code,
            error_message=error_message,
            first_failure_timestamp=first_failure_timestamp,
            retry_count=retry_count,
            created_at=datetime.utcnow()
        )

        self.dlq_entries[dlq_id] = entry

        # Emit DecisionReceipt for governance violations per F8
        if error_code == ErrorCode.GOVERNANCE_VIOLATION:
            self._emit_governance_receipt(signal, error_code, error_message)

        # Emit DecisionReceipt for DLQ threshold crossing per F8
        if len(self.dlq_entries) >= self.dlq_threshold:
            self._emit_dlq_threshold_receipt()

        logger.warning(f"Signal added to DLQ: {dlq_id} (signal_id: {signal.signal_id}, error: {error_code})")
        return dlq_id

    def _find_entry_by_signal_id(self, signal_id: str) -> Optional[DLQEntry]:
        """Find DLQ entry by signal ID."""
        for entry in self.dlq_entries.values():
            if entry.signal_id == signal_id:
                return entry
        return None

    def _emit_governance_receipt(self, signal: SignalEnvelope, error_code: ErrorCode, error_message: str) -> None:
        """
        Emit DecisionReceipt for governance violation per F8.

        Args:
            signal: SignalEnvelope
            error_code: Error code
            error_message: Error message
        """
        receipt_data = {
            'decision_type': 'governance_violation',
            'module': 'SIN',
            'tenant_id': signal.tenant_id,
            'producer_id': signal.producer_id,
            'signal_id': signal.signal_id,
            'signal_type': signal.signal_type,
            'error_code': error_code.value,
            'error_message': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }

        receipt_id = self.trust.emit_receipt(receipt_data)
        logger.info(f"DecisionReceipt emitted for governance violation: {receipt_id}")

    def _emit_dlq_threshold_receipt(self) -> None:
        """Emit DecisionReceipt for DLQ threshold crossing per F8."""
        receipt_data = {
            'decision_type': 'dlq_threshold_crossed',
            'module': 'SIN',
            'dlq_size': len(self.dlq_entries),
            'threshold': self.dlq_threshold,
            'timestamp': datetime.utcnow().isoformat()
        }

        receipt_id = self.trust.emit_receipt(receipt_data)
        logger.warning(f"DecisionReceipt emitted for DLQ threshold crossing: {receipt_id}")

    def get_dlq_entry(self, dlq_id: str) -> Optional[DLQEntry]:
        """
        Get DLQ entry by ID.

        Args:
            dlq_id: DLQ entry ID

        Returns:
            DLQEntry or None if not found
        """
        return self.dlq_entries.get(dlq_id)

    def list_dlq_entries(self, tenant_id: Optional[str] = None, producer_id: Optional[str] = None,
                         signal_type: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[DLQEntry]:
        """
        List DLQ entries with filters.

        Args:
            tenant_id: Filter by tenant ID
            producer_id: Filter by producer ID
            signal_type: Filter by signal type
            limit: Maximum number of entries
            offset: Offset for pagination

        Returns:
            List of DLQEntry
        """
        entries = list(self.dlq_entries.values())

        # Apply filters
        if tenant_id:
            entries = [e for e in entries if e.tenant_id == tenant_id]
        if producer_id:
            entries = [e for e in entries if e.producer_id == producer_id]
        if signal_type:
            entries = [e for e in entries if e.signal_type == signal_type]

        # Sort by created_at (newest first)
        entries.sort(key=lambda e: e.created_at, reverse=True)

        # Apply pagination
        return entries[offset:offset + limit]

    def reprocess_dlq_entry(self, dlq_id: str) -> tuple[bool, Optional[str]]:
        """
        Mark DLQ entry for reprocessing.

        Args:
            dlq_id: DLQ entry ID

        Returns:
            (success, error_message) tuple
        """
        entry = self.dlq_entries.get(dlq_id)
        if not entry:
            return False, f"DLQ entry {dlq_id} not found"

        # Reset retry count
        self.retry_counts[entry.signal_id] = 0

        # Remove from DLQ (will be reprocessed)
        del self.dlq_entries[dlq_id]

        logger.info(f"DLQ entry marked for reprocessing: {dlq_id}")
        return True, None

    def get_dlq_stats(self) -> Dict[str, Any]:
        """
        Get DLQ statistics.

        Returns:
            Statistics dictionary
        """
        total_entries = len(self.dlq_entries)
        by_error_code: Dict[str, int] = {}
        by_tenant: Dict[str, int] = {}
        by_producer: Dict[str, int] = {}

        for entry in self.dlq_entries.values():
            # Count by error code
            error_code = entry.error_code.value
            by_error_code[error_code] = by_error_code.get(error_code, 0) + 1

            # Count by tenant
            by_tenant[entry.tenant_id] = by_tenant.get(entry.tenant_id, 0) + 1

            # Count by producer
            by_producer[entry.producer_id] = by_producer.get(entry.producer_id, 0) + 1

        return {
            'total_entries': total_entries,
            'by_error_code': by_error_code,
            'by_tenant': by_tenant,
            'by_producer': by_producer,
            'threshold': self.dlq_threshold,
            'threshold_exceeded': total_entries >= self.dlq_threshold
        }

