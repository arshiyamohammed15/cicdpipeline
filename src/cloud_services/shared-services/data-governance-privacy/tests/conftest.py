"""
Shared fixtures for Data Governance & Privacy tests.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from data_governance_privacy.main import app  # type: ignore
from data_governance_privacy.services import DataGovernanceService  # type: ignore
from data_governance_privacy.tests.harness import (
    TenantFactory,
    IAMTokenFactory,
    ClassificationPayloadFactory,
    ConsentStateFactory,
    RetentionPolicyFactory,
    PerfRunner,
)


@pytest.fixture(scope="session")
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def tenant_factory() -> TenantFactory:
    return TenantFactory()


@pytest.fixture(scope="session")
def token_factory() -> IAMTokenFactory:
    return IAMTokenFactory()


@pytest.fixture(scope="session")
def classification_factory() -> ClassificationPayloadFactory:
    return ClassificationPayloadFactory()


@pytest.fixture(scope="session")
def consent_factory() -> ConsentStateFactory:
    return ConsentStateFactory()


@pytest.fixture(scope="session")
def retention_policy_factory() -> RetentionPolicyFactory:
    return RetentionPolicyFactory()


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Create an event loop for async performance suites."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def perf_runner(event_loop: asyncio.AbstractEventLoop) -> PerfRunner:
    return PerfRunner(loop=event_loop)


@pytest.fixture()
def governance_service() -> DataGovernanceService:
    return DataGovernanceService()


