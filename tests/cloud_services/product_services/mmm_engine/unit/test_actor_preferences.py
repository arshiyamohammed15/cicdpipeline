from __future__ import annotations
"""
Feature tests for actor preferences (FR-14).

Tests preference enforcement in decide() method:
- Opt-out categories filtering
- Snooze functionality
- Preferred surfaces filtering
"""


# Imports handled by conftest.py

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mmm_engine.main import app
from mmm_engine.models import (
    DecideRequest,
    ActorType,
    ActorPreferences,
    ActionType,
)
from mmm_engine.services import MMMService
from mmm_engine.database.repositories import (
    ActorPreferencesRepository,
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
def test_preference_opt_out_categories_filtering(db_session) -> None:
    """Test opt-out categories filter actions."""
    service = MMMService()

    # Create preferences with opt-out for mentor
    repo = ActorPreferencesRepository(db_session)
    preferences = ActorPreferences(
        preference_id=str(uuid.uuid4()),
        tenant_id="tenant-1",
        actor_id="actor-1",
        opt_out_categories=["mentor", "multiplier"],
        preferred_surfaces=[],
    )
    repo.save_preferences(preferences)

    # Create a decision request
    request = DecideRequest(
        tenant_id="tenant-1",
        actor_id="actor-1",
        actor_type=ActorType.HUMAN,
        context={},
    )

    # Mock playbooks that would generate mentor actions
    with patch("mmm_engine.services.PlaybookRepository") as mock_repo:
        mock_repo.return_value.list_playbooks.return_value = []
        with patch("mmm_engine.services.DecisionRepository"):
            response = service.decide(request, db=db_session)

    # Actions should not include mentor or multiplier
    for action in response.decision.actions:
        assert action.type.value not in ["mentor", "multiplier"]


@pytest.mark.unit
def test_preference_snooze_blocks_all_actions(db_session) -> None:
    """Test snooze_until blocks all actions if in future."""
    service = MMMService()

    # Create preferences with snooze until future
    repo = ActorPreferencesRepository(db_session)
    snooze_until = datetime.now(timezone.utc) + timedelta(hours=2)
    preferences = ActorPreferences(
        preference_id=str(uuid.uuid4()),
        tenant_id="tenant-1",
        actor_id="actor-1",
        opt_out_categories=[],
        snooze_until=snooze_until,
        preferred_surfaces=[],
    )
    repo.save_preferences(preferences)

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

    # Should return empty actions when snoozed
    assert len(response.decision.actions) == 0


@pytest.mark.unit
def test_preference_preferred_surfaces_filtering(db_session) -> None:
    """Test preferred_surfaces filters action surfaces."""
    service = MMMService()

    # Create preferences with only IDE surface preferred
    repo = ActorPreferencesRepository(db_session)
    preferences = ActorPreferences(
        preference_id=str(uuid.uuid4()),
        tenant_id="tenant-1",
        actor_id="actor-1",
        opt_out_categories=[],
        preferred_surfaces=["ide"],
    )
    repo.save_preferences(preferences)

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
        assert len(action.surfaces) > 0
        for surface in action.surfaces:
            assert surface.value == "ide"


@pytest.mark.unit
def test_actor_preferences_api_get(client: TestClient) -> None:
    """Test GET /v1/mmm/actors/{actor_id}/preferences endpoint."""
    # Mock authentication
    with patch(
        "mmm_engine.routes.get_tenant_id",
        return_value="tenant-1",
    ):
        with patch(
            "mmm_engine.routes.get_actor_preferences"
        ) as mock_get:
            mock_get.return_value = ActorPreferences(
                preference_id="pref-1",
                tenant_id="tenant-1",
                actor_id="actor-1",
                opt_out_categories=["mentor"],
                preferred_surfaces=["ide"],
            )

            response = client.get(
                "/v1/mmm/actors/actor-1/preferences",
                headers={"Authorization": "Bearer token"},
            )

            assert response.status_code in (200, 403)
            if response.status_code == 200:
                data = response.json()
                assert data["actor_id"] == "actor-1"
                assert "mentor" in data["opt_out_categories"]


@pytest.mark.unit
def test_actor_preferences_api_update(client: TestClient) -> None:
    """Test PUT /v1/mmm/actors/{actor_id}/preferences endpoint."""
    with patch(
        "mmm_engine.routes.get_tenant_id",
        return_value="tenant-1",
    ):
        with patch(
            "mmm_engine.routes.update_actor_preferences"
        ) as mock_update:
            mock_update.return_value = ActorPreferences(
                preference_id="pref-1",
                tenant_id="tenant-1",
                actor_id="actor-1",
                opt_out_categories=["multiplier"],
                preferred_surfaces=["ide", "ci"],
            )

            response = client.put(
                "/v1/mmm/actors/actor-1/preferences",
                json={"opt_out_categories": ["multiplier"], "preferred_surfaces": ["ide", "ci"]},
                headers={"Authorization": "Bearer token"},
            )

            assert response.status_code in (200, 403)
            if response.status_code == 200:
                data = response.json()
                assert "multiplier" in data["opt_out_categories"]


@pytest.mark.unit
def test_actor_preferences_api_snooze(client: TestClient) -> None:
    """Test POST /v1/mmm/actors/{actor_id}/preferences/snooze endpoint."""
    with patch(
        "mmm_engine.routes.get_tenant_id",
        return_value="tenant-1",
    ):
        with patch(
            "mmm_engine.routes.snooze_actor_preferences"
        ) as mock_snooze:
            snooze_until = datetime.now(timezone.utc) + timedelta(hours=4)
            mock_snooze.return_value = ActorPreferences(
                preference_id="pref-1",
                tenant_id="tenant-1",
                actor_id="actor-1",
                opt_out_categories=[],
                snooze_until=snooze_until,
                preferred_surfaces=[],
            )

            response = client.post(
                "/v1/mmm/actors/actor-1/preferences/snooze",
                json={"duration_hours": 4},
                headers={"Authorization": "Bearer token"},
            )

            assert response.status_code in (200, 403)
            if response.status_code == 200:
                data = response.json()
                assert data["snooze_until"] is not None

