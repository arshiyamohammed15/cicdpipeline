from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def _load_app():
    repo_root = Path(__file__).resolve().parents[4]
    module_path = repo_root / "src" / "cloud_services" / "shared-services" / "trust-as-capability" / "main.py"
    spec = importlib.util.spec_from_file_location("trust_as_capability_main", module_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module.app


def test_trust_missing_subject() -> None:
    app = _load_app()
    client = TestClient(app)
    resp = client.post("/trust/evaluate", json={"context": {"workspace_trust": True}})
    assert resp.status_code == 400
    assert "subject_id" in resp.json().get("detail", "")
