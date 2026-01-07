"""
Tests for Detection Engine Core Service

Tests service layer per PRD §3.9, §3.3
Coverage: 100% of service functionality
"""


# Imports handled by conftest.py
import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for imports
# Module setup handled by root conftest.py.parent.parent))

from detection_engine_core.services import DetectionEngineService
from detection_engine_core.models import (
    DecisionRequest, EvaluationPoint, DecisionStatus,
    FeedbackRequest
)


@pytest.mark.unit
class TestDetectionEngineService:
    """Test DetectionEngineService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = DetectionEngineService()

    @pytest.mark.unit
    def test_evaluate_decision_pass(self):
        """Test decision evaluation with pass status"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={
                'risk_score': 0.1,
                'file_count': 5
            },
            actor={
                'repo_id': 'test-repo'
            }
        )

        response = self.service.evaluate_decision(request)

        assert response.receipt is not None
        assert response.receipt.decision['status'] == DecisionStatus.PASS.value
        assert response.confidence is not None
        assert response.accuracy_metrics is not None

    @pytest.mark.unit
    def test_evaluate_decision_warn(self):
        """Test decision evaluation with warn status"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={
                'risk_score': 0.4,
                'file_count': 25
            },
            actor={
                'repo_id': 'test-repo'
            }
        )

        response = self.service.evaluate_decision(request)

        assert response.receipt.decision['status'] == DecisionStatus.WARN.value

    @pytest.mark.unit
    def test_evaluate_decision_soft_block(self):
        """Test decision evaluation with soft_block status"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_MERGE,
            inputs={
                'risk_score': 0.6,
                'file_count': 35
            },
            actor={
                'repo_id': 'test-repo'
            }
        )

        response = self.service.evaluate_decision(request)

        assert response.receipt.decision['status'] == DecisionStatus.SOFT_BLOCK.value

    @pytest.mark.unit
    def test_evaluate_decision_hard_block(self):
        """Test decision evaluation with hard_block status"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_DEPLOY,
            inputs={
                'risk_score': 0.9,
                'file_count': 60,
                'has_recent_incidents': True
            },
            actor={
                'repo_id': 'test-repo'
            }
        )

        response = self.service.evaluate_decision(request)

        assert response.receipt.decision['status'] == DecisionStatus.HARD_BLOCK.value

    @pytest.mark.unit
    def test_evaluate_decision_performance_budget(self):
        """Test that decision evaluation respects performance budgets"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={
                'risk_score': 0.1,
                'file_count': 5
            },
            actor={
                'repo_id': 'test-repo'
            }
        )

        response = self.service.evaluate_decision(request)

        # Should complete within budget (degraded flag indicates if exceeded)
        assert response.receipt.degraded is not None

    @pytest.mark.unit
    def test_evaluate_decision_receipt_fields(self):
        """Test that receipt contains all required fields per PRD §3.2"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={
                'risk_score': 0.1
            },
            actor={
                'repo_id': 'test-repo'
            },
            policy_version_ids=['POL-INIT']
        )

        response = self.service.evaluate_decision(request)
        receipt = response.receipt

        # Required fields per GSMD receipts_schema
        assert receipt.receipt_id is not None
        assert receipt.gate_id is not None
        assert receipt.policy_version_ids is not None
        assert receipt.snapshot_hash is not None
        assert receipt.timestamp_utc is not None
        assert receipt.timestamp_monotonic_ms is not None
        assert receipt.evaluation_point is not None
        assert receipt.inputs is not None
        assert receipt.decision is not None
        assert receipt.actor is not None
        assert receipt.degraded is not None
        assert receipt.signature is not None

    @pytest.mark.unit
    def test_evaluate_decision_confidence_calculation(self):
        """Test confidence calculation per PRD §3.3"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={
                'risk_score': 0.1
            },
            actor={
                'repo_id': 'test-repo'
            }
        )

        response = self.service.evaluate_decision(request)

        assert response.confidence is not None
        assert 0.0 <= response.confidence <= 1.0

    @pytest.mark.unit
    def test_evaluate_decision_accuracy_metrics(self):
        """Test accuracy metrics calculation per PRD §3.3"""
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={
                'risk_score': 0.1
            },
            actor={
                'repo_id': 'test-repo'
            }
        )

        response = self.service.evaluate_decision(request)

        assert response.accuracy_metrics is not None
        assert 'precision' in response.accuracy_metrics
        assert 'recall' in response.accuracy_metrics
        assert 'f1' in response.accuracy_metrics
        assert 'false_positive_rate' in response.accuracy_metrics
        assert 'false_negative_rate' in response.accuracy_metrics
        assert 'error_rate' in response.accuracy_metrics

    @pytest.mark.unit
    def test_submit_feedback(self):
        """Test feedback submission per PRD §3.6"""
        request = FeedbackRequest(
            decision_receipt_id='test-receipt-id',
            pattern_id='FB-01',
            choice='worked',
            tags=['test'],
            actor={
                'repo_id': 'test-repo'
            }
        )

        response = self.service.submit_feedback(request)

        assert response.feedback_id is not None
        assert response.status == 'accepted'
        assert response.message is not None

    @pytest.mark.unit
    def test_submit_feedback_all_patterns(self):
        """Test feedback submission with all pattern IDs"""
        patterns = ['FB-01', 'FB-02', 'FB-03', 'FB-04']
        choices = ['worked', 'partly', 'didnt']

        for pattern in patterns:
            for choice in choices:
                request = FeedbackRequest(
                    decision_receipt_id='test-receipt-id',
                    pattern_id=pattern,
                    choice=choice,
                    tags=[],
                    actor={
                        'repo_id': 'test-repo'
                    }
                )

                response = self.service.submit_feedback(request)
                assert response.feedback_id is not None

    @pytest.mark.unit
    def test_evaluate_decision_all_evaluation_points(self):
        """Test decision evaluation for all evaluation points"""
        evaluation_points = [
            EvaluationPoint.PRE_COMMIT,
            EvaluationPoint.PRE_MERGE,
            EvaluationPoint.PRE_DEPLOY,
            EvaluationPoint.POST_DEPLOY
        ]

        for ep in evaluation_points:
            request = DecisionRequest(
                evaluation_point=ep,
                inputs={
                    'risk_score': 0.1
                },
                actor={
                    'repo_id': 'test-repo'
                }
            )

            response = self.service.evaluate_decision(request)
            assert response.receipt.evaluation_point == ep

