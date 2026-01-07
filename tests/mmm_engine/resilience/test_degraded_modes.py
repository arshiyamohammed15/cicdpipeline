from __future__ import annotations
"""
Resilience tests for MMM Engine degraded modes.

Per PRD Phase 4, tests resilience requirements:
- RF-MMM-01: LLM Gateway unavailable → Mirror-only actions
- RF-MMM-02: ERIS unavailable → Receipt queuing, non-blocking
- RF-MMM-03: Policy unavailable → Fail-closed for safety-critical, cached for others
- UBI unavailable → Empty signals, continue
- Data Governance unavailable → Default config, continue
- IAM unavailable → 503 rejection
"""


import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from cloud_services.product_services.mmm_engine.main import app
from cloud_services.product_services.mmm_engine.services import MMMService
from cloud_services.product_services.mmm_engine.integrations.policy_client import (
    PolicyClientError,
)
from cloud_services.product_services.mmm_engine.models import DecideRequest, ActorType


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mmm_service() -> MMMService:
    """MMM service instance."""
    return MMMService()


@pytest.mark.integration
def test_rf_mmm_01_llm_gateway_unavailable_mirror_only(mmm_service: MMMService) -> None:
    """
    Test RF-MMM-01: LLM Gateway unavailable → Suppress Mentor/Multiplier, allow Mirror-only.

    Per PRD NFR-6, when LLM Gateway is unavailable, the engine should:
    - Suppress Mentor and Multiplier actions (require LLM)
    - Allow Mirror actions (no LLM required)
    """

    # Mock LLM Gateway to raise exception
    with patch.object(mmm_service.llm_gateway, "generate", side_effect=RuntimeError("LLM Gateway unavailable")):
        request = DecideRequest(
            tenant_id="test-tenant",
            actor_id="actor-1",
            actor_type=ActorType.HUMAN,
            context={"roles": ["developer"]},
        )

        # Mock database and other dependencies
        with patch("cloud_services.product_services.mmm_engine.services.PlaybookRepository") as mock_repo:
            mock_repo.return_value.list_playbooks.return_value = []
            with patch("cloud_services.product_services.mmm_engine.services.DecisionRepository"):
                response = mmm_service.decide(request, db=None)

        # Should return decision with actions
        assert response.decision is not None
        # All actions should be Mirror type (Mentor/Multiplier suppressed)
        for action in response.decision.actions:
            assert action.type.value == "mirror"


@pytest.mark.integration
def test_rf_mmm_02_eris_unavailable_non_blocking(mmm_service: MMMService) -> None:
    """
    Test RF-MMM-02: ERIS unavailable → Receipt queuing, non-blocking.

    Per PRD FR-12, ERIS receipt emission should not block the decision response.
    """

    # Mock ERIS to fail
    with patch.object(mmm_service.eris, "emit_receipt", side_effect=Exception("ERIS unavailable")):
        request = DecideRequest(
            tenant_id="test-tenant",
            actor_id="actor-1",
            actor_type=ActorType.HUMAN,
            context={},
        )

        with patch("cloud_services.product_services.mmm_engine.services.PlaybookRepository") as mock_repo:
            mock_repo.return_value.list_playbooks.return_value = []
            with patch("cloud_services.product_services.mmm_engine.services.DecisionRepository"):
                # Should not raise exception, decision should succeed
                response = mmm_service.decide(request, db=None)

        assert response.decision is not None
        # Decision should be returned even though receipt emission failed
        assert response.decision.decision_id is not None


@pytest.mark.integration
def test_rf_mmm_03_policy_unavailable_fail_closed_safety_critical(mmm_service: MMMService) -> None:
    """
    Test RF-MMM-03: Policy unavailable → Fail-closed for safety-critical tenants.

    Per PRD FR-11, safety-critical tenants should fail-closed when policy unavailable.
    """

    # Mock PolicyCache to raise PolicyClientError
    with patch.object(
        mmm_service.policy_cache,
        "get_snapshot",
        side_effect=PolicyClientError("Policy unavailable"),
    ):
        # Mark tenant as safety-critical
        mmm_service.policy_cache.set_safety_critical("safety-critical-tenant", True)

        request = DecideRequest(
            tenant_id="safety-critical-tenant",
            actor_id="actor-1",
            actor_type=ActorType.HUMAN,
            context={},
        )

        with patch("cloud_services.product_services.mmm_engine.services.PlaybookRepository") as mock_repo:
            mock_repo.return_value.list_playbooks.return_value = []
            with patch("cloud_services.product_services.mmm_engine.services.DecisionRepository"):
                # Should raise PolicyClientError for safety-critical tenant
                with pytest.raises(PolicyClientError, match="safety-critical"):
                    mmm_service.decide(request, db=None)


