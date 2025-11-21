from datetime import datetime, timedelta, timezone

import pytest

from bdr.catalog import BackupCatalog, CatalogError
from bdr.models import (
    BackupRun,
    BackupStatus,
    BackupType,
    BackupVerificationRecord,
    DrillResult,
    PlanTestMetadata,
    VerificationStatus,
)
from bdr.storage import BackupArtifact


def _sample_run():
    now = datetime.now(timezone.utc)
    return BackupRun(
        backup_id="bk_1",
        plan_id="plan_a",
        dataset_ids=["ds1"],
        started_at=now - timedelta(minutes=1),
        finished_at=now,
        backup_type=BackupType.FULL,
        status=BackupStatus.SUCCESS,
        storage_locations=["memory://plan_a/ds1/1"],
        checksums={"sha256": "abc"},
    )


def test_catalog_records_runs_and_verification():
    catalog = BackupCatalog()
    run = _sample_run()
    artifact = BackupArtifact(dataset_id="ds1", location="memory://x", payload="data")
    catalog.record_run(run, [artifact])
    stored = catalog.get_backup("bk_1")
    assert stored.plan_id == "plan_a"

    verification = BackupVerificationRecord(
        backup_id="bk_1",
        verified_at=datetime.now(timezone.utc),
        status=VerificationStatus.VERIFIED,
    )
    catalog.record_verification(verification)
    assert catalog.verification_status("bk_1") == VerificationStatus.VERIFIED


def test_catalog_rejects_duplicate_backups():
    catalog = BackupCatalog()
    run = _sample_run()
    artifact = BackupArtifact(dataset_id="ds1", location="memory://x", payload="data")
    catalog.record_run(run, [artifact])
    with pytest.raises(CatalogError):
        catalog.record_run(run, [artifact])
    with pytest.raises(CatalogError):
        catalog.get_backup("missing")
    with pytest.raises(CatalogError):
        catalog.artifacts_for_backup("missing")


def test_catalog_plan_test_metadata():
    catalog = BackupCatalog()
    run = _sample_run()
    artifact = BackupArtifact(dataset_id="ds1", location="memory://x", payload="data")
    catalog.record_run(run, [artifact])
    drill = DrillResult(
        scenario_id="sc1",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        achieved_rpo="PT5M",
        achieved_rto="PT10M",
        status=BackupStatus.SUCCESS,
    )
    catalog.mark_plan_test("plan_a", drill, timedelta(days=1))
    assert "plan_a" not in catalog.flag_stale_plans(timedelta(days=30))
    metadata = catalog.mark_plan_test("plan_b", None, timedelta(days=1))
    assert metadata.stale
    catalog._plan_metadata["plan_c"] = PlanTestMetadata(  # type: ignore[attr-defined]
        plan_id="plan_c",
        last_tested_at=datetime.now(timezone.utc) - timedelta(days=2),
    )
    assert "plan_b" in catalog.flag_stale_plans(timedelta(days=1))
    assert "plan_c" in catalog.flag_stale_plans(timedelta(days=1))
    assert catalog.last_successful_run("plan_a") is not None
    assert catalog.list_backups()  # exercise sorting path
    assert catalog.verification_status("missing") == VerificationStatus.SUSPECT

