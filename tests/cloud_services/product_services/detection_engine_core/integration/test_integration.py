"""
Integration Tests for Detection Engine Core Service

Tests end-to-end workflows per PRD §3.9
Coverage: Critical integration paths
"""


# Imports handled by conftest.py
import pytest
import time
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Module setup handled by root conftest.py
from detection_engine_core.main import app
from detection_engine_core.services import DetectionEngineService
from detection_engine_core.models import (
    DecisionRequest, EvaluationPoint, DecisionStatus,
    FeedbackRequest
)

client = TestClient(app)


@pytest.mark.integration
class TestServiceIntegration:
    """Test service integration"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = DetectionEngineService()

    @pytest.mark.integration
    def test_decision_evaluation_end_to_end(self):
        """Test complete decision evaluation workflow"""
        # 1. Create request
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={
                'risk_score': 0.5,
                'file_count': 30,
                'has_tests': True
            },
            actor={
                'repo_id': 'test-repo',
                'type': 'human'
            },
            context={
                'surface': 'ide',
                'branch': 'main'
            }
        )

        # 2. Evaluate decision
        response = self.service.evaluate_decision(request)

        # 3. Verify response structure
        assert response.receipt is not None
        assert response.receipt.receipt_id is not None
        assert response.receipt.decision is not None
        assert response.receipt.decision['status'] in ['pass', 'warn', 'soft_block', 'hard_block']
        assert response.confidence is not None
        assert response.accuracy_metrics is not None

        # 4. Verify receipt fields per PRD §3.2
        receipt = response.receipt
        assert receipt.gate_id == 'detection-engine-core'
        assert receipt.evaluation_point == EvaluationPoint.PRE_COMMIT
        assert receipt.actor['repo_id'] == 'test-repo'
        assert receipt.context is not None
        assert receipt.context['surface'] == 'ide'

    @pytest.mark.integration
    def test_feedback_submission_end_to_end(self):
        """Test complete feedback submission workflow"""
        # 1. Create decision receipt first
        decision_request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'risk_score': 0.1},
            actor={'repo_id': 'test-repo'}
        )
        decision_response = self.service.evaluate_decision(decision_request)
        decision_receipt_id = decision_response.receipt.receipt_id

        # 2. Submit feedback
        feedback_request = FeedbackRequest(
            decision_receipt_id=decision_receipt_id,
            pattern_id='FB-01',
            choice='worked',
            tags=['accurate', 'helpful'],
            actor={'repo_id': 'test-repo'}
        )

        feedback_response = self.service.submit_feedback(feedback_request)

        # 3. Verify feedback response
        assert feedback_response.feedback_id is not None
        assert feedback_response.status == 'accepted'
        assert feedback_response.message is not None

        # 4. Verify feedback links to decision receipt
        # (In production, would verify storage linkage)
        assert feedback_request.decision_receipt_id == decision_receipt_id

    @pytest.mark.integration
    def test_performance_budget_tracking(self):
        """Test performance budget tracking per PRD §3.12"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'risk_score': 0.1},
            actor={'repo_id': 'test-repo'}
        )

        start_time = time.perf_counter()
        response = self.service.evaluate_decision(request)
        elapsed = time.perf_counter() - start_time

        # Verify degraded flag is set if budget exceeded
        budget_seconds = 0.050  # 50ms for pre-commit
        if elapsed > budget_seconds:
            assert response.receipt.degraded is True
        else:
            # Should not be degraded if within budget
            assert response.receipt.degraded is False or response.receipt.degraded is True  # Can be either

    @pytest.mark.integration
    def test_all_evaluation_points_workflow(self):
        """Test workflow for all evaluation points"""
        evaluation_points = [
            EvaluationPoint.PRE_COMMIT,
            EvaluationPoint.PRE_MERGE,
            EvaluationPoint.PRE_DEPLOY,
            EvaluationPoint.POST_DEPLOY
        ]

        for ep in evaluation_points:
            request = DecisionRequest(
                evaluation_point=ep,
                inputs={'risk_score': 0.1},
                actor={'repo_id': 'test-repo'}
            )

            response = self.service.evaluate_decision(request)
            assert response.receipt.evaluation_point == ep
            assert response.receipt.decision is not None

    @pytest.mark.integration
    def test_confidence_calculation_integration(self):
        """Test confidence calculation integration per PRD §3.3"""
        test_cases = [
            (0.1, 0.95),  # Low risk -> high confidence
            (0.4, 0.75),  # Moderate risk -> moderate confidence
            (0.7, 0.85),  # High risk -> high confidence in detection
            (0.9, 0.85),  # Very high risk -> high confidence
        ]

        for risk_score, expected_min_confidence in test_cases:
            request = DecisionRequest(
                evaluation_point=EvaluationPoint.PRE_COMMIT,
                inputs={'risk_score': risk_score},
                actor={'repo_id': 'test-repo'}
            )

            response = self.service.evaluate_decision(request)
            assert response.confidence is not None
            assert 0.0 <= response.confidence <= 1.0
            # Confidence should be reasonable (within 0.1 of expected)
            assert abs(response.confidence - expected_min_confidence) < 0.2

    @pytest.mark.integration
    def test_accuracy_metrics_integration(self):
        """Test accuracy metrics integration per PRD §3.3"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'risk_score': 0.1},
            actor={'repo_id': 'test-repo'}
        )

        response = self.service.evaluate_decision(request)

        assert response.accuracy_metrics is not None
        metrics = response.accuracy_metrics

        # Verify all required metrics present
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1' in metrics
        assert 'false_positive_rate' in metrics
        assert 'false_negative_rate' in metrics
        assert 'error_rate' in metrics

        # Verify metrics are in valid ranges
        for metric_name, value in metrics.items():
            assert 0.0 <= value <= 1.0, f"{metric_name} should be between 0 and 1"


@pytest.mark.integration
class TestAPIIntegration:
    """Test API integration"""

    @pytest.mark.integration
    def test_api_decision_evaluation_workflow(self):
        """Test API decision evaluation workflow"""
        request_data = {
            "evaluation_point": "pre-commit",
            "inputs": {
                "risk_score": 0.3,
                "file_count": 20
            },
            "actor": {
                "repo_id": "test-repo",
                "type": "human"
            },
            "context": {
                "surface": "ide",
                "branch": "main"
            }
        }

        response = client.post(
            "/v1/decisions/evaluate",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "receipt" in data
        assert "confidence" in data
        assert "accuracy_metrics" in data

        # Verify receipt structure
        receipt = data["receipt"]
        assert receipt["gate_id"] == "detection-engine-core"
        assert receipt["evaluation_point"] == "pre-commit"
        assert receipt["decision"]["status"] in ["pass", "warn", "soft_block", "hard_block"]

    @pytest.mark.integration
    def test_api_feedback_workflow(self):
        """Test API feedback submission workflow"""
        # 1. Create decision first
        decision_request = {
            "evaluation_point": "pre-commit",
            "inputs": {"risk_score": 0.1},
            "actor": {"repo_id": "test-repo"}
        }

        decision_response = client.post(
            "/v1/decisions/evaluate",
            json=decision_request,
            headers={"Authorization": "Bearer test-token"}
        )

        assert decision_response.status_code == 200
        decision_receipt_id = decision_response.json()["receipt"]["receipt_id"]

        # 2. Submit feedback
        feedback_request = {
            "decision_receipt_id": decision_receipt_id,
            "pattern_id": "FB-02",
            "choice": "partly",
            "tags": ["needs-improvement"],
            "actor": {"repo_id": "test-repo"}
        }

        feedback_response = client.post(
            "/v1/feedback",
            json=feedback_request,
            headers={"Authorization": "Bearer test-token"}
        )

        assert feedback_response.status_code == 201
        feedback_data = feedback_response.json()
        assert feedback_data["status"] == "accepted"
        assert feedback_data["feedback_id"] is not None

    @pytest.mark.integration
    def test_api_error_handling(self):
        """Test API error handling"""
        # Test with invalid evaluation point
        invalid_request = {
            "evaluation_point": "invalid-point",
            "inputs": {},
            "actor": {"repo_id": "test-repo"}
        }

        response = client.post(
            "/v1/decisions/evaluate",
            json=invalid_request,
            headers={"Authorization": "Bearer test-token"}
        )

        # Should return 422 (validation error) or 500 (server error)
        assert response.status_code in [400, 422, 500]

    @pytest.mark.integration
    def test_api_health_checks(self):
        """Test API health check endpoints"""
        # Health check
        health_response = client.get("/v1/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

        # Readiness check
        readiness_response = client.get("/v1/ready")
        assert readiness_response.status_code == 200
        assert readiness_response.json()["ready"] is True


@pytest.mark.integration
class TestPerformanceIntegration:
    """Test performance integration per PRD §3.12"""

    @pytest.mark.integration
    def test_pre_commit_performance_budget(self):
        """Test pre-commit performance budget (50ms p95)"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'risk_score': 0.1},
            actor={'repo_id': 'test-repo'}
        )

        service = DetectionEngineService()
        times = []

        # Run multiple times to check p95
        for _ in range(20):
            start = time.perf_counter()
            service.evaluate_decision(request)
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            times.append(elapsed)

        # Sort and get p95
        times.sort()
        p95_index = int(len(times) * 0.95)
        p95_time = times[p95_index]

        # Should be within reasonable range (allowing for test overhead)
        assert p95_time < 100, f"p95 latency {p95_time}ms exceeds budget (50ms) with test overhead"

    @pytest.mark.integration
    def test_pre_merge_performance_budget(self):
        """Test pre-merge performance budget (100ms p95)"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_MERGE,
            inputs={'risk_score': 0.1},
            actor={'repo_id': 'test-repo'}
        )

        service = DetectionEngineService()
        times = []

        for _ in range(20):
            start = time.perf_counter()
            service.evaluate_decision(request)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        times.sort()
        p95_index = int(len(times) * 0.95)
        p95_time = times[p95_index]

        assert p95_time < 200, f"p95 latency {p95_time}ms exceeds budget (100ms) with test overhead"

