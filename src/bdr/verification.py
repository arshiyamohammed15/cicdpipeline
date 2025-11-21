"""Backup verification utilities."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Iterable

from .catalog import BackupCatalog, CatalogError
from .models import BackupRun, BackupStatus, BackupVerificationRecord, VerificationStatus


class VerificationError(RuntimeError):
    """Raised when verification fails."""


class ChecksumComputer:
    """Generates checksums for backup payload descriptors."""

    def compute(self, payload: bytes | str) -> str:
        data = payload if isinstance(payload, bytes) else payload.encode("utf-8")
        return hashlib.sha256(data).hexdigest()


class BackupVerifier:
    """Performs checksum verification for backups and updates the catalog."""

    def __init__(self, catalog: BackupCatalog, checksum: ChecksumComputer | None = None) -> None:
        self._catalog = catalog
        self._checksum = checksum or ChecksumComputer()

    def verify(self, run: BackupRun, payloads: Iterable[bytes | str]) -> BackupVerificationRecord:
        expected = run.checksums.get("sha256")
        computed = self._checksum.compute("".join(value.decode("utf-8") if isinstance(value, bytes) else value for value in payloads))
        status = VerificationStatus.VERIFIED if expected == computed else VerificationStatus.SUSPECT
        record = BackupVerificationRecord(
            backup_id=run.backup_id,
            verified_at=datetime.now(timezone.utc),
            status=status,
            details=None if status == VerificationStatus.VERIFIED else "checksum_mismatch",
        )
        if status == VerificationStatus.VERIFIED:
            self._catalog.record_verification(record)
        else:
            # Still record the verification attempt for observability, but mark as suspect.
            try:
                self._catalog.record_verification(record)
            except CatalogError as exc:
                raise VerificationError(str(exc)) from exc
        return record

