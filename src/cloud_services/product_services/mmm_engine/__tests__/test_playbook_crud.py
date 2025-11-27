from fastapi.testclient import TestClient

from cloud_services.product_services.mmm_engine.main import app

client = TestClient(app)


def auth_headers(tenant: str = "tenant-demo") -> dict[str, str]:
    return {"Authorization": f"Bearer tenant-{tenant}"}


def test_playbook_create_and_publish():
    payload = {
        "version": "1.0.0",
        "name": "Flow steady",
        "actions": [{"type": "mirror", "payload": {"title": "Check flow"}}],
    }
    resp = client.post("/v1/mmm/playbooks", json=payload, headers=auth_headers("demo"))
    assert resp.status_code == 200
    playbook_id = resp.json()["playbook_id"]

    publish = client.post(f"/v1/mmm/playbooks/{playbook_id}/publish", headers=auth_headers("demo"))
    assert publish.status_code == 200
    assert publish.json()["status"] == "published"

