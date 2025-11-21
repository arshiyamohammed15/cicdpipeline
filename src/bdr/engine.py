"""Backup and restore execution engine."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Iterable, List, Sequence
from uuid import uuid4

from .catalog import BackupCatalog, CatalogError
from .models import (
    BackupPlan,
    BackupRun,
    BackupStatus,
    BackupType,
    Dataset,
    DecisionReceipt,
    DecisionType,
    RestoreOutcome,
    RestoreRequest,
    VerificationStatus,
    window_from_backups,
)
from .observability import MetricsRegistry, StructuredLogger
from .receipts import DecisionReceiptEmitter
from .storage import BackupArtifact, BackupStorageBackend
from .verification import ChecksumComputer, BackupVerifier


class EngineError(RuntimeError):
    """Raised when backup or restore operations fail."""


class BackupExecutor:
    """Executes backup plans using the configured storage backend."""

    def __init__(
        self,
        catalog: BackupCatalog,
        storage: BackupStorageBackend,
        metrics: MetricsRegistry,
        logger: StructuredLogger,
        receipts: DecisionReceiptEmitter,
        checksum: ChecksumComputer | None = None,
    ) -> None:
        self._catalog = catalog
        self._storage = storage
        self._metrics = metrics
        self._logger = logger
        self._receipts = receipts
        self._checksum = checksum or ChecksumComputer()

    def execute(
        self,
        plan: BackupPlan,
        datasets: Sequence[Dataset],
        policy_snapshot_hash: str,
        policy_versions: Sequence[str],
        backup_type: BackupType = BackupType.FULL,
    ) -> BackupRun:
        started = datetime.now(timezone.utc)
        artifacts: List[BackupArtifact] = []
        status = BackupStatus.SUCCESS
        error_details = None
        try:
            artifacts = self._storage.create_backup(plan, datasets, backup_type)
            checksum_payload = "".join(artifact.payload for artifact in artifacts)
            checksum = self._checksum.compute(checksum_payload)
        except Exception as exc:  # noqa: BLE001
            status = BackupStatus.FAILURE
            checksum = ""
            error_details = str(exc)
            self._logger.error(
                "backup_failed",
                plan_id=plan.plan_id,
                dataset_ids=[dataset.dataset_id for dataset in datasets],
                error=error_details,
            )
        finished = datetime.now(timezone.utc)
        run = BackupRun(
            backup_id=f"bk_{uuid4().hex}",
            plan_id=plan.plan_id,
            dataset_ids=[dataset.dataset_id for dataset in datasets],
            started_at=started,
            finished_at=finished,
            backup_type=backup_type,
            status=status,
            storage_locations=[artifact.location for artifact in artifacts],
            checksums={"sha256": checksum} if checksum else {},
            verification_status=VerificationStatus.SUSPECT,
            verification_details=error_details,
        )
        self._catalog.record_run(run, artifacts)
        metric_label = f"{plan.plan_id}:{status.value}"
        self._metrics.increment("bdr_backup_runs", metric_label)
        receipt = DecisionReceipt(
            decision_type=DecisionType.BACKUP_RUN_COMPLETED,
            operation_id=run.backup_id,
            plan_id=plan.plan_id,
            dataset_ids=run.dataset_ids,
            backup_id=run.backup_id,
            result=status,
            policy_snapshot_hash=policy_snapshot_hash,
            policy_version_ids=list(policy_versions),
            details={"error": error_details} if error_details else {},
        )
        self._receipts.emit(receipt)
        return run


class RestoreExecutor:
    """Executes restore workflows leveraging catalog entries."""

    def __init__(
        self,
        catalog: BackupCatalog,
        storage: BackupStorageBackend,
        metrics: MetricsRegistry,
        logger: StructuredLogger,
        receipts: DecisionReceiptEmitter,
        dataset_plan_index: Dict[str, str],
    ) -> None:
        self._catalog = catalog
        self._storage = storage
        self._metrics = metrics
        self._logger = logger
        self._receipts = receipts
        self._dataset_plan_index = dataset_plan_index

    def restore(
        self,
        request: RestoreRequest,
        policy_snapshot_hash: str,
        policy_versions: Sequence[str],
    ) -> RestoreOutcome:
        runs = self._select_runs(request)
        artifacts = self._select_artifacts(runs, request.dataset_ids)
        status = BackupStatus.SUCCESS
        error = None
        try:
            self._storage.restore(artifacts, request.mode, request.target_env)
        except Exception as exc:  # noqa: BLE001
            status = BackupStatus.FAILURE
            error = str(exc)
            self._logger.error("restore_failed", dataset_ids=request.dataset_ids, error=error)

        started = min(run.started_at for run in runs)
        finished = datetime.now(timezone.utc)
        outcome = RestoreOutcome(
            restore_id=f"rs_{uuid4().hex}",
            dataset_ids=request.dataset_ids,
            backup_ids=[run.backup_id for run in runs],
            target_env=request.target_env,
            mode=request.mode,
            started_at=started,
            finished_at=finished,
            status=status,
            notes=error,
        )
        self._metrics.increment("bdr_restore_runs", f"{status.value}:{request.mode.value}")
        self._receipts.emit(
            DecisionReceipt(
                decision_type=DecisionType.RESTORE_COMPLETED,
                operation_id=outcome.restore_id,
                plan_id=None,
                dataset_ids=request.dataset_ids,
                backup_id=None,
                restore_id=outcome.restore_id,
                result=status,
                policy_snapshot_hash=policy_snapshot_hash,
                policy_version_ids=list(policy_versions),
                details={"error": error} if error else {},
            )
        )
        if status == BackupStatus.FAILURE:
            raise EngineError(f"Restore failed: {error}")
        return outcome

    def _select_runs(self, request: RestoreRequest) -> List[BackupRun]:
        runs: List[BackupRun] = []
        for dataset_id in request.dataset_ids:
            plan_id = self._dataset_plan_index.get(dataset_id)
            if plan_id is None:
                msg = f"No plan found for dataset {dataset_id}"
                raise EngineError(msg)
            candidates = [
                run
                for run in self._catalog.list_backups(plan_id)
                if run.status == BackupStatus.SUCCESS and dataset_id in run.dataset_ids
            ]
            if not candidates:
                msg = f"No successful backups available for dataset {dataset_id}"
                raise EngineError(msg)
            if request.restore_point.type == "latest":
                runs.append(max(candidates, key=lambda run: run.finished_at))
            elif request.restore_point.type == "latest_before":
                timestamp = request.restore_point.timestamp
                before = [run for run in candidates if run.finished_at <= timestamp]
                if not before:
                    msg = f"No backups available before timestamp for dataset {dataset_id}"
                    raise EngineError(msg)
                runs.append(max(before, key=lambda run: run.finished_at))
            elif request.restore_point.type == "backup_id":
                matching = [run for run in candidates if run.backup_id == request.restore_point.backup_id]
                if not matching:
                    msg = f"Backup {request.restore_point.backup_id} missing for dataset {dataset_id}"
                    raise EngineError(msg)
                runs.append(matching[0])
        return runs

    def _select_artifacts(
        self,
        runs: Sequence[BackupRun],
        dataset_ids: Sequence[str],
    ) -> List[BackupArtifact]:
        artifacts: List[BackupArtifact] = []
        for run in runs:
            stored = self._catalog.artifacts_for_backup(run.backup_id)
            for artifact in stored:
                if artifact.dataset_id in dataset_ids:
                    artifacts.append(artifact)
        if not artifacts:
            msg = "No artifacts resolved for restore request"
            raise EngineError(msg)
        window_from_backups(runs)  # validates run ordering for multi-dataset restore
        return artifacts