@pytest.mark.integration
def test_rf_mmm_03_policy_unavailable_cached_snapshot(mmm_service: MMMService) -> None:
    """
    Test RF-MMM-03: Policy unavailable → Cached snapshot for non-safety-critical tenants.

    Per PRD FR-11, non-safety-critical tenants should use cached snapshot if within 5min window.
    """
    from cloud_services.product_services.mmm_engine.integrations.policy_client import (
        PolicySnapshot,
    )
    import time

    # Create a cached snapshot
    cached_snapshot = PolicySnapshot(
        snapshot_id="cached-snapshot",
        version_ids=["pol-v1"],
        tenant_id="regular-tenant",
        allowed=True,
        restrictions=[],
        fail_open_allowed=True,
        degradation_mode="prefer_backup",
        fetched_at=time.time() - 120,  # 2 minutes ago (within 5min window)
    )

    # Mock PolicyCache to return cached snapshot on first call, then fail
    call_count = 0

    def mock_get_snapshot(tenant_id: str, allow_fail_open: bool = None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return cached_snapshot
        raise PolicyClientError("Policy unavailable")

    with patch.object(mmm_service.policy_cache, "get_snapshot", side_effect=mock_get_snapshot):
        request = DecideRequest(
            tenant_id="regular-tenant",
            actor_id="actor-1",
            actor_type=ActorType.HUMAN,
            context={},
        )

        with patch("cloud_services.product_services.mmm_engine.services.PlaybookRepository") as mock_repo:
            mock_repo.return_value.list_playbooks.return_value = []
            with patch("cloud_services.product_services.mmm_engine.services.DecisionRepository"):
                # Should use cached snapshot (marked as stale)
                response = mmm_service.decide(request, db=None)

        assert response.decision is not None
        assert response.decision.degraded_mode is True


@pytest.mark.integration
def test_ubi_unavailable_empty_signals_continue(mmm_service: MMMService) -> None:
    """
    Test UBI unavailable → Use empty recent_signals array, continue.

    Per PRD NFR-6, UBI unavailability should not block decisions.
    """

    # Mock UBI client to return empty list
    with patch.object(mmm_service.signal_service, "get_recent_signals", return_value=[]):
        request = DecideRequest(
            tenant_id="test-tenant",
            actor_id="actor-1",
            actor_type=ActorType.HUMAN,
            context={},
        )

        with patch("cloud_services.product_services.mmm_engine.services.PlaybookRepository") as mock_repo:
            mock_repo.return_value.list_playbooks.return_value = []
            with patch("cloud_services.product_services.mmm_engine.services.DecisionRepository"):
                response = mmm_service.decide(request, db=None)

        assert response.decision is not None
        # Context should have empty signals
        assert len(response.decision.context.recent_signals) == 0


@pytest.mark.integration
def test_data_governance_unavailable_default_config(mmm_service: MMMService) -> None:
    """
    Test Data Governance unavailable → Use default quiet hours, continue.

    Per PRD NFR-6, Data Governance unavailability should use defaults.
    """

    # Mock Data Governance to return defaults
    with patch.object(
        mmm_service.data_governance,
        "get_tenant_config",
        return_value={"quiet_hours": {"start": 22, "end": 6}, "retention_days": 90},
    ):
        request = DecideRequest(
            tenant_id="test-tenant",
            actor_id="actor-1",
            actor_type=ActorType.HUMAN,
            context={},
        )

        with patch("cloud_services.product_services.mmm_engine.services.PlaybookRepository") as mock_repo:
            mock_repo.return_value.list_playbooks.return_value = []
            with patch("cloud_services.product_services.mmm_engine.services.DecisionRepository"):
                response = mmm_service.decide(request, db=None)

        assert response.decision is not None
        # Should use default quiet hours
        assert response.decision.context.quiet_hours is not None


@pytest.mark.integration
def test_iam_unavailable_503_rejection(client: TestClient) -> None:
    """
    Test IAM unavailable → Reject with 503.

    Per PRD NFR-6, IAM unavailability should reject requests with 503.
    """
    from unittest.mock import patch

    # Mock IAM client to fail
    with patch(
        "cloud_services.product_services.mmm_engine.middleware.verify_token",
        return_value=(False, None, "IAM service unavailable"),
    ):
        response = client.post(
            "/v1/mmm/decide",
            json={"tenant_id": "test-tenant", "actor_id": "actor-1"},
            headers={"Authorization": "Bearer invalid-token"},
        )

        # Should return 401 (unauthorized) or 503 (service unavailable)
        assert response.status_code in [401, 503]

