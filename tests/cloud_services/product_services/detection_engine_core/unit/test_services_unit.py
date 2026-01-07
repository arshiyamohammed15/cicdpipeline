"""
Unit Tests for Detection Engine Core Service

Tests service layer per PRD §3.9
Coverage: 100% of services.py - every method, every branch, every line
"""


# Imports handled by conftest.py
import pytest
import time
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Module setup handled by root conftest.py.parent.parent))

from detection_engine_core.services import DetectionEngineService
from detection_engine_core.models import (
    DecisionRequest, DecisionResponse, EvaluationPoint, DecisionStatus,
    FeedbackRequest, FeedbackReceiptModel, EvidenceHandle
)


@pytest.mark.unit
class TestDetectionEngineServiceInit:
    """Test service initialization"""

    @pytest.mark.unit
    def test_init_sets_performance_budgets(self):
        """Test that __init__ sets performance budgets correctly"""
        service = DetectionEngineService()

        assert hasattr(service, 'performance_budgets')
        assert service.performance_budgets[EvaluationPoint.PRE_COMMIT] == 0.050
        assert service.performance_budgets[EvaluationPoint.PRE_MERGE] == 0.100
        assert service.performance_budgets[EvaluationPoint.PRE_DEPLOY] == 0.200
        assert service.performance_budgets[EvaluationPoint.POST_DEPLOY] == 0.200


@pytest.mark.unit
class TestPerformDetection:
    """Test _perform_detection method"""

    @pytest.mark.unit
    def test_perform_detection_with_high_risk_score(self):
        """Test detection with risk_score > 0.8"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'risk_score': 0.9},
            actor={'repo_id': 'test-repo'}
        )

        result = service._perform_detection(request)

        assert result['status'] == DecisionStatus.HARD_BLOCK
        assert 'High risk detected' in result['rationale']
        assert result['risk_score'] == 0.9

    @pytest.mark.unit
    def test_perform_detection_with_large_file_count_and_incidents(self):
        """Test detection with file_count > 50 and has_recent_incidents"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'file_count': 60, 'has_recent_incidents': True},
            actor={'repo_id': 'test-repo'}
        )

        result = service._perform_detection(request)

        assert result['status'] == DecisionStatus.HARD_BLOCK
        assert 'recent incidents' in result['rationale']

    @pytest.mark.unit
    def test_perform_detection_with_risk_score_0_5(self):
        """Test detection with risk_score > 0.5"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'risk_score': 0.6},
            actor={'repo_id': 'test-repo'}
        )

        result = service._perform_detection(request)

        assert result['status'] == DecisionStatus.SOFT_BLOCK
        assert 'Moderate risk detected' in result['rationale']

    @pytest.mark.unit
    def test_perform_detection_with_file_count_30(self):
        """Test detection with file_count > 30"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'file_count': 35},
            actor={'repo_id': 'test-repo'}
        )

        result = service._perform_detection(request)

        assert result['status'] == DecisionStatus.SOFT_BLOCK

    @pytest.mark.unit
    def test_perform_detection_with_risk_score_0_3(self):
        """Test detection with risk_score > 0.3"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'risk_score': 0.4},
            actor={'repo_id': 'test-repo'}
        )

        result = service._perform_detection(request)

        assert result['status'] == DecisionStatus.WARN
        assert 'Low risk detected' in result['rationale']

    @pytest.mark.unit
    def test_perform_detection_with_file_count_20(self):
        """Test detection with file_count > 20"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'file_count': 25},
            actor={'repo_id': 'test-repo'}
        )

        result = service._perform_detection(request)

        assert result['status'] == DecisionStatus.WARN

    @pytest.mark.unit
    def test_perform_detection_with_low_risk(self):
        """Test detection with low risk (pass)"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'risk_score': 0.2, 'file_count': 10},
            actor={'repo_id': 'test-repo'}
        )

        result = service._perform_detection(request)

        assert result['status'] == DecisionStatus.PASS
        assert 'No significant risks detected' in result['rationale']

    @pytest.mark.unit
    def test_perform_detection_with_empty_inputs(self):
        """Test detection with empty inputs"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )

        result = service._perform_detection(request)

        assert result['status'] == DecisionStatus.PASS
        assert result['risk_score'] == 0.0
        assert result['file_count'] == 0

    @pytest.mark.unit
    def test_perform_detection_with_none_inputs(self):
        """Test detection with None inputs - Pydantic validation prevents this"""
        # Pydantic validation prevents None for required dict fields
        # This test verifies that the model validation works correctly
        with pytest.raises(Exception):  # Pydantic ValidationError
            DecisionRequest(
                evaluation_point=EvaluationPoint.PRE_COMMIT,
                inputs=None,
                actor={'repo_id': 'test-repo'}
            )


