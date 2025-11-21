from datetime import datetime, timezone

import pytest

from bdr.catalog import BackupCatalog
from bdr.models import BackupRun, BackupStatus, BackupType, VerificationStatus
from bdr.storage import BackupArtifact
from bdr.verification import BackupVerifier, ChecksumComputer, VerificationError


def _run():
    now = datetime.now(timezone.utc)
    return BackupRun(
        backup_id="bk_ver",
        plan_id="plan",
        dataset_ids=["ds"],
        started_at=now,
        finished_at=now,
        backup_type=BackupType.FULL,
        status=BackupStatus.SUCCESS,
        storage_locations=["memory://plan/ds/1"],
        checksums={"sha256": ChecksumComputer().compute("payload")},
    )


def test_verification_success():
    catalog = BackupCatalog()
    run = _run()
    artifact = BackupArtifact(dataset_id="ds", location="memory://plan/ds/1", payload="payload")
    catalog.record_run(run, [artifact])
    verifier = BackupVerifier(catalog)
    record = verifier.verify(run, ["payload"])
    assert record.status == VerificationStatus.VERIFIED


def test_verification_detects_mismatch():
    catalog = BackupCatalog()
    run = _run()
    artifact = BackupArtifact(dataset_id="ds", location="memory://plan/ds/1", payload="payload")
    catalog.record_run(run, [artifact])
    verifier = BackupVerifier(catalog)
    record = verifier.verify(run, ["different"])
    assert record.status == VerificationStatus.SUSPECT


def test_verification_handles_catalog_error_for_suspect():
    catalog = BackupCatalog()
    run = _run()
    verifier = BackupVerifier(catalog)
    with pytest.raises(VerificationError):
        verifier.verify(run, ["different"])

