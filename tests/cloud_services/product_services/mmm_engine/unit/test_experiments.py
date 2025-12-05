from __future__ import annotations
"""
Feature tests for experiment management (FR-13).

Tests experiment CRUD and activation/deactivation.
"""


# Imports handled by conftest.py

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from mmm_engine.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client with mocked IAM."""
    # Mock IAM client to bypass authentication
    with patch("mmm_engine.middleware.verify_token") as mock_verify:
        mock_verify.return_value = (True, {"tenant_id": "tenant-1", "roles": ["mmm_admin"]}, None)
        yield TestClient(app)


def test_experiments_api_list(client: TestClient) -> None:
    """Test GET /v1/mmm/experiments endpoint."""
    with patch(
        "mmm_engine.routes.get_tenant_id",
        return_value="tenant-1",
    ):
        with patch("mmm_engine.routes.list_experiments") as mock_list:
            mock_list.return_value = [
                {
                    "experiment_id": "exp-1",
                    "name": "Test Experiment",
                    "status": "active",
                    "config": {},
                }
            ]

            response = client.get(
                "/v1/mmm/experiments?tenant_id=tenant-1",
                headers={"Authorization": "Bearer token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["experiment_id"] == "exp-1"


def test_experiments_api_create(client: TestClient) -> None:
    """Test POST /v1/mmm/experiments endpoint."""
    with patch(
        "mmm_engine.routes.get_tenant_id",
        return_value="tenant-1",
    ):
        with patch("mmm_engine.routes.create_experiment") as mock_create:
            mock_create.return_value = {
                "experiment_id": "exp-1",
                "tenant_id": "tenant-1",
                "name": "New Experiment",
                "status": "draft",
                "config": {},
            }

            response = client.post(
                "/v1/mmm/experiments",
                json={"name": "New Experiment", "status": "draft", "config": {}},
                headers={"Authorization": "Bearer token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "New Experiment"


def test_experiments_api_activate(client: TestClient) -> None:
    """Test POST /v1/mmm/experiments/{experiment_id}/activate endpoint."""
    with patch(
        "mmm_engine.routes.get_tenant_id",
        return_value="tenant-1",
    ):
        with patch("mmm_engine.routes.activate_experiment") as mock_activate:
            mock_activate.return_value = {
                "experiment_id": "exp-1",
                "tenant_id": "tenant-1",
                "name": "Test Experiment",
                "status": "active",
                "config": {},
            }

            response = client.post(
                "/v1/mmm/experiments/exp-1/activate",
                headers={"Authorization": "Bearer token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"


def test_experiments_api_deactivate(client: TestClient) -> None:
    """Test POST /v1/mmm/experiments/{experiment_id}/deactivate endpoint."""
    with patch(
        "mmm_engine.routes.get_tenant_id",
        return_value="tenant-1",
    ):
        with patch(
            "mmm_engine.routes.deactivate_experiment"
        ) as mock_deactivate:
            mock_deactivate.return_value = {
                "experiment_id": "exp-1",
                "tenant_id": "tenant-1",
                "name": "Test Experiment",
                "status": "inactive",
                "config": {},
            }

            response = client.post(
                "/v1/mmm/experiments/exp-1/deactivate",
                headers={"Authorization": "Bearer token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "inactive"

