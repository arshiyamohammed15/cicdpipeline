"""
Shared fixtures for Data Governance & Privacy tests.
"""

import pytest
from fastapi.testclient import TestClient

from data_governance_privacy.main import app  # type: ignore


@pytest.fixture(scope="session")
def test_client() -> TestClient:
    return TestClient(app)


