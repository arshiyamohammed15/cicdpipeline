"""Deduplication store stub."""
from __future__ import annotations

from typing import Set


class DeduplicationStore:
    def __init__(self) -> None:
        self._seen: Set[str] = set()

    def is_duplicate(self, signal_id: str) -> bool:
        if signal_id in self._seen:
            return True
        self._seen.add(signal_id)
        return False
