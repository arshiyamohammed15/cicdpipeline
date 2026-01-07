"""
Tests for Detection Engine Core Routes

Tests API routes per PRD §3.7
Coverage: 100% of route handlers
"""


# Imports handled by conftest.py
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add parent directory to path for imports
# Module setup handled by root conftest.py.parent.parent))

from detection_engine_core.main import app
from detection_engine_core.models import EvaluationPoint

client = TestClient(app)


@pytest.mark.unit
class TestRoutes:
    """Test API routes"""

    @pytest.mark.unit
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    @pytest.mark.unit
    def test_readiness_check(self):
        """Test readiness check endpoint"""
        response = client.get("/v1/ready")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "checks" in data

    @pytest.mark.unit
    def test_evaluate_decision_success(self):
        """Test decision evaluation endpoint - success"""
        request_data = {
            "evaluation_point": "pre-commit",
            "inputs": {
                "risk_score": 0.1,
                "file_count": 5
            },
            "actor": {
                "repo_id": "test-repo"
            }
        }

        response = client.post(
            "/v1/decisions/evaluate",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "receipt" in data
        assert "confidence" in data
        assert "accuracy_metrics" in data

    @pytest.mark.unit
    def test_evaluate_decision_unauthorized(self):
        """Test decision evaluation endpoint - unauthorized"""
        request_data = {
            "evaluation_point": "pre-commit",
            "inputs": {},
            "actor": {
                "repo_id": "test-repo"
            }
        }

        response = client.post(
            "/v1/decisions/evaluate",
            json=request_data
        )

        assert response.status_code == 401

    @pytest.mark.unit
    def test_submit_feedback_success(self):
        """Test feedback submission endpoint - success"""
        request_data = {
            "decision_receipt_id": "test-receipt-id",
            "pattern_id": "FB-01",
            "choice": "worked",
            "tags": [],
            "actor": {
                "repo_id": "test-repo"
            }
        }

        response = client.post(
            "/v1/feedback",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "feedback_id" in data
        assert data["status"] == "accepted"

    @pytest.mark.unit
    def test_submit_feedback_unauthorized(self):
        """Test feedback submission endpoint - unauthorized"""
        request_data = {
            "decision_receipt_id": "test-receipt-id",
            "pattern_id": "FB-01",
            "choice": "worked",
            "tags": [],
            "actor": {
                "repo_id": "test-repo"
            }
        }

        response = client.post(
            "/v1/feedback",
            json=request_data
        )

        assert response.status_code == 401

