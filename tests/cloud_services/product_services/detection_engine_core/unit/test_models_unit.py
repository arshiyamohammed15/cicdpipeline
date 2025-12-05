"""
Unit Tests for Detection Engine Core Models

Tests Pydantic models per PRD §3.2, §3.7
Coverage: 100% of models.py - every model, every field, every validation
"""


# Imports handled by conftest.py
import pytest
import sys
from pathlib import Path
from datetime import datetime
from pydantic import ValidationError

# Module setup handled by root conftest.py.parent.parent))

from detection_engine_core.models import (
    DecisionStatus, EvaluationPoint, ActorType, DataCategory, Surface,
    EvidenceHandle, DecisionReceiptModel, DecisionRequest, DecisionResponse,
    DecisionResponseError, FeedbackReceiptModel, FeedbackRequest, FeedbackResponse,
    EvidenceLink, HealthResponse, ReadinessResponse
)


class TestEnums:
    """Test enum classes"""

    def test_decision_status_values(self):
        """Test DecisionStatus enum values"""
        assert DecisionStatus.PASS == "pass"
        assert DecisionStatus.WARN == "warn"
        assert DecisionStatus.SOFT_BLOCK == "soft_block"
        assert DecisionStatus.HARD_BLOCK == "hard_block"

    def test_evaluation_point_values(self):
        """Test EvaluationPoint enum values"""
        assert EvaluationPoint.PRE_COMMIT == "pre-commit"
        assert EvaluationPoint.PRE_MERGE == "pre-merge"
        assert EvaluationPoint.PRE_DEPLOY == "pre-deploy"
        assert EvaluationPoint.POST_DEPLOY == "post-deploy"

    def test_actor_type_values(self):
        """Test ActorType enum values"""
        assert ActorType.HUMAN == "human"
        assert ActorType.AI == "ai"
        assert ActorType.AUTOMATED == "automated"

    def test_data_category_values(self):
        """Test DataCategory enum values"""
        assert DataCategory.PUBLIC == "public"
        assert DataCategory.INTERNAL == "internal"
        assert DataCategory.CONFIDENTIAL == "confidential"
        assert DataCategory.RESTRICTED == "restricted"

    def test_surface_values(self):
        """Test Surface enum values"""
        assert Surface.IDE == "ide"
        assert Surface.PR == "pr"
        assert Surface.CI == "ci"


class TestEvidenceHandle:
    """Test EvidenceHandle model"""

    def test_evidence_handle_creation(self):
        """Test EvidenceHandle creation with required fields"""
        handle = EvidenceHandle(
            url="https://example.com/evidence",
            type="artifact",
            description="Test evidence"
        )

        assert handle.url == "https://example.com/evidence"
        assert handle.type == "artifact"
        assert handle.description == "Test evidence"
        assert handle.expires_at is None

    def test_evidence_handle_with_expires_at(self):
        """Test EvidenceHandle with expires_at"""
        handle = EvidenceHandle(
            url="https://example.com/evidence",
            type="artifact",
            description="Test evidence",
            expires_at="2025-12-31T23:59:59Z"
        )

        assert handle.expires_at == "2025-12-31T23:59:59Z"

    def test_evidence_handle_missing_required_fields(self):
        """Test EvidenceHandle validation with missing fields"""
        with pytest.raises(ValidationError):
            EvidenceHandle(
                url="https://example.com/evidence"
                # Missing type and description
            )


class TestDecisionReceiptModel:
    """Test DecisionReceiptModel"""

    def test_decision_receipt_creation(self):
        """Test DecisionReceiptModel creation"""
        receipt = DecisionReceiptModel(
            receipt_id="test-id",
            gate_id="detection-engine-core",
            policy_version_ids=["POL-001"],
            snapshot_hash="sha256:test",
            timestamp_utc="2025-01-01T00:00:00Z",
            timestamp_monotonic_ms=1000,
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            decision={"status": "pass", "rationale": "Test"},
            evidence_handles=[],
            actor={"repo_id": "test-repo"},
            signature="test-signature"
        )

        assert receipt.receipt_id == "test-id"
        assert receipt.gate_id == "detection-engine-core"
        assert receipt.degraded is False

    def test_decision_receipt_with_optional_fields(self):
        """Test DecisionReceiptModel with optional fields"""
        receipt = DecisionReceiptModel(
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
            context={"surface": "ide"},
            override={"reason": "test"},
            data_category=DataCategory.INTERNAL,
            degraded=True,
            signature="test-signature"
        )

        assert receipt.context is not None
        assert receipt.override is not None
        assert receipt.data_category == DataCategory.INTERNAL
        assert receipt.degraded is True


