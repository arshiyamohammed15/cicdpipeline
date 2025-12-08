"""Policy ingestion utilities for the BDR backend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
import hashlib

from pydantic import ValidationError

from .models import BackupPlan, Dataset, ensure_unique_ids


class PolicyLoadError(RuntimeError):
    """Raised when policy bundles cannot be loaded or validated."""


def _load_json(source: str | Path) -> Sequence[dict]:
    path = Path(source)
    if not path.exists():
        msg = f"Policy file not found: {path}"
        raise PolicyLoadError(msg)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"Invalid JSON in policy file {path}: {exc}"
        raise PolicyLoadError(msg) from exc
    if not isinstance(data, Sequence):
        msg = f"Policy file {path} must contain a JSON array"
        raise PolicyLoadError(msg)
    return data


def _hash_payload(records: Iterable[dict]) -> str:
    hasher = hashlib.sha256()
    for record in records:
        hasher.update(json.dumps(record, sort_keys=True).encode("utf-8"))
    return hasher.hexdigest()


class PolicyBundle:
    """Container holding dataset and plan definitions plus integrity metadata."""

    def __init__(self, datasets: List[Dataset], plans: List[BackupPlan], snapshot_hash: str) -> None:
        self.datasets = datasets
        self.plans = plans
        self.snapshot_hash = snapshot_hash

    def dataset_index(self) -> dict[str, Dataset]:
        return {dataset.dataset_id: dataset for dataset in self.datasets}

    def plan_index(self) -> dict[str, BackupPlan]:
        return {plan.plan_id: plan for plan in self.plans}


class PolicyLoader:
    """Loads datasets and backup plans from JSON sequences or files."""

    def __init__(
        self,
        dataset_source: Sequence[dict] | str | Path,
        plan_source: Sequence[dict] | str | Path,
    ) -> None:
        self._dataset_source = dataset_source
        self._plan_source = plan_source

    def load(self) -> PolicyBundle:
        datasets_raw = (
            self._dataset_source
            if isinstance(self._dataset_source, Sequence) and not isinstance(self._dataset_source, (str, bytes, bytearray))
            else _load_json(self._dataset_source)
        )
        plans_raw = (
            self._plan_source
            if isinstance(self._plan_source, Sequence) and not isinstance(self._plan_source, (str, bytes, bytearray))
            else _load_json(self._plan_source)
        )
        snapshot_hash = _hash_payload(datasets_raw) + _hash_payload(plans_raw)

        try:
            def _normalize_plane(entry):
                if isinstance(entry, dict) and "plane" in entry and isinstance(entry["plane"], str):
                    entry = dict(entry)
                    entry["plane"] = entry["plane"].replace("-", "_")
                return entry

            datasets = [Dataset.model_validate(_normalize_plane(item)) for item in datasets_raw]
            plans = [BackupPlan.model_validate(_normalize_plane(plan)) for plan in plans_raw]
        except ValidationError as exc:
            msg = f"Policy validation failed: {exc}"
            raise PolicyLoadError(msg) from exc

        ensure_unique_ids(datasets, "dataset_id")
        ensure_unique_ids(plans, "plan_id")

        dataset_ids = {dataset.dataset_id for dataset in datasets}
        for plan in plans:
            missing = set(plan.dataset_ids) - dataset_ids
            if missing:
                msg = f"Plan {plan.plan_id} references unknown datasets: {', '.join(sorted(missing))}"
                raise PolicyLoadError(msg)

        return PolicyBundle(datasets=datasets, plans=plans, snapshot_hash=snapshot_hash)

