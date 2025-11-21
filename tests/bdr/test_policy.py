import json
from pathlib import Path

import pytest

from bdr.policy import PolicyLoader, PolicyLoadError


def test_policy_loader_success(dataset_definitions, plan_definitions):
    loader = PolicyLoader(dataset_source=dataset_definitions, plan_source=plan_definitions)
    bundle = loader.load()
    assert len(bundle.datasets) == 2
    assert len(bundle.plans) == 2


def test_policy_loader_rejects_unknown_dataset(dataset_definitions, plan_definitions):
    bad_plans = [plan_definitions[0] | {"dataset_ids": ["unknown_ds"]}]
    loader = PolicyLoader(dataset_source=dataset_definitions, plan_source=bad_plans)
    with pytest.raises(PolicyLoadError):
        loader.load()


def test_policy_loader_reads_from_files(tmp_path: Path, dataset_definitions, plan_definitions):
    dataset_file = tmp_path / "datasets.json"
    plan_file = tmp_path / "plans.json"
    dataset_file.write_text(json.dumps(dataset_definitions), encoding="utf-8")
    plan_file.write_text(json.dumps(plan_definitions), encoding="utf-8")
    loader = PolicyLoader(dataset_source=str(dataset_file), plan_source=str(plan_file))
    bundle = loader.load()
    assert bundle.snapshot_hash
    assert "ds_policy_store" in bundle.dataset_index()
    assert "bp_policy_store" in bundle.plan_index()


def test_policy_loader_rejects_invalid_json(tmp_path: Path):
    dataset_file = tmp_path / "datasets.json"
    plan_file = tmp_path / "plans.json"
    dataset_file.write_text("{invalid", encoding="utf-8")
    plan_file.write_text("[]", encoding="utf-8")
    loader = PolicyLoader(dataset_source=str(dataset_file), plan_source=str(plan_file))
    with pytest.raises(PolicyLoadError):
        loader.load()


def test_policy_loader_requires_json_array(tmp_path: Path):
    dataset_file = tmp_path / "datasets.json"
    plan_file = tmp_path / "plans.json"
    dataset_file.write_text("{}", encoding="utf-8")
    plan_file.write_text("[]", encoding="utf-8")
    loader = PolicyLoader(dataset_source=str(dataset_file), plan_source=str(plan_file))
    with pytest.raises(PolicyLoadError):
        loader.load()


def test_policy_loader_missing_file(tmp_path: Path):
    missing_path = tmp_path / "missing.json"
    plan_file = tmp_path / "plans.json"
    plan_file.write_text("[]", encoding="utf-8")
    loader = PolicyLoader(dataset_source=str(missing_path), plan_source=str(plan_file))
    with pytest.raises(PolicyLoadError):
        loader.load()


def test_policy_loader_validation_error(dataset_definitions, plan_definitions):
    bad_datasets = dataset_definitions.copy()
    bad_datasets[0] = {**bad_datasets[0]}
    bad_datasets[0].pop("dataset_id")
    loader = PolicyLoader(dataset_source=bad_datasets, plan_source=plan_definitions)
    with pytest.raises(PolicyLoadError):
        loader.load()

