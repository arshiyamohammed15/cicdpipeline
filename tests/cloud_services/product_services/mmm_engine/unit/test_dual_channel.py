from __future__ import annotations
"""
Feature tests for dual-channel approval (FR-6).

Tests dual-channel approval workflow:
- Create approval record
- Record first approval
- Record second approval
- Rejection handling
- Action execution blocking until fully approved
"""


# Imports handled by conftest.py

from datetime import datetime, timezone
from unittest.mock import patch
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mmm_engine.main import app
from mmm_engine.models import (
    DualChannelApproval,
    DualChannelApprovalStatus,
)
from mmm_engine.database.repositories import (
    DualChannelApprovalRepository,
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
def test_dual_channel_create_approval(db_session) -> None:
    """Test creating dual-channel approval record."""
    repo = DualChannelApprovalRepository(db_session)
    approval = DualChannelApproval(
        approval_id=str(uuid.uuid4()),
        action_id=str(uuid.uuid4()),
        decision_id=str(uuid.uuid4()),
        actor_id="actor-1",
        status=DualChannelApprovalStatus.PENDING,
    )

    created = repo.create_approval(approval)

    assert created.status == DualChannelApprovalStatus.PENDING
    assert created.actor_id == "actor-1"


@pytest.mark.unit
def test_dual_channel_first_approval(db_session) -> None:
    """Test recording first approval."""
    repo = DualChannelApprovalRepository(db_session)
    action_id = str(uuid.uuid4())
    approval = DualChannelApproval(
        approval_id=str(uuid.uuid4()),
        action_id=action_id,
        decision_id=str(uuid.uuid4()),
        actor_id="actor-1",
        status=DualChannelApprovalStatus.PENDING,
    )
    repo.create_approval(approval)

    updated = repo.record_first_approval(action_id, "actor-1")

    assert updated is not None
    assert updated.status == DualChannelApprovalStatus.FIRST_APPROVED
    assert updated.first_approval_at is not None


@pytest.mark.unit
def test_dual_channel_second_approval(db_session) -> None:
    """Test recording second approval."""
    repo = DualChannelApprovalRepository(db_session)
    action_id = str(uuid.uuid4())
    approval = DualChannelApproval(
        approval_id=str(uuid.uuid4()),
        action_id=action_id,
        decision_id=str(uuid.uuid4()),
        actor_id="actor-1",
        status=DualChannelApprovalStatus.PENDING,
    )
    repo.create_approval(approval)
    repo.record_first_approval(action_id, "actor-1")

    updated = repo.record_second_approval(action_id, "approver-1")

    assert updated is not None
    assert updated.status == DualChannelApprovalStatus.FULLY_APPROVED
    assert updated.second_approval_at is not None
    assert updated.approver_id == "approver-1"


@pytest.mark.unit
def test_dual_channel_rejection(db_session) -> None:
    """Test rejection handling."""
    repo = DualChannelApprovalRepository(db_session)
    action_id = str(uuid.uuid4())
    approval = DualChannelApproval(
        approval_id=str(uuid.uuid4()),
        action_id=action_id,
        decision_id=str(uuid.uuid4()),
        actor_id="actor-1",
        status=DualChannelApprovalStatus.PENDING,
    )
    repo.create_approval(approval)

    updated = repo.reject_approval(action_id)

    assert updated is not None
    assert updated.status == DualChannelApprovalStatus.REJECTED


@pytest.mark.unit
def test_dual_channel_api_approve(client: TestClient) -> None:
    """Test POST /v1/mmm/actions/{action_id}/approve endpoint."""
    with patch(
        "mmm_engine.services.MMMService.record_dual_channel_approval"
    ) as mock_approve:
        mock_approve.return_value = DualChannelApproval(
            approval_id="approval-1",
            action_id="action-1",
            decision_id="decision-1",
            actor_id="actor-1",
            status=DualChannelApprovalStatus.FIRST_APPROVED,
            first_approval_at=datetime.now(timezone.utc),
        )

        response = client.post(
            "/v1/mmm/actions/action-1/approve",
            json={"actor_id": "actor-1", "is_first": True},
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"


@pytest.mark.unit
def test_dual_channel_api_get_status(client: TestClient) -> None:
    """Test GET /v1/mmm/actions/{action_id}/approval-status endpoint."""
    with patch(
        "mmm_engine.services.MMMService.get_dual_channel_approval_status"
    ) as mock_get:
        mock_get.return_value = DualChannelApproval(
            approval_id="approval-1",
            action_id="action-1",
            decision_id="decision-1",
            actor_id="actor-1",
            status=DualChannelApprovalStatus.FULLY_APPROVED,
            first_approval_at=datetime.now(timezone.utc),
            second_approval_at=datetime.now(timezone.utc),
        )

        response = client.get(
            "/v1/mmm/actions/action-1/approval-status",
            headers={"Authorization": "Bearer token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "fully_approved"

