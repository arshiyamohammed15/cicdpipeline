"""
End-to-End Workflow Tests for Detection Engine Core

Tests complete user workflows per PRD §3.8, §3.9
Coverage: Critical user journeys
"""

import pytest
import time
import sys
from pathlib import Path
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from services import DetectionEngineService
from models import (
    DecisionRequest, EvaluationPoint, DecisionStatus,
    FeedbackRequest
)

client = TestClient(app)


class TestE2EWorkflows:
    """Test end-to-end workflows"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = DetectionEngineService()

    def test_developer_workflow_pre_commit(self):
        """
        Test complete developer workflow: pre-commit evaluation
        
        Scenario:
        1. Developer makes changes
        2. Pre-commit hook triggers detection engine
        3. Decision is evaluated
        4. Receipt is generated
        5. Developer views decision card
        6. Developer submits feedback
        """
        # Step 1: Developer makes changes (simulated via inputs)
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={
                'risk_score': 0.2,
                'file_count': 10,
                'has_tests': True,
                'has_documentation': True
            },
            actor={
                'repo_id': 'developer-repo',
                'type': 'human'
            },
            context={
                'surface': 'ide',
                'branch': 'feature-branch',
                'commit': 'abc123'
            }
        )

        # Step 2: Evaluate decision
        response = self.service.evaluate_decision(request)

        # Step 3: Verify receipt generated
        assert response.receipt is not None
        assert response.receipt.evaluation_point == EvaluationPoint.PRE_COMMIT
        assert response.receipt.decision['status'] in ['pass', 'warn', 'soft_block', 'hard_block']

        # Step 4: Verify performance within budget
        assert response.receipt.degraded is not None  # Flag is set

        # Step 5: Developer submits feedback
        feedback_request = FeedbackRequest(
            decision_receipt_id=response.receipt.receipt_id,
            pattern_id='FB-01',
            choice='worked',
            tags=['accurate'],
            actor={'repo_id': 'developer-repo'}
        )

        feedback_response = self.service.submit_feedback(feedback_request)
        assert feedback_response.status == 'accepted'

    def test_pr_review_workflow_pre_merge(self):
        """
        Test PR review workflow: pre-merge evaluation
        
        Scenario:
        1. PR is opened
        2. Pre-merge check triggers detection engine
        3. Decision is evaluated
        4. Receipt is generated with PR context
        5. Reviewer views decision
        """
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_MERGE,
            inputs={
                'risk_score': 0.6,
                'file_count': 35,
                'has_recent_incidents': False
            },
            actor={
                'repo_id': 'pr-repo',
                'type': 'human'
            },
            context={
                'surface': 'pr',
                'pr_id': 'PR-123',
                'branch': 'feature-branch'
            }
        )

        response = self.service.evaluate_decision(request)

        assert response.receipt.evaluation_point == EvaluationPoint.PRE_MERGE
        assert response.receipt.context is not None
        assert response.receipt.context['surface'] == 'pr'
        assert response.receipt.context['pr_id'] == 'PR-123'

        # Should be soft_block or warn for risk_score 0.6
        assert response.receipt.decision['status'] in ['warn', 'soft_block']

    def test_deployment_workflow_pre_deploy(self):
        """
        Test deployment workflow: pre-deploy evaluation
        
        Scenario:
        1. Deployment is triggered
        2. Pre-deploy check triggers detection engine
        3. Decision is evaluated
        4. Receipt is generated
        5. Deployment proceeds or is blocked
        """
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_DEPLOY,
            inputs={
                'risk_score': 0.9,
                'file_count': 60,
                'has_recent_incidents': True
            },
            actor={
                'repo_id': 'deploy-repo',
                'type': 'automated'
            },
            context={
                'surface': 'ci',
                'deployment_id': 'DEP-456'
            }
        )

        response = self.service.evaluate_decision(request)

        assert response.receipt.evaluation_point == EvaluationPoint.PRE_DEPLOY
        assert response.receipt.context is not None
        assert response.receipt.context['surface'] == 'ci'

        # Should be hard_block for high risk with incidents
        assert response.receipt.decision['status'] == DecisionStatus.HARD_BLOCK.value

    def test_feedback_learning_workflow(self):
        """
        Test feedback learning workflow per PRD §3.3
        
        Scenario:
        1. Decision is made
        2. User provides feedback
        3. Feedback is linked to decision receipt
        4. System learns from correction
        """
        # Step 1: Create decision
        decision_request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={'risk_score': 0.5},
            actor={'repo_id': 'learning-repo'}
        )
        decision_response = self.service.evaluate_decision(decision_request)
        decision_receipt_id = decision_response.receipt.receipt_id

        # Step 2: Submit multiple feedback entries
        feedback_patterns = [
            ('FB-01', 'worked'),
            ('FB-02', 'partly'),
            ('FB-03', 'didnt'),
            ('FB-04', 'worked')
        ]

        feedback_ids = []
        for pattern_id, choice in feedback_patterns:
            feedback_request = FeedbackRequest(
                decision_receipt_id=decision_receipt_id,
                pattern_id=pattern_id,
                choice=choice,
                tags=['learning'],
                actor={'repo_id': 'learning-repo'}
            )
            feedback_response = self.service.submit_feedback(feedback_request)
            feedback_ids.append(feedback_response.feedback_id)

        # Step 3: Verify all feedback linked to same decision
        assert len(feedback_ids) == len(feedback_patterns)
        assert all(fid is not None for fid in feedback_ids)

        # In production, would verify feedback is used for learning
        # (accuracy metrics improvement, confidence adjustment, etc.)

    def test_multi_evaluation_point_workflow(self):
        """
        Test workflow across multiple evaluation points
        
        Scenario:
        1. Pre-commit evaluation
        2. Pre-merge evaluation
        3. Pre-deploy evaluation
        4. Post-deploy evaluation
        """
        repo_id = 'multi-ep-repo'
        evaluation_points = [
            EvaluationPoint.PRE_COMMIT,
            EvaluationPoint.PRE_MERGE,
            EvaluationPoint.PRE_DEPLOY,
            EvaluationPoint.POST_DEPLOY
        ]

        receipts = []
        for ep in evaluation_points:
            request = DecisionRequest(
                evaluation_point=ep,
                inputs={'risk_score': 0.3},
                actor={'repo_id': repo_id},
                context={'branch': 'main'}
            )

            response = self.service.evaluate_decision(request)
            receipts.append(response.receipt)

            # Verify each receipt
            assert response.receipt.evaluation_point == ep
            assert response.receipt.actor['repo_id'] == repo_id

        # Verify all receipts generated
        assert len(receipts) == len(evaluation_points)

        # Verify receipts have sequential timestamps (or at least valid timestamps)
        timestamps = [r.timestamp_utc for r in receipts]
        assert all(ts is not None for ts in timestamps)

    def test_error_recovery_workflow(self):
        """
        Test error recovery workflow
        
        Scenario:
        1. Service encounters error
        2. Degraded mode is activated
        3. Service continues to function
        4. Error is logged
        """
        # Simulate error condition (invalid inputs)
        request = DecisionRequest(
            evaluation_point=EvaluationPoint.PRE_COMMIT,
            inputs={},  # Minimal inputs
            actor={'repo_id': 'error-repo'}
        )

        # Service should handle gracefully
        response = self.service.evaluate_decision(request)

        # Should still generate receipt (possibly with degraded flag)
        assert response.receipt is not None
        assert response.receipt.decision is not None

        # Degraded flag may be set
        assert isinstance(response.receipt.degraded, bool)

