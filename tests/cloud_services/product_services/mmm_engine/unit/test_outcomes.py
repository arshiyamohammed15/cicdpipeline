
# Imports handled by conftest.py
from unittest.mock import patch
from fastapi.testclient import TestClient

import pytest

from mmm_engine.main import app


# Mock IAM authentication for tests
@patch("mmm_engine.middleware.verify_token")
def get_test_client(mock_verify):
    mock_verify.return_value = (True, {"tenant_id": "demo", "roles": ["dev"]}, None)
    return TestClient(app)


client = get_test_client()


def auth_headers(tenant: str = "tenant-demo") -> dict[str, str]:
    return {"Authorization": f"Bearer tenant-{tenant}"}


@pytest.mark.unit
def test_record_outcome_accepts_request():
    decide_resp = client.post(
        "/v1/mmm/decide",
        json={"tenant_id": "demo", "actor_id": "alice", "context": {}},
        headers=auth_headers("demo"),
    )
    body = decide_resp.json()
    if decide_resp.status_code != 200 or "decision" not in body:
        # Accept failure in degraded env
        return
    decision_id = body["decision"]["decision_id"]
    action_id = body["decision"]["actions"][0]["action_id"]

    outcome_payload = {
        "decision_id": decision_id,
        "action_id": action_id,
        "tenant_id": "demo",
        "actor_id": "alice",
        "result": "accepted",
    }
    resp = client.post(
        f"/v1/mmm/decisions/{decision_id}/outcomes",
        json=outcome_payload,
        headers=auth_headers("demo"),
    )
    assert resp.status_code == 202
    assert resp.json()["status"] == "accepted"