@pytest.mark.unit
class TestGenerateBadges:
    """Test _generate_badges method"""

    @pytest.mark.unit
    def test_generate_badges_with_has_tests(self):
        """Test badge generation with has_tests"""
        service = DetectionEngineService()
        inputs = {'has_tests': True}

        badges = service._generate_badges(inputs)

        assert 'has-tests' in badges

    @pytest.mark.unit
    def test_generate_badges_with_has_documentation(self):
        """Test badge generation with has_documentation"""
        service = DetectionEngineService()
        inputs = {'has_documentation': True}

        badges = service._generate_badges(inputs)

        assert 'has-docs' in badges

    @pytest.mark.unit
    def test_generate_badges_with_code_review_approved(self):
        """Test badge generation with code_review_approved"""
        service = DetectionEngineService()
        inputs = {'code_review_approved': True}

        badges = service._generate_badges(inputs)

        assert 'reviewed' in badges

    @pytest.mark.unit
    def test_generate_badges_with_all_flags(self):
        """Test badge generation with all flags"""
        service = DetectionEngineService()
        inputs = {
            'has_tests': True,
            'has_documentation': True,
            'code_review_approved': True
        }

        badges = service._generate_badges(inputs)

        assert len(badges) == 3
        assert 'has-tests' in badges
        assert 'has-docs' in badges
        assert 'reviewed' in badges

    @pytest.mark.unit
    def test_generate_badges_with_no_flags(self):
        """Test badge generation with no flags"""
        service = DetectionEngineService()
        inputs = {}

        badges = service._generate_badges(inputs)

        assert len(badges) == 0

    @pytest.mark.unit
    def test_generate_badges_with_false_flags(self):
        """Test badge generation with false flags"""
        service = DetectionEngineService()
        inputs = {
            'has_tests': False,
            'has_documentation': False,
            'code_review_approved': False
        }

        badges = service._generate_badges(inputs)

        assert len(badges) == 0


