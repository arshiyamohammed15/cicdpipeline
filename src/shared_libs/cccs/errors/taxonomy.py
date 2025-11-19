"""Error Taxonomy Framework (ETFHF) implementation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Dict, Type

from ..types import CanonicalError


@dataclass(frozen=True)
class TaxonomyEntry:
    canonical_code: str
    severity: str
    retryable: bool
    user_message: str


class ErrorTaxonomy:
    """Maps exceptions to canonical codes per EPC-5 manifests."""

    def __init__(self, mapping: Dict[Type[BaseException], TaxonomyEntry]):
        self._mapping = mapping

    def normalize_error(self, error: BaseException, context: dict | None = None) -> CanonicalError:
        entry = self._resolve_entry(error)
        debug_id = f"err-{uuid.uuid4().hex[:12]}"
        return CanonicalError(
            canonical_code=entry.canonical_code,
            severity=entry.severity,
            retryable=entry.retryable,
            user_message=entry.user_message,
            debug_id=debug_id,
        )

    def _resolve_entry(self, error: BaseException) -> TaxonomyEntry:
        for exc_type, entry in self._mapping.items():
            if isinstance(error, exc_type):
                return entry
        return TaxonomyEntry(
            canonical_code="unknown_error",
            severity="critical",
            retryable=False,
            user_message="An unknown error occurred.",
        )


