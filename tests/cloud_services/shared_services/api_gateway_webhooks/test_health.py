from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def _load_app():
    repo_root = Path(__file__).resolve().parents[4]
    module_path = repo_root / "src" / "cloud_services" / "shared-services" / "api-gateway-webhooks" / "main.py"
    spec = importlib.util.spec_from_file_location("api_gateway_webhooks_main", module_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module.app


def test_health() -> None:
    app = _load_app()
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "api-gateway-webhooks"
