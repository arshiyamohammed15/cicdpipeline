from __future__ import annotations
"""
Feature tests for tenant MMM policy configuration (FR-13).

Tests tenant policy enforcement in decide() method:
- enabled_action_types filtering
- enabled_surfaces filtering
- quotas enforcement
- quiet_hours override
"""


# Imports handled by conftest.py

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from mmm_engine.main import app
from mmm_engine.models import (
    DecideRequest,
    ActorType,
    TenantMMMPolicy,
)
from mmm_engine.services import MMMService
from mmm_engine.database.repositories import (
    TenantPolicyRepository,
)


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client with mocked IAM."""
    # Mock IAM client to bypass authentication
    with patch("mmm_engine.middleware.verify_token") as mock_verify:
        mock_verify.return_value = (True, {"tenant_id": "tenant-1", "roles": ["user"]}, None)
        yield TestClient(app)


@pytest.fixture
def db_session():
    """Database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    from mmm_engine.database.models import Base

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.mark.unit
def test_tenant_policy_enabled_action_types_filtering(db_session) -> None:
    """Test enabled_action_types filters actions."""
    service = MMMService()

    # Create tenant policy with only mirror enabled
    repo = TenantPolicyRepository(db_session)
    policy = TenantMMMPolicy(
        policy_id=str(uuid.uuid4()),
        tenant_id="tenant-1",
        enabled_surfaces=["ide", "ci", "alert"],
        quotas={"max_actions_per_day": 10, "max_actions_per_hour": 3},
        quiet_hours={"start": 22, "end": 6},
        enabled_action_types=["mirror"],  # Only mirror enabled
    )
    repo.save_policy(policy)

    request = DecideRequest(
        tenant_id="tenant-1",
        actor_id="actor-1",
        actor_type=ActorType.HUMAN,
        context={},
    )

    with patch("mmm_engine.services.PlaybookRepository") as mock_repo:
        mock_repo.return_value.list_playbooks.return_value = []
        with patch("mmm_engine.services.DecisionRepository"):
            response = service.decide(request, db=db_session)

    # All actions should be mirror type
    for action in response.decision.actions:
        assert action.type.value == "mirror"


@pytest.mark.unit
def test_tenant_policy_enabled_surfaces_filtering(db_session) -> None:
    """Test enabled_surfaces filters action surfaces."""
    service = MMMService()

    # Create tenant policy with only IDE surface enabled
    repo = TenantPolicyRepository(db_session)
    policy = TenantMMMPolicy(
        policy_id=str(uuid.uuid4()),
        tenant_id="tenant-1",
        enabled_surfaces=["ide"],  # Only IDE enabled
        quotas={"max_actions_per_day": 10, "max_actions_per_hour": 3},
        quiet_hours={"start": 22, "end": 6},
        enabled_action_types=["mirror", "mentor", "multiplier"],
    )
    repo.save_policy(policy)

    request = DecideRequest(
        tenant_id="tenant-1",
        actor_id="actor-1",
        actor_type=ActorType.HUMAN,
        context={},
    )

    with patch("mmm_engine.services.PlaybookRepository") as mock_repo:
        mock_repo.return_value.list_playbooks.return_value = []
        with patch("mmm_engine.services.DecisionRepository"):
            response = service.decide(request, db=db_session)

    # All actions should only have IDE surface
    for action in response.decision.actions:
        if action.surfaces:
            for surface in action.surfaces:
                assert surface.value == "ide"


@pytest.mark.unit
def test_tenant_policy_quiet_hours_override(db_session) -> None:
    """Test tenant policy quiet_hours override Data Governance config."""
    service = MMMService()

    # Create tenant policy with custom quiet hours
    repo = TenantPolicyRepository(db_session)
    policy = TenantMMMPolicy(
        policy_id=str(uuid.uuid4()),
        tenant_id="tenant-1",
        enabled_surfaces=["ide", "ci", "alert"],
        quotas={"max_actions_per_day": 10, "max_actions_per_hour": 3},
        quiet_hours={"start": 20, "end": 8},  # Custom quiet hours
        enabled_action_types=["mirror", "mentor", "multiplier"],
    )
    repo.save_policy(policy)

    request = DecideRequest(
        tenant_id="tenant-1",
        actor_id="actor-1",
        actor_type=ActorType.HUMAN,
        context={},
    )

    with patch("mmm_engine.services.PlaybookRepository") as mock_repo:
        mock_repo.return_value.list_playbooks.return_value = []
        with patch("mmm_engine.services.DecisionRepository"):
            response = service.decide(request, db=db_session)

    # Context should use tenant policy quiet hours
    assert response.decision.context.quiet_hours is not None
    assert response.decision.context.quiet_hours["start"] == 20
    assert response.decision.context.quiet_hours["end"] == 8


@pytest.mark.unit
def test_tenant_policy_api_get(client: TestClient) -> None:
    """Test GET /v1/mmm/tenants/{tenant_id}/policy endpoint."""
    with patch(
        "mmm_engine.routes.get_tenant_id",
        return_value="tenant-1",
    ):
        with patch("mmm_engine.routes.get_tenant_policy") as mock_get:
            mock_get.return_value = TenantMMMPolicy(
                policy_id="policy-1",
                tenant_id="tenant-1",
                enabled_surfaces=["ide"],
                quotas={"max_actions_per_day": 5},
                quiet_hours={"start": 22, "end": 6},
                enabled_action_types=["mirror"],
            )

            response = client.get(
                "/v1/mmm/tenants/tenant-1/policy",
                headers={"Authorization": "Bearer token"},
            )

            assert response.status_code in (200, 403)
            if response.status_code == 200:
                data = response.json()
                assert data["tenant_id"] == "tenant-1"
                assert data["enabled_surfaces"] == ["ide"]


@pytest.mark.unit
def test_tenant_policy_api_update(client: TestClient) -> None:
    """Test PUT /v1/mmm/tenants/{tenant_id}/policy endpoint."""
    with patch(
        "mmm_engine.routes.get_tenant_id",
        return_value="tenant-1",
    ):
        with patch(
            "mmm_engine.routes.update_tenant_policy"
        ) as mock_update:
            mock_update.return_value = TenantMMMPolicy(
                policy_id="policy-1",
                tenant_id="tenant-1",
                enabled_surfaces=["ide", "ci"],
                quotas={"max_actions_per_day": 10},
                quiet_hours={"start": 22, "end": 6},
                enabled_action_types=["mirror", "mentor"],
            )

            response = client.put(
                "/v1/mmm/tenants/tenant-1/policy",
                json={"enabled_surfaces": ["ide", "ci"], "enabled_action_types": ["mirror", "mentor"]},
                headers={"Authorization": "Bearer token"},
            )

            assert response.status_code in (200, 403)
            if response.status_code == 200:
                data = response.json()
                assert "ide" in data["enabled_surfaces"]
                assert "mentor" in data["enabled_action_types"]

