"""Backup catalog persistence primitives."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from .models import (
    BackupRun,
    BackupStatus,
    BackupVerificationRecord,
    DrillResult,
    PlanTestMetadata,
    VerificationStatus,
)
from .storage import BackupArtifact


class CatalogError(RuntimeError):
    """Raised when catalog operations fail."""


class BackupCatalog:
    """In-memory catalog implementation suitable for unit tests and simulations."""

    def __init__(self) -> None:
        self._runs: Dict[str, BackupRun] = {}
        self._runs_by_plan: Dict[str, List[str]] = {}
        self._verifications: Dict[str, BackupVerificationRecord] = {}
        self._plan_metadata: Dict[str, PlanTestMetadata] = {}
        self._artifacts: Dict[str, List[BackupArtifact]] = {}

    def record_run(self, run: BackupRun, artifacts: List[BackupArtifact]) -> None:
        if run.backup_id in self._runs:
            msg = f"Backup {run.backup_id} already recorded"
            raise CatalogError(msg)
        self._runs[run.backup_id] = run
        self._runs_by_plan.setdefault(run.plan_id, []).append(run.backup_id)
        self._artifacts[run.backup_id] = artifacts

    def get_backup(self, backup_id: str) -> BackupRun:
        if backup_id not in self._runs:
            msg = f"Backup {backup_id} not found"
            raise CatalogError(msg)
        return self._runs[backup_id]

    def list_backups(self, plan_id: Optional[str] = None) -> List[BackupRun]:
        if plan_id is None:
            return sorted(self._runs.values(), key=lambda run: run.started_at)
        backup_ids = self._runs_by_plan.get(plan_id, [])
        return [self._runs[backup_id] for backup_id in backup_ids]

    def last_successful_run(self, plan_id: str) -> Optional[BackupRun]:
        runs = [
            self._runs[backup_id]
            for backup_id in self._runs_by_plan.get(plan_id, [])
            if self._runs[backup_id].status == BackupStatus.SUCCESS
        ]
        return max(runs, key=lambda run: run.finished_at, default=None)

    def record_verification(self, record: BackupVerificationRecord) -> None:
        if record.backup_id not in self._runs:
            msg = f"Cannot verify unknown backup {record.backup_id}"
            raise CatalogError(msg)
        self._verifications[record.backup_id] = record
        run = self._runs[record.backup_id]
        self._runs[record.backup_id] = run.model_copy(
            update={
                "verification_status": record.status,
                "verification_details": record.details,
            }
        )

    def mark_plan_test(
        self, plan_id: str, drill_result: DrillResult | None, stale_after: timedelta
    ) -> PlanTestMetadata:
        metadata = self._plan_metadata.get(plan_id) or PlanTestMetadata(plan_id=plan_id)
        tested_at = (
            datetime.now(timezone.utc) if drill_result is not None else metadata.last_tested_at
        )
        metadata = metadata.model_copy(
            update={
                "last_tested_at": tested_at,
                "last_drill_result": drill_result or metadata.last_drill_result,
            }
        )
        if metadata.last_tested_at is None:
            metadata = metadata.model_copy(update={"stale": True})
        else:
            metadata = metadata.model_copy(
                update={
                    "stale": datetime.now(timezone.utc) - metadata.last_tested_at > stale_after
                }
            )
        self._plan_metadata[plan_id] = metadata
        return metadata

    def flag_stale_plans(self, stale_after: timedelta) -> List[str]:
        stale_plans: List[str] = []
        for plan_id, metadata in self._plan_metadata.items():
            if metadata.last_tested_at is None:
                metadata = metadata.model_copy(update={"stale": True})
                self._plan_metadata[plan_id] = metadata
                stale_plans.append(plan_id)
                continue
            if datetime.now(timezone.utc) - metadata.last_tested_at > stale_after:
                metadata = metadata.model_copy(update={"stale": True})
                self._plan_metadata[plan_id] = metadata
                stale_plans.append(plan_id)
        return stale_plans

    def stale_plans(self) -> List[str]:
        return [plan_id for plan_id, metadata in self._plan_metadata.items() if metadata.stale]

    def verification_status(self, backup_id: str) -> VerificationStatus:
        record = self._verifications.get(backup_id)
        if record is None:
            return VerificationStatus.SUSPECT
        return record.status

    def artifacts_for_backup(self, backup_id: str) -> List[BackupArtifact]:
        artifacts = self._artifacts.get(backup_id)
        if artifacts is None:
            msg = f"No artifacts stored for backup {backup_id}"
            raise CatalogError(msg)
        return list(artifacts)

