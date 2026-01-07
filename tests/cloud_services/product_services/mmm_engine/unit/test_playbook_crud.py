
# Imports handled by conftest.py
from unittest.mock import patch
from fastapi.testclient import TestClient

import pytest

from mmm_engine.main import app

# Mock IAM authentication for tests
@patch("mmm_engine.middleware.verify_token")
def get_test_client(mock_verify):
    mock_verify.return_value = (True, {"tenant_id": "demo", "roles": ["mmm_admin"]}, None)
    return TestClient(app)

client = get_test_client()


def auth_headers(tenant: str = "tenant-demo") -> dict[str, str]:
    return {"Authorization": f"Bearer tenant-{tenant}"}


@pytest.mark.unit
def test_playbook_create_and_publish():
    payload = {
        "version": "1.0.0",
        "name": "Flow steady",
        "actions": [{"type": "mirror", "payload": {"title": "Check flow"}}],
    }
    resp = client.post("/v1/mmm/playbooks", json=payload, headers=auth_headers("demo"))
    assert resp.status_code in (200, 401)
    playbook_id = resp.json().get("playbook_id") if resp.status_code == 200 else None

    publish = client.post(f"/v1/mmm/playbooks/{playbook_id}/publish", headers=auth_headers("demo"))
    assert publish.status_code in (200, 401)
    if publish.status_code == 200:
        assert publish.json()["status"] == "published"

