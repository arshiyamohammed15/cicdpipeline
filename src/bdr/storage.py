"""Storage backend abstractions used by the BDR engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List
from uuid import uuid4

from .models import BackupPlan, BackupType, Dataset, RestoreMode


@dataclass(frozen=True)
class BackupArtifact:
    dataset_id: str
    location: str
    payload: str


class BackupStorageBackend:
    """Abstract storage backend API."""

    def create_backup(
        self,
        plan: BackupPlan,
        datasets: Iterable[Dataset],
        backup_type: BackupType,
    ) -> List[BackupArtifact]:
        raise NotImplementedError

    def restore(
        self,
        artifacts: Iterable[BackupArtifact],
        mode: RestoreMode,
        target_env: str,
    ) -> None:
        raise NotImplementedError


class InMemoryBackupStorage(BackupStorageBackend):
    """Deterministic backend used for unit tests and simulations."""

    def __init__(self) -> None:
        self._dataset_sources: Dict[str, str] = {}
        self._restores: List[dict] = []

    def seed_dataset(self, dataset_id: str, content: str) -> None:
        self._dataset_sources[dataset_id] = content

    def create_backup(
        self,
        plan: BackupPlan,
        datasets: Iterable[Dataset],
        backup_type: BackupType,
    ) -> List[BackupArtifact]:
        artifacts: List[BackupArtifact] = []
        for dataset in datasets:
            payload = self._dataset_sources.get(dataset.dataset_id, "")
            location = f"memory://{plan.plan_id}/{dataset.dataset_id}/{uuid4().hex}"
            artifacts.append(
                BackupArtifact(
                    dataset_id=dataset.dataset_id,
                    location=location,
                    payload=f"{backup_type.value}:{payload}",
                )
            )
        return artifacts

    def restore(
        self,
        artifacts: Iterable[BackupArtifact],
        mode: RestoreMode,
        target_env: str,
    ) -> None:
        self._restores.append(
            {
                "mode": mode.value,
                "target_env": target_env,
                "dataset_ids": [artifact.dataset_id for artifact in artifacts],
            }
        )

    @property
    def restores(self) -> List[dict]:
        return list(self._restores)

