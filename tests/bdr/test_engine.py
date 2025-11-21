from datetime import datetime, timedelta, timezone

import pytest

from bdr.catalog import BackupCatalog
from bdr.engine import EngineError, RestoreExecutor
from bdr.models import (
    BackupRun,
    BackupStatus,
    BackupType,
    RestoreMode,
    RestorePoint,
    RestoreRequest,
    VerificationStatus,
)
from bdr.observability import MetricsRegistry, StructuredLogger
from bdr.receipts import DecisionReceiptEmitter
from bdr.storage import BackupArtifact, InMemoryBackupStorage


def _backup_run(status: BackupStatus = BackupStatus.SUCCESS):
    now = datetime.now(timezone.utc)
    return BackupRun(
        backup_id="bk_engine",
        plan_id="plan",
        dataset_ids=["ds"],
        started_at=now - timedelta(minutes=1),
        finished_at=now,
        backup_type=BackupType.FULL,
        status=status,
        storage_locations=["memory://plan/ds/1"],
        checksums={"sha256": "abc"},
        verification_status=VerificationStatus.SUSPECT,
    )


def _executor(catalog, dataset_plan_index):
    storage = InMemoryBackupStorage()
    metrics = MetricsRegistry()
    logger = StructuredLogger()
    receipts = DecisionReceiptEmitter()
    return RestoreExecutor(catalog, storage, metrics, logger, receipts, dataset_plan_index)


def test_restore_executor_missing_plan_mapping():
    catalog = BackupCatalog()
    executor = _executor(catalog, {})
    request = RestoreRequest(
        dataset_ids=["unknown"],
        target_env="env",
        mode=RestoreMode.IN_PLACE,
        restore_point=RestorePoint(type="latest"),
    )
    with pytest.raises(EngineError):
        executor.restore(request, "hash", [])


def test_restore_executor_requires_successful_backups():
    catalog = BackupCatalog()
    run = _backup_run(status=BackupStatus.FAILURE)
    catalog.record_run(run, [BackupArtifact(dataset_id="ds", location="memory://plan/ds/1", payload="data")])
    executor = _executor(catalog, {"ds": "plan"})
    request = RestoreRequest(
        dataset_ids=["ds"],
        target_env="env",
        mode=RestoreMode.IN_PLACE,
        restore_point=RestorePoint(type="latest"),
    )
    with pytest.raises(EngineError):
        executor.restore(request, "hash", [])


def test_restore_executor_latest_before_without_prior_match():
    catalog = BackupCatalog()
    run = _backup_run()
    catalog.record_run(run, [BackupArtifact(dataset_id="ds", location="memory://plan/ds/1", payload="data")])
    executor = _executor(catalog, {"ds": "plan"})
    past_timestamp = run.started_at - timedelta(hours=1)
    request = RestoreRequest(
        dataset_ids=["ds"],
        target_env="env",
        mode=RestoreMode.IN_PLACE,
        restore_point=RestorePoint(type="latest_before", timestamp=past_timestamp),
    )
    with pytest.raises(EngineError):
        executor.restore(request, "hash", [])


def test_restore_executor_missing_backup_id():
    catalog = BackupCatalog()
    run = _backup_run()
    catalog.record_run(run, [BackupArtifact(dataset_id="ds", location="memory://plan/ds/1", payload="data")])
    executor = _executor(catalog, {"ds": "plan"})
    request = RestoreRequest(
        dataset_ids=["ds"],
        target_env="env",
        mode=RestoreMode.IN_PLACE,
        restore_point=RestorePoint(type="backup_id", backup_id="missing"),
    )
    with pytest.raises(EngineError):
        executor.restore(request, "hash", [])


def test_restore_executor_requires_artifacts():
    catalog = BackupCatalog()
    run = _backup_run()
    artifact = BackupArtifact(dataset_id="other", location="memory://plan/ds/1", payload="data")
    catalog.record_run(run, [artifact])
    executor = _executor(catalog, {"ds": "plan"})
    request = RestoreRequest(
        dataset_ids=["ds"],
        target_env="env",
        mode=RestoreMode.IN_PLACE,
        restore_point=RestorePoint(type="latest"),
    )
    with pytest.raises(EngineError):
        executor.restore(request, "hash", [])


def test_restore_executor_backup_id_success():
    catalog = BackupCatalog()
    run = _backup_run()
    artifact = BackupArtifact(dataset_id="ds", location="memory://plan/ds/1", payload="data")
    catalog.record_run(run, [artifact])
    executor = _executor(catalog, {"ds": "plan"})
    request = RestoreRequest(
        dataset_ids=["ds"],
        target_env="env",
        mode=RestoreMode.IN_PLACE,
        restore_point=RestorePoint(type="backup_id", backup_id="bk_engine"),
    )
    outcome = executor.restore(request, "hash", [])
    assert outcome.status == BackupStatus.SUCCESS


def test_restore_executor_latest_before_success():
    catalog = BackupCatalog()
    run = _backup_run()
    artifact = BackupArtifact(dataset_id="ds", location="memory://plan/ds/1", payload="data")
    catalog.record_run(run, [artifact])
    executor = _executor(catalog, {"ds": "plan"})
    future_timestamp = run.finished_at + timedelta(seconds=1)
    request = RestoreRequest(
        dataset_ids=["ds"],
        target_env="env",
        mode=RestoreMode.SIDE_BY_SIDE,
        restore_point=RestorePoint(type="latest_before", timestamp=future_timestamp),
    )
    outcome = executor.restore(request, "hash", [])
    assert outcome.status == BackupStatus.SUCCESS

