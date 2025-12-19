"""Durable write-ahead log queues for courier batching with deep-copy and receipt emission."""

from __future__ import annotations

import copy
import json
import logging
import os
import threading
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Callable, Deque, Dict, Iterable, Optional

logger = logging.getLogger(__name__)

# CR-025, CR-032: Maximum payload size (10MB)
MAX_PAYLOAD_SIZE_BYTES = 10 * 1024 * 1024
# CR-030: Maximum number of entries before cleanup
MAX_ENTRIES_BEFORE_CLEANUP = 10000


@dataclass
class WALEntry:
    """WAL entry with sequence, payload (deep-copied), and state."""

    sequence: int
    payload: Dict[str, Any]
    state: str = "pending"
    entry_type: str = "receipt"  # receipt, budget, policy_snapshot


class WALQueue:
    """
    Hardened WAL-backed queue with deep-copy payloads and receipt emission.

    Features:
    - Deep-copy all payloads to prevent mutation
    - Persist budgets and policy snapshots
    - Emit pending_sync and dead_letter receipts
    - Fsync for durability
    """

    def __init__(self, path: Path):
        self._path = path
        self._entries: Deque[WALEntry] = deque()
        self._sequence = 0
        # CR-029: Add lock for concurrent access
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            self._load()

    def _load(self) -> None:
        """Load WAL entries from disk."""
        try:
            with self._path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    entry = WALEntry(
                        sequence=record["sequence"],
                        payload=copy.deepcopy(record["payload"]),  # Deep copy on load
                        state=record.get("state", "pending"),
                        entry_type=record.get("entry_type", "receipt"),
                    )
                    self._entries.append(entry)
                    self._sequence = max(self._sequence, entry.sequence)
        except Exception:
            # If load fails, start fresh
            self._entries = deque()
            self._sequence = 0

    def _persist(self) -> None:
        """Persist WAL entries to disk with fsync."""
        # Write to temporary file first, then rename (atomic)
        temp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        try:
            with temp_path.open("w", encoding="utf-8") as handle:
                for entry in self._entries:
                    handle.write(
                        json.dumps(
                            {
                                "sequence": entry.sequence,
                                "payload": entry.payload,  # Already deep-copied
                                "state": entry.state,
                                "entry_type": entry.entry_type,
                            }
                        )
                        + "\n"
                    )
                handle.flush()
                # CR-028: Ensure fsync before rename for atomic write
                os.fsync(handle.fileno())
            # CR-028: Atomic rename after fsync
            temp_path.replace(self._path)
            # CR-028: Ensure directory is synced for metadata
            # On Windows, directory fsync may fail with permission errors, so we handle it gracefully
            if self._path.parent.exists():
                try:
                    dir_fd = os.open(self._path.parent, os.O_RDONLY)
                    try:
                        os.fsync(dir_fd)
                    finally:
                        os.close(dir_fd)
                except (PermissionError, OSError):
                    # On Windows, directory fsync may not be supported or may require admin privileges
                    # File fsync above is sufficient for data integrity
                    pass
        except Exception:
            # If temp file exists, clean it up
            if temp_path.exists():
                temp_path.unlink()
            raise

    def append(
        self, payload: Dict[str, Any], entry_type: str = "receipt"
    ) -> WALEntry:
        """
        Append entry to WAL with deep-copy.

        Args:
            payload: Payload to append (will be deep-copied)
            entry_type: Type of entry (receipt, budget, policy_snapshot)

        Returns:
            WALEntry with sequence and deep-copied payload
        """
        # CR-032: Validate payload is JSON-serializable
        try:
            json.dumps(payload)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Payload is not JSON-serializable: {e}") from e
        
        # CR-025: Validate payload size
        payload_json = json.dumps(payload)
        payload_size = len(payload_json.encode('utf-8'))
        if payload_size > MAX_PAYLOAD_SIZE_BYTES:
            raise ValueError(f"Payload size {payload_size} exceeds maximum {MAX_PAYLOAD_SIZE_BYTES} bytes")
        
        # CR-029: Use lock for thread-safe access
        with self._lock:
            self._sequence += 1
            # Deep copy payload to prevent mutation
            payload_copy = copy.deepcopy(payload)
            entry = WALEntry(
                sequence=self._sequence,
                payload=payload_copy,
                state="pending",
                entry_type=entry_type,
            )
            self._entries.append(entry)
            # CR-030: Cleanup old entries if deque grows too large
            if len(self._entries) > MAX_ENTRIES_BEFORE_CLEANUP:
                self._cleanup_old_entries()
            self._persist()
        return entry

    def append_budget_snapshot(self, budget_data: Dict[str, Any]) -> WALEntry:
        """
        Persist budget snapshot to WAL.

        Args:
            budget_data: Budget snapshot data (will be deep-copied)

        Returns:
            WALEntry for the budget snapshot
        """
        return self.append(budget_data, entry_type="budget")

    def append_policy_snapshot(self, policy_data: Dict[str, Any]) -> WALEntry:
        """
        Persist policy snapshot to WAL.

        Args:
            policy_data: Policy snapshot data (will be deep-copied)

        Returns:
            WALEntry for the policy snapshot
        """
        return self.append(policy_data, entry_type="policy_snapshot")

    def mark(self, sequence: int, state: str) -> None:
        """
        Mark entry state (pending, acked, pending_sync, dead_letter).

        Args:
            sequence: Entry sequence number
            state: New state
        """
        # CR-029: Use lock for thread-safe access
        with self._lock:
            for entry in self._entries:
                if entry.sequence == sequence:
                    entry.state = state
                    break
            self._persist()

    def drain(
        self,
        sink: Callable[[Dict[str, Any]], None],
        receipt_emitter: Optional[Callable[[Dict[str, Any]], None]] = None,
        entry_filter: Optional[Callable[[WALEntry], bool]] = None,
    ) -> Iterable[WALEntry]:
        """
        Drain pending entries to sink, emitting receipts for failures.

        Per PRD ??7.1: Nothing is dropped without an explicit dead_letter receipt.

        Args:
            sink: Callback to process entries
            receipt_emitter: Optional callback to emit dead_letter receipts
            entry_filter: Optional predicate to select entries for draining

        Returns:
            Iterable of drained entries
        """
        drained: list[WALEntry] = []
        # Mark entries as processing under lock to avoid duplicate drains.
        with self._lock:
            pending_entries = [e for e in self._entries if e.state == "pending"]
            if entry_filter:
                pending_entries = [e for e in pending_entries if entry_filter(e)]
            for entry in pending_entries:
                entry.state = "processing"
            if pending_entries:
                self._persist()

        for entry in pending_entries:
            error: Optional[Exception] = None
            try:
                # Deep copy payload before passing to sink
                payload_copy = copy.deepcopy(entry.payload)
                sink(payload_copy)
                new_state = "acked"
                drained.append(entry)
            except Exception as e:
                new_state = "dead_letter"
                error = e
                logger.error(f"WAL drain failed for entry {entry.sequence}: {e}")

            # Update state under lock; do not call receipt_emitter while holding the lock.
            with self._lock:
                entry.state = new_state
                self._persist()

            if error and receipt_emitter:
                try:
                    dead_letter_receipt = {
                        "receipt_type": "dead_letter",
                        "wal_sequence": entry.sequence,
                        "entry_type": entry.entry_type,
                        "error": str(error),
                        "payload": entry.payload,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    receipt_emitter(dead_letter_receipt)
                except Exception as emit_error:
                    # CR-031: If receipt emitter fails, log but don't change state
                    logger.error(f"Failed to emit dead_letter receipt: {emit_error}")

        with self._lock:
            # Remove only acked entries from queue, keep pending and dead_letter
            self._entries = deque(e for e in self._entries if e.state != "acked")
            # CR-030: Cleanup old dead_letter entries
            self._cleanup_old_entries()
        return drained
    def get_pending_sync_entries(self) -> Iterable[WALEntry]:
        """Get entries marked as pending_sync."""
        return [e for e in self._entries if e.state == "pending_sync"]

    def get_dead_letter_entries(self) -> Iterable[WALEntry]:
        """Get entries marked as dead_letter."""
        return [e for e in self._entries if e.state == "dead_letter"]

    def _cleanup_old_entries(self) -> None:
        """CR-030: Cleanup old dead_letter entries to prevent memory growth."""
        # Keep only last 1000 dead_letter entries
        dead_letter_entries = [e for e in self._entries if e.state == "dead_letter"]
        if len(dead_letter_entries) > 1000:
            # Sort by sequence and keep only most recent
            dead_letter_entries.sort(key=lambda e: e.sequence, reverse=True)
            entries_to_remove = {e.sequence for e in dead_letter_entries[1000:]}
            self._entries = deque(e for e in self._entries if e.sequence not in entries_to_remove)


