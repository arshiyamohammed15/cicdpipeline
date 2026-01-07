"""
Unit tests for Identity & Access Management service layer.
"""


# Imports handled by conftest.py
import pytest
from datetime import datetime, timedelta
from identity_access_management.services import IAMService, TokenValidator, RBACEvaluator, ABACEvaluator
from identity_access_management.models import VerifyRequest, DecisionRequest, Subject, DecisionContext
from identity_access_management.dependencies import MockM27EvidenceLedger, MockM29DataPlane, MockM32TrustPlane


@pytest.mark.unit
class TestIAMService:
    """Test IAM service functionality."""

    @pytest.mark.unit
    def test_service_initialization(self):
        """Test service initialization."""
        service = IAMService()
        assert service is not None
        assert service.token_validator is not None
        assert service.rbac_evaluator is not None
        assert service.abac_evaluator is not None

    @pytest.mark.unit
    def test_get_metrics(self):
        """Test metrics retrieval."""
        service = IAMService()
        metrics = service.get_metrics()
        assert "authentication_count" in metrics
        assert "decision_count" in metrics
        assert "policy_count" in metrics


@pytest.mark.unit
class TestTokenValidator:
    """Test token validator functionality."""

    @pytest.mark.unit
    def test_validator_initialization(self):
        """Test token validator initialization."""
        data_plane = MockM29DataPlane()
        validator = TokenValidator(data_plane)
        assert validator is not None

    @pytest.mark.unit
    def test_token_verification_missing_library(self):
        """Test token verification when PyJWT is not available."""
        data_plane = MockM29DataPlane()
        validator = TokenValidator(data_plane)
        # This test verifies graceful handling when PyJWT is not installed
        # In production, PyJWT should be installed
        result = validator.verify_token("invalid_token")
        assert result[0] is False  # is_valid


@pytest.mark.unit
class TestRBACEvaluator:
    """Test RBAC evaluator functionality."""

    @pytest.mark.unit
    def test_evaluator_initialization(self):
        """Test RBAC evaluator initialization."""
        evaluator = RBACEvaluator()
        assert evaluator is not None

    @pytest.mark.unit
    def test_role_mapping(self):
        """Test organizational role mapping."""
        evaluator = RBACEvaluator()
        assert evaluator.map_org_role("executive") == "admin"
        assert evaluator.map_org_role("lead") == "developer"
        assert evaluator.map_org_role("individual_contributor") == "developer"

    @pytest.mark.unit
    def test_rbac_evaluation_allow(self):
        """Test RBAC evaluation allowing access."""
        evaluator = RBACEvaluator()
        allowed, reason = evaluator.evaluate(["admin"], "read", "resource")
        assert allowed is True
        assert "admin" in reason

    @pytest.mark.unit
    def test_rbac_evaluation_deny(self):
        """Test RBAC evaluation denying access."""
        evaluator = RBACEvaluator()
        allowed, reason = evaluator.evaluate(["viewer"], "write", "resource")
        assert allowed is False
        assert "viewer" in reason or "allows" not in reason


@pytest.mark.unit
class TestABACEvaluator:
    """Test ABAC evaluator functionality."""

    @pytest.mark.unit
    def test_evaluator_initialization(self):
        """Test ABAC evaluator initialization."""
        trust_plane = MockM32TrustPlane()
        evaluator = ABACEvaluator(trust_plane)
        assert evaluator is not None

    @pytest.mark.unit
    def test_abac_evaluation_no_constraints(self):
        """Test ABAC evaluation with no constraints."""
        trust_plane = MockM32TrustPlane()
        evaluator = ABACEvaluator(trust_plane)
        subject = Subject(sub="user123", roles=["developer"])
        allowed, reason = evaluator.evaluate(None, subject)
        assert allowed is True
        assert "No constraints" in reason

    @pytest.mark.unit
    def test_abac_evaluation_high_risk(self):
        """Test ABAC evaluation with high risk score."""
        trust_plane = MockM32TrustPlane()
        evaluator = ABACEvaluator(trust_plane)
        context = DecisionContext(risk_score=0.9)
        subject = Subject(sub="user123", roles=["developer"])
        allowed, reason = evaluator.evaluate(context, subject)
        assert allowed is False
        assert "Risk score" in reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
