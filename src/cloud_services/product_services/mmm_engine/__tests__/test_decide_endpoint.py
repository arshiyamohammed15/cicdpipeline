from fastapi.testclient import TestClient

from cloud_services.product_services.mmm_engine.main import app


client = TestClient(app)


def auth_headers(tenant: str = "tenant-demo") -> dict[str, str]:
    return {"Authorization": f"Bearer tenant-{tenant}"}


def test_decide_returns_actions():
    response = client.post(
        "/v1/mmm/decide",
        json={"tenant_id": "demo", "actor_id": "alice", "context": {"roles": ["dev"]}},
        headers=auth_headers("demo"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"]["actions"]