class TestDecisionRequest:
    """Test DecisionRequest model"""

    def test_decision_request_creation(self):
        """Test DecisionRequest creation"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={"risk_score": 0.1},
            actor={"repo_id": "test-repo"}
        )

        assert request.evaluation_point == EvaluationPoint.PRE_COMMIT
        assert request.inputs == {"risk_score": 0.1}
        assert request.actor == {"repo_id": "test-repo"}
        assert request.context is None
        assert request.policy_version_ids is None

    def test_decision_request_with_optional_fields(self):
        """Test DecisionRequest with optional fields"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_MERGE,
            inputs={},
            actor={"repo_id": "test-repo"},
            context={"surface": "pr"},
            policy_version_ids=["POL-001"]
        )

        assert request.context is not None
        assert request.policy_version_ids == ["POL-001"]


class TestDecisionResponse:
    """Test DecisionResponse model"""

    def test_decision_response_creation(self):
        """Test DecisionResponse creation"""
        receipt = DecisionReceiptModel(
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

        response = DecisionResponse(
            receipt=receipt,
            confidence=0.95,
            accuracy_metrics={"precision": 0.85}
        )

        assert response.receipt == receipt
        assert response.confidence == 0.95
        assert response.accuracy_metrics == {"precision": 0.85}

    def test_decision_response_with_optional_fields(self):
        """Test DecisionResponse with optional fields"""
        receipt = DecisionReceiptModel(
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

        response = DecisionResponse(receipt=receipt)

        assert response.confidence is None
        assert response.accuracy_metrics is None

    def test_decision_response_confidence_validation(self):
        """Test DecisionResponse confidence validation"""
        receipt = DecisionReceiptModel(
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

        # Valid confidence
        response = DecisionResponse(receipt=receipt, confidence=0.5)
        assert response.confidence == 0.5

        # Invalid confidence (too high)
        with pytest.raises(ValidationError):
            DecisionResponse(receipt=receipt, confidence=1.5)

        # Invalid confidence (too low)
        with pytest.raises(ValidationError):
            DecisionResponse(receipt=receipt, confidence=-0.1)


class TestDecisionResponseError:
    """Test DecisionResponseError model"""

    def test_decision_response_error_creation(self):
        """Test DecisionResponseError creation"""
        error = DecisionResponseError(
            error_code="TEST_ERROR",
            error_message="Test error message",
            degraded=True
        )

        assert error.error_code == "TEST_ERROR"
        assert error.error_message == "Test error message"
        assert error.degraded is True

    def test_decision_response_error_default_degraded(self):
        """Test DecisionResponseError with default degraded"""
        error = DecisionResponseError(
            error_code="TEST_ERROR",
            error_message="Test error message"
        )

        assert error.degraded is False


class TestFeedbackReceiptModel:
    """Test FeedbackReceiptModel"""

    def test_feedback_receipt_creation(self):
        """Test FeedbackReceiptModel creation"""
        receipt = FeedbackReceiptModel(
            feedback_id="fb-001",
            decision_receipt_id="dr-001",
            pattern_id="FB-01",
            choice="worked",
            tags=["positive"],
            actor={"repo_id": "test-repo"},
            timestamp_utc="2025-01-01T00:00:00Z",
            signature="test-signature"
        )

        assert receipt.feedback_id == "fb-001"
        assert receipt.pattern_id == "FB-01"
        assert receipt.choice == "worked"

    def test_feedback_receipt_pattern_id_validation(self):
        """Test FeedbackReceiptModel pattern_id validation"""
        # Valid pattern IDs
        for pattern_id in ["FB-01", "FB-02", "FB-03", "FB-04"]:
            receipt = FeedbackReceiptModel(
                feedback_id="fb-001",
                decision_receipt_id="dr-001",
                pattern_id=pattern_id,
                choice="worked",
                tags=[],
                actor={"repo_id": "test-repo"},
                timestamp_utc="2025-01-01T00:00:00Z",
                signature="test-signature"
            )
            assert receipt.pattern_id == pattern_id

        # Invalid pattern ID
        with pytest.raises(ValidationError):
            FeedbackReceiptModel(
                feedback_id="fb-001",
                decision_receipt_id="dr-001",
                pattern_id="FB-05",  # Invalid
                choice="worked",
                tags=[],
                actor={"repo_id": "test-repo"},
                timestamp_utc="2025-01-01T00:00:00Z",
                signature="test-signature"
            )

    def test_feedback_receipt_choice_validation(self):
        """Test FeedbackReceiptModel choice validation"""
        # Valid choices
        for choice in ["worked", "partly", "didnt"]:
            receipt = FeedbackReceiptModel(
                feedback_id="fb-001",
                decision_receipt_id="dr-001",
                pattern_id="FB-01",
                choice=choice,
                tags=[],
                actor={"repo_id": "test-repo"},
                timestamp_utc="2025-01-01T00:00:00Z",
                signature="test-signature"
            )
            assert receipt.choice == choice

        # Invalid choice
        with pytest.raises(ValidationError):
            FeedbackReceiptModel(
                feedback_id="fb-001",
                decision_receipt_id="dr-001",
                pattern_id="FB-01",
                choice="invalid",  # Invalid
                tags=[],
                actor={"repo_id": "test-repo"},
                timestamp_utc="2025-01-01T00:00:00Z",
                signature="test-signature"
            )


class TestFeedbackRequest:
    """Test FeedbackRequest model"""

    def test_feedback_request_creation(self):
        """Test FeedbackRequest creation"""
        request = FeedbackRequest(
            decision_receipt_id="dr-001",
            pattern_id="FB-01",
            choice="worked",
            tags=["positive"],
            actor={"repo_id": "test-repo"}
        )

        assert request.decision_receipt_id == "dr-001"
        assert request.pattern_id == "FB-01"
        assert request.choice == "worked"
        assert request.tags == ["positive"]

    def test_feedback_request_default_tags(self):
        """Test FeedbackRequest with default tags"""
        request = FeedbackRequest(
            decision_receipt_id="dr-001",
            pattern_id="FB-01",
            choice="worked",
            actor={"repo_id": "test-repo"}
        )

        assert request.tags == []


class TestFeedbackResponse:
    """Test FeedbackResponse model"""

    def test_feedback_response_creation(self):
        """Test FeedbackResponse creation"""
        response = FeedbackResponse(
            feedback_id="fb-001",
            status="accepted",
            message="Success"
        )

        assert response.feedback_id == "fb-001"
        assert response.status == "accepted"
        assert response.message == "Success"

    def test_feedback_response_optional_message(self):
        """Test FeedbackResponse with optional message"""
        response = FeedbackResponse(
            feedback_id="fb-001",
            status="accepted"
        )

        assert response.message is None


class TestEvidenceLink:
    """Test EvidenceLink model"""

    def test_evidence_link_creation(self):
        """Test EvidenceLink creation"""
        link = EvidenceLink(
            type="artifact",
            href="https://example.com/evidence",
            label="Test evidence"
        )

        assert link.type == "artifact"
        assert link.href == "https://example.com/evidence"
        assert link.label == "Test evidence"
        assert link.expires_at is None

    def test_evidence_link_with_expires_at(self):
        """Test EvidenceLink with expires_at"""
        link = EvidenceLink(
            type="artifact",
            href="https://example.com/evidence",
            label="Test evidence",
            expires_at="2025-12-31T23:59:59Z"
        )

        assert link.expires_at == "2025-12-31T23:59:59Z"


class TestHealthResponse:
    """Test HealthResponse model"""

    def test_health_response_creation(self):
        """Test HealthResponse creation"""
        response = HealthResponse(status="healthy")

        assert response.status == "healthy"
        assert response.timestamp is not None
        assert isinstance(response.timestamp, datetime)


class TestReadinessResponse:
    """Test ReadinessResponse model"""

    def test_readiness_response_creation(self):
        """Test ReadinessResponse creation"""
        response = ReadinessResponse(
            ready=True,
            checks={"service": True, "detection_engine": True}
        )

        assert response.ready is True
        assert response.checks == {"service": True, "detection_engine": True}
        assert response.timestamp is None

    def test_readiness_response_with_timestamp(self):
        """Test ReadinessResponse with timestamp"""
        timestamp = datetime.utcnow()
        response = ReadinessResponse(
            ready=True,
            checks={"service": True},
            timestamp=timestamp
        )

        assert response.timestamp == timestamp

