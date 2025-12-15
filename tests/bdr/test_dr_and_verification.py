from datetime import datetime, timezone

import pytest

from src.bdr.catalog import BackupCatalog
from src.bdr.dr import DRScenarioCatalog, DRError, FailoverOrchestrator
from src.bdr.models import BackupRun, BackupStatus, BackupType, VerificationStatus
from src.bdr.observability import MetricsRegistry, StructuredLogger
from src.bdr.receipts import DecisionReceiptEmitter
from src.bdr.verification import BackupVerifier, ChecksumComputer, VerificationError


def test_failover_raises_for_missing_scenario() -> None:
    catalog = DRScenarioCatalog()
    orchestrator = FailoverOrchestrator(
        scenarios=catalog,
        metrics=MetricsRegistry(),
        logger=StructuredLogger(),
        receipts=DecisionReceiptEmitter(),
    )

    with pytest.raises(DRError):
        orchestrator.execute(
            scenario_id="missing-scenario",
            initiator="alice",
            target_env="prod",
        )


def test_verification_catalog_error_is_wrapped() -> None:
    checksum_payload = "payload"
    started = datetime.now(timezone.utc)
    finished = started

    # Create a run that matches the checksum but is not recorded in the catalog,
    # which will trigger a CatalogError inside record_verification.
    checksum = ChecksumComputer().compute(checksum_payload)
    run = BackupRun(
        backup_id="bk_missing",
        plan_id="plan1",
        dataset_ids=["dataset1"],
        started_at=started,
        finished_at=finished,
        backup_type=BackupType.FULL,
        status=BackupStatus.SUCCESS,
        storage_locations=[],
        checksums={"sha256": checksum},
        verification_status=VerificationStatus.SUSPECT,
        verification_details=None,
    )

    verifier = BackupVerifier(catalog=BackupCatalog())

    with pytest.raises(VerificationError):
        verifier.verify(run=run, payloads=[checksum_payload])

