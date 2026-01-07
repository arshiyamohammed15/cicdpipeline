from __future__ import annotations
import pytest

import os
from pathlib import Path

from config.constitution import path_utils


@pytest.mark.constitution
def test_env_override_resolves_and_creates_parent(tmp_path, monkeypatch):
    target = tmp_path / "custom" / "constitution_rules.db"
    monkeypatch.setenv("CONSTITUTION_DB_PATH", str(target))

    resolved = path_utils.resolve_constitution_db_path(None)

    assert resolved == target.resolve()
    assert resolved.parent.exists()


@pytest.mark.constitution
def test_inside_repo_candidate_redirects_to_storage(tmp_path, monkeypatch):
    storage_dir = tmp_path / "ide" / "db"
    monkeypatch.setattr(path_utils, "_default_storage_dir", lambda: storage_dir)
    monkeypatch.delenv("CONSTITUTION_DB_PATH", raising=False)

    candidate = path_utils.REPO_ROOT / "config" / "constitution_rules.db"
    resolved = path_utils.resolve_constitution_db_path(str(candidate))

    assert resolved.parent == storage_dir
    assert resolved.name == "constitution_rules.db"
    assert resolved.is_absolute()
    assert resolved.parent.exists()
    # ensure the resolved path is no longer inside the repo
    assert not resolved.is_relative_to(path_utils.REPO_ROOT)


@pytest.mark.constitution
def test_relative_candidate_drops_parents_and_uses_storage_dir(tmp_path, monkeypatch):
    storage_dir = tmp_path / "ide" / "db"
    monkeypatch.setattr(path_utils, "_default_storage_dir", lambda: storage_dir)
    monkeypatch.delenv("ALERTING_DB_PATH", raising=False)

    resolved = path_utils.resolve_alerting_db_path("nested/alerting.db")

    assert resolved.parent == storage_dir
    assert resolved.name == "alerting.db"
    assert resolved.parent.exists()
