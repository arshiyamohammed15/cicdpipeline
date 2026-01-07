
# Imports handled by conftest.py
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from mmm_engine.main import app


@pytest.fixture(scope="function", autouse=True)
def mock_iam():
    """Mock IAM authentication for tests."""
    # Mock the IAM client's verify_token method
    with patch("mmm_engine.integrations.iam_client.IAMClient.verify_token") as mock_verify:
        mock_verify.return_value = (True, {"tenant_id": "demo", "roles": ["dev"]}, None)
        yield mock_verify


@pytest.fixture
def client():
    """Test client with mocked IAM."""
    return TestClient(app)


def auth_headers(tenant: str = "tenant-demo") -> dict[str, str]:
    return {"Authorization": f"Bearer tenant-{tenant}"}


@pytest.mark.unit
def test_decide_returns_actions(client):
    response = client.post(
        "/v1/mmm/decide",
        json={"tenant_id": "demo", "actor_id": "alice", "context": {"roles": ["dev"]}},
        headers=auth_headers("demo"),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"]["actions"]