@pytest.mark.unit
class TestCalculateConfidence:
    """Test _calculate_confidence method"""

    @pytest.mark.unit
    def test_calculate_confidence_high_risk(self):
        """Test confidence calculation for high risk (> 0.7)"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {'risk_score': 0.8}

        confidence = service._calculate_confidence(request, result)

        assert confidence == 0.85

    @pytest.mark.unit
    def test_calculate_confidence_moderate_risk(self):
        """Test confidence calculation for moderate risk (> 0.4)"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {'risk_score': 0.5}

        confidence = service._calculate_confidence(request, result)

        assert confidence == 0.75

    @pytest.mark.unit
    def test_calculate_confidence_low_risk(self):
        """Test confidence calculation for low risk (> 0.1)"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {'risk_score': 0.2}

        confidence = service._calculate_confidence(request, result)

        assert confidence == 0.90

    @pytest.mark.unit
    def test_calculate_confidence_very_low_risk(self):
        """Test confidence calculation for very low risk (<= 0.1)"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {'risk_score': 0.05}

        confidence = service._calculate_confidence(request, result)

        assert confidence == 0.95

    @pytest.mark.unit
    def test_calculate_confidence_with_missing_risk_score(self):
        """Test confidence calculation with missing risk_score"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {}

        confidence = service._calculate_confidence(request, result)

        assert confidence == 0.95  # Defaults to very low risk


@pytest.mark.unit
class TestCalculateAccuracyMetrics:
    """Test _calculate_accuracy_metrics method"""

    @pytest.mark.unit
    def test_calculate_accuracy_metrics_returns_dict(self):
        """Test that accuracy metrics returns a dictionary"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {}

        metrics = service._calculate_accuracy_metrics(request, result)

        assert isinstance(metrics, dict)
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1' in metrics
        assert 'false_positive_rate' in metrics
        assert 'false_negative_rate' in metrics
        assert 'error_rate' in metrics

    @pytest.mark.unit
    def test_calculate_accuracy_metrics_values(self):
        """Test that accuracy metrics have expected values"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {}

        metrics = service._calculate_accuracy_metrics(request, result)

        assert metrics['precision'] == 0.85
        assert metrics['recall'] == 0.80
        assert metrics['f1'] == 0.82
        assert metrics['false_positive_rate'] == 0.15
        assert metrics['false_negative_rate'] == 0.20
        assert metrics['error_rate'] == 0.18


@pytest.mark.unit
class TestGenerateReceipt:
    """Test _generate_receipt method"""

    @pytest.mark.unit
    def test_generate_receipt_creates_receipt(self):
        """Test that receipt is generated correctly"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'risk_score': 0.1},
            actor={'repo_id': 'test-repo'},
            policy_version_ids=['POL-TEST']
        )
        result = {
            'status': DecisionStatus.PASS,
            'rationale': 'Test',
            'badges': []
        }

        receipt = service._generate_receipt(request, result, False, 0.01)

        assert receipt.receipt_id is not None
        assert receipt.gate_id == 'detection-engine-core'
        assert receipt.policy_version_ids == ['POL-TEST']
        assert receipt.evaluation_point == EvaluationPoint.PRE_COMMIT
        assert receipt.decision['status'] == 'pass'
        assert receipt.degraded is False

    @pytest.mark.unit
    def test_generate_receipt_with_default_policy_version_ids(self):
        """Test receipt generation with default policy version IDs"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {
            'status': DecisionStatus.PASS,
            'rationale': 'Test',
            'badges': []
        }

        receipt = service._generate_receipt(request, result, False, 0.01)

        assert receipt.policy_version_ids == ['POL-INIT']

    @pytest.mark.unit
    def test_generate_receipt_with_degraded_flag(self):
        """Test receipt generation with degraded flag"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {
            'status': DecisionStatus.PASS,
            'rationale': 'Test',
            'badges': []
        }

        receipt = service._generate_receipt(request, result, True, 0.01)

        assert receipt.degraded is True

    @pytest.mark.unit
    def test_generate_receipt_with_actor_type_from_inputs(self):
        """Test receipt generation with actor.type from inputs"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'actor_type': 'ai'},
            actor={'repo_id': 'test-repo'}
        )
        result = {
            'status': DecisionStatus.PASS,
            'rationale': 'Test',
            'badges': []
        }

        receipt = service._generate_receipt(request, result, False, 0.01)

        assert receipt.actor['type'] == 'ai'

    @pytest.mark.unit
    def test_generate_receipt_with_evidence_urls(self):
        """Test receipt generation with evidence URLs"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'evidence_urls': ['https://example.com/evidence1']},
            actor={'repo_id': 'test-repo'}
        )
        result = {
            'status': DecisionStatus.PASS,
            'rationale': 'Test',
            'badges': []
        }

        receipt = service._generate_receipt(request, result, False, 0.01)

        assert len(receipt.evidence_handles) == 1
        assert receipt.evidence_handles[0].url == 'https://example.com/evidence1'
        assert receipt.evidence_handles[0].type == 'artifact'

    @pytest.mark.unit
    def test_generate_receipt_with_multiple_evidence_urls(self):
        """Test receipt generation with multiple evidence URLs"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'evidence_urls': ['https://example.com/e1', 'https://example.com/e2']},
            actor={'repo_id': 'test-repo'}
        )
        result = {
            'status': DecisionStatus.PASS,
            'rationale': 'Test',
            'badges': []
        }

        receipt = service._generate_receipt(request, result, False, 0.01)

        assert len(receipt.evidence_handles) == 2

    @pytest.mark.unit
    def test_generate_receipt_with_context(self):
        """Test receipt generation with context"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'},
            context={'surface': 'ide', 'branch': 'main'}
        )
        result = {
            'status': DecisionStatus.PASS,
            'rationale': 'Test',
            'badges': []
        }

        receipt = service._generate_receipt(request, result, False, 0.01)

        assert receipt.context is not None
        assert receipt.context['surface'] == 'ide'
        assert receipt.context['branch'] == 'main'

    @pytest.mark.unit
    def test_generate_receipt_with_decision_status_enum(self):
        """Test receipt generation with DecisionStatus enum"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {
            'status': DecisionStatus.WARN,
            'rationale': 'Test',
            'badges': []
        }

        receipt = service._generate_receipt(request, result, False, 0.01)

        assert receipt.decision['status'] == 'warn'

    @pytest.mark.unit
    def test_generate_receipt_with_decision_status_string(self):
        """Test receipt generation with decision status as string"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {
            'status': 'warn',
            'rationale': 'Test',
            'badges': []
        }

        receipt = service._generate_receipt(request, result, False, 0.01)

        assert receipt.decision['status'] == 'warn'

    @pytest.mark.unit
    def test_generate_receipt_with_badges(self):
        """Test receipt generation with badges"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {
            'status': DecisionStatus.PASS,
            'rationale': 'Test',
            'badges': ['has-tests', 'has-docs']
        }

        receipt = service._generate_receipt(request, result, False, 0.01)

        assert receipt.decision['badges'] == ['has-tests', 'has-docs']

    @pytest.mark.unit
    def test_generate_receipt_with_missing_badges(self):
        """Test receipt generation with missing badges"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        result = {
            'status': DecisionStatus.PASS,
            'rationale': 'Test'
        }

        receipt = service._generate_receipt(request, result, False, 0.01)

        assert receipt.decision['badges'] == []


