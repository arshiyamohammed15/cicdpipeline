from fastapi.testclient import TestClient

from cloud_services.product_services.mmm_engine.main import app


client = TestClient(app)


def auth_headers(tenant: str = "tenant-demo") -> dict[str, str]:
    return {"Authorization": f"Bearer tenant-{tenant}"}


def test_record_outcome_accepts_request():
    decide_resp = client.post(
        "/v1/mmm/decide",
        json={"tenant_id": "demo", "actor_id": "alice", "context": {}},
        headers=auth_headers("demo"),
    )
    decision_id = decide_resp.json()["decision"]["decision_id"]
    action_id = decide_resp.json()["decision"]["actions"][0]["action_id"]

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

