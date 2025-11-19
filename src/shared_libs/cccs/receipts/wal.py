"""Durable write-ahead log queues for courier batching with deep-copy and receipt emission."""

from __future__ import annotations

import copy
import json
import logging
import os
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Callable, Deque, Dict, Iterable, Optional

logger = logging.getLogger(__name__)


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
                os.fsync(handle.fileno())
            temp_path.replace(self._path)
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
        for entry in self._entries:
            if entry.sequence == sequence:
                entry.state = state
                break
        self._persist()

    def drain(
        self, sink: Callable[[Dict[str, Any]], None], receipt_emitter: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Iterable[WALEntry]:
        """
        Drain pending entries to sink, emitting receipts for failures.

        Per PRD §7.1: Nothing is dropped without an explicit dead_letter receipt.

        Args:
            sink: Callback to process entries
            receipt_emitter: Optional callback to emit dead_letter receipts

        Returns:
            Iterable of drained entries
        """
        drained: list[WALEntry] = []
        pending_entries = [e for e in self._entries if e.state == "pending"]

        for entry in pending_entries:
            try:
                # Deep copy payload before passing to sink
                payload_copy = copy.deepcopy(entry.payload)
                sink(payload_copy)
                entry.state = "acked"
                drained.append(entry)
            except Exception as e:
                # Per PRD §7.1: Mark as dead_letter and emit receipt
                entry.state = "dead_letter"
                logger.error(f"WAL drain failed for entry {entry.sequence}: {e}")
                
                # Emit dead_letter receipt per PRD §7.1
                if receipt_emitter:
                    try:
                        dead_letter_receipt = {
                            "receipt_type": "dead_letter",
                            "wal_sequence": entry.sequence,
                            "entry_type": entry.entry_type,
                            "error": str(e),
                            "payload": entry.payload,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                        receipt_emitter(dead_letter_receipt)
                    except Exception as emit_error:
                        logger.error(f"Failed to emit dead_letter receipt: {emit_error}")
            finally:
                self._persist()

        # Remove only acked entries from queue, keep pending and dead_letter
        self._entries = deque(e for e in self._entries if e.state != "acked")
        return drained

    def get_pending_sync_entries(self) -> Iterable[WALEntry]:
        """Get entries marked as pending_sync."""
        return [e for e in self._entries if e.state == "pending_sync"]

    def get_dead_letter_entries(self) -> Iterable[WALEntry]:
        """Get entries marked as dead_letter."""
        return [e for e in self._entries if e.state == "dead_letter"]


