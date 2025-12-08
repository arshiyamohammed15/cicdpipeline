"""
Unit Tests for Detection Engine Core Routes

Tests route handlers per PRD §3.7
Coverage: 100% of routes.py - every route, every branch, every line
"""


# Imports handled by conftest.py
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Module setup handled by root conftest.py.parent.parent))

from detection_engine_core.routes import (
    router, get_service, get_tenant_id,
    evaluate_decision, submit_feedback, health_check, readiness_check
)
from detection_engine_core.models import (
    DecisionRequest, DecisionResponse, EvaluationPoint, DecisionStatus,
    FeedbackRequest, FeedbackResponse, HealthResponse, ReadinessResponse
)
import detection_engine_core.models as dec_models
import sys
sys.modules["models"] = dec_models
from detection_engine_core.services import DetectionEngineService


class TestGetService:
    """Test get_service dependency"""

    def test_get_service_returns_service_instance(self):
        """Test that get_service returns DetectionEngineService instance"""
        # Clear global service
        import routes
        routes._service = None

        service = get_service()

        assert isinstance(service, DetectionEngineService)

    def test_get_service_caches_service_instance(self):
        """Test that get_service caches service instance"""
        import routes
        routes._service = None

        service1 = get_service()
        service2 = get_service()

        assert service1 is service2


class TestGetTenantId:
    """Test get_tenant_id dependency"""

    def test_get_tenant_id_with_bearer_token(self):
        """Test get_tenant_id with Bearer token"""
        authorization = "Bearer test-token"

        tenant_id = get_tenant_id(authorization)

        assert tenant_id == "default-tenant"

    def test_get_tenant_id_without_bearer_prefix(self):
        """Test get_tenant_id without Bearer prefix"""
        authorization = "test-token"

        tenant_id = get_tenant_id(authorization)

        assert tenant_id == "default-tenant"

    def test_get_tenant_id_without_authorization(self):
        """Test get_tenant_id without authorization header"""
        with pytest.raises(HTTPException) as exc_info:
            get_tenant_id(None)

        assert exc_info.value.status_code == 401
        assert "Authorization header required" in exc_info.value.detail

    def test_get_tenant_id_with_invalid_token(self):
        """Test get_tenant_id with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            get_tenant_id("invalid")

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    def test_get_tenant_id_with_empty_token(self):
        """Test get_tenant_id with empty token"""
        with pytest.raises(HTTPException) as exc_info:
            get_tenant_id("Bearer ")

        assert exc_info.value.status_code == 401


class TestEvaluateDecisionRoute:
    """Test evaluate_decision route handler"""

    @pytest.fixture
    def mock_service(self):
        """Create mock service"""
        service = MagicMock(spec=DetectionEngineService)
        return service

    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        return DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'risk_score': 0.1},
            actor={'repo_id': 'test-repo'}
        )

    @pytest.mark.asyncio
    async def test_evaluate_decision_success(self, mock_service, mock_request):
        """Test successful decision evaluation"""
        from models import DecisionReceiptModel, EvaluationPoint

        mock_receipt = DecisionReceiptModel(
            receipt_id="test-id",
            gate_id="detection-engine-core",
            policy_version_ids=["POL-001"],
            snapshot_hash="sha256:test",
            timestamp_utc="2025-01-01T00:00:00Z",
            timestamp_monotonic_ms=1000,
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            decision={"status": "pass"},
            evidence_handles=[],
            actor={"repo_id": "test-repo"},
            signature="test-signature"
        )

        mock_response = DecisionResponse(
            receipt=mock_receipt,
            confidence=0.95,
            accuracy_metrics={}
        )
        mock_service.evaluate_decision.return_value = mock_response

        response = await evaluate_decision(mock_request, "test-tenant", mock_service)

        assert response == mock_response
        mock_service.evaluate_decision.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_evaluate_decision_with_exception(self, mock_service, mock_request):
        """Test decision evaluation with exception"""
        mock_service.evaluate_decision.side_effect = Exception("Test error")

        from fastapi.responses import JSONResponse
        from models import DecisionResponseError

        response = await evaluate_decision(mock_request, "test-tenant", mock_service)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500


class TestSubmitFeedbackRoute:
    """Test submit_feedback route handler"""

    @pytest.fixture
    def mock_service(self):
        """Create mock service"""
        service = MagicMock(spec=DetectionEngineService)
        return service

    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        return FeedbackRequest(
            decision_receipt_id='test-receipt-id',
            pattern_id='FB-01',
            choice='worked',
            tags=[],
            actor={'repo_id': 'test-repo'}
        )

    @pytest.mark.asyncio
    async def test_submit_feedback_success(self, mock_service, mock_request):
        """Test successful feedback submission"""
        mock_response = FeedbackResponse(
            feedback_id='test-feedback-id',
            status='accepted',
            message='Success'
        )
        mock_service.submit_feedback.return_value = mock_response

        response = await submit_feedback(mock_request, "test-tenant", mock_service)

        assert response == mock_response
        mock_service.submit_feedback.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_submit_feedback_with_exception(self, mock_service, mock_request):
        """Test feedback submission with exception"""
        mock_service.submit_feedback.side_effect = Exception("Test error")

        with pytest.raises(HTTPException) as exc_info:
            await submit_feedback(mock_request, "test-tenant", mock_service)

        assert exc_info.value.status_code == 500
        assert "Test error" in str(exc_info.value.detail)


class TestHealthCheckRoute:
    """Test health_check route handler"""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self):
        """Test that health_check returns healthy status"""
        response = await health_check()

        assert isinstance(response, HealthResponse)
        assert response.status == "healthy"


class TestReadinessCheckRoute:
    """Test readiness_check route handler"""

    @pytest.mark.asyncio
    async def test_readiness_check_returns_ready(self):
        """Test that readiness_check returns ready status"""
        response = await readiness_check()

        assert isinstance(response, ReadinessResponse)
        assert response.ready is True
        assert isinstance(response.checks, dict)
        assert response.checks.get("service") is True
        assert response.checks.get("detection_engine") is True
        assert response.timestamp is not None


class TestRouterIntegration:
    """Test router integration"""

    def test_router_has_correct_prefix(self):
        """Test that router has correct prefix"""
        assert router.prefix == "/v1"

    def test_router_has_correct_tags(self):
        """Test that router has correct tags"""
        assert "detection-engine-core" in router.tags