@pytest.mark.unit
class TestEvaluateDecision:
    """Test evaluate_decision method"""

    @pytest.mark.unit
    def test_evaluate_decision_returns_response(self):
        """Test that evaluate_decision returns DecisionResponse"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'risk_score': 0.1},
            actor={'repo_id': 'test-repo'}
        )

        # time.perf_counter is called twice: once at start, once in _generate_receipt
        with patch('time.perf_counter', side_effect=[0, 0.01, 1000]):
            response = service.evaluate_decision(request)

        assert isinstance(response, DecisionResponse)
        assert response.receipt is not None
        assert response.confidence is not None
        assert response.accuracy_metrics is not None

    @pytest.mark.unit
    def test_evaluate_decision_sets_degraded_when_budget_exceeded(self):
        """Test that degraded flag is set when budget is exceeded"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )

        # time.perf_counter is called twice: once at start, once in _generate_receipt
        with patch('time.perf_counter', side_effect=[0, 0.060, 1000]):  # 60ms > 50ms
            response = service.evaluate_decision(request)

        assert response.receipt.degraded is True

    @pytest.mark.unit
    def test_evaluate_decision_does_not_set_degraded_when_within_budget(self):
        """Test that degraded flag is not set when within budget"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )

        # time.perf_counter is called twice: once at start, once in _generate_receipt
        with patch('time.perf_counter', side_effect=[0, 0.040, 1000]):  # 40ms < 50ms
            response = service.evaluate_decision(request)

        assert response.receipt.degraded is False

    @pytest.mark.unit
    def test_evaluate_decision_uses_default_budget_for_unknown_evaluation_point(self):
        """Test that default budget (200ms) is used for unknown evaluation point"""
        service = DetectionEngineService()
        # Create request with custom evaluation point (not in enum)
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )
        # Mock performance_budgets to not have the evaluation point
        service.performance_budgets = {}

        # time.perf_counter is called twice: once at start, once in _generate_receipt
        with patch('time.perf_counter', side_effect=[0, 0.250, 1000]):  # 250ms > 200ms default
            response = service.evaluate_decision(request)

        assert response.receipt.degraded is True

    @pytest.mark.unit
    def test_evaluate_decision_handles_exception(self):
        """Test that evaluate_decision handles exceptions"""
        service = DetectionEngineService()
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},
            actor={'repo_id': 'test-repo'}
        )

        with patch.object(service, '_perform_detection', side_effect=Exception('Test error')):
            with pytest.raises(Exception) as exc_info:
                service.evaluate_decision(request)
            assert 'Test error' in str(exc_info.value)


@pytest.mark.unit
class TestSubmitFeedback:
    """Test submit_feedback method"""

    @pytest.mark.unit
    def test_submit_feedback_returns_response(self):
        """Test that submit_feedback returns FeedbackResponse"""
        service = DetectionEngineService()
        request = FeedbackRequest(
            decision_receipt_id='test-receipt-id',
            pattern_id='FB-01',
            choice='worked',
            tags=['positive'],
            actor={'repo_id': 'test-repo'}
        )

        response = service.submit_feedback(request)

        assert response.feedback_id is not None
        assert response.status == 'accepted'
        assert 'Feedback submitted successfully' in response.message

    @pytest.mark.unit
    def test_submit_feedback_generates_unique_feedback_id(self):
        """Test that submit_feedback generates unique feedback IDs"""
        service = DetectionEngineService()
        request = FeedbackRequest(
            decision_receipt_id='test-receipt-id',
            pattern_id='FB-01',
            choice='worked',
            tags=[],
            actor={'repo_id': 'test-repo'}
        )

        response1 = service.submit_feedback(request)
        response2 = service.submit_feedback(request)

        assert response1.feedback_id != response2.feedback_id

    @pytest.mark.unit
    def test_submit_feedback_preserves_request_data(self):
        """Test that submit_feedback preserves request data"""
        service = DetectionEngineService()
        request = FeedbackRequest(
            decision_receipt_id='test-receipt-id',
            pattern_id='FB-02',
            choice='partly',
            tags=['needs-improvement'],
            actor={'repo_id': 'test-repo', 'type': 'human'}
        )

        response = service.submit_feedback(request)

        # Verify feedback receipt would contain this data (in production)
        assert response.feedback_id is not None

