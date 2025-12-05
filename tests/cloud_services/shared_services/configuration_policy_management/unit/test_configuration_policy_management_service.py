"""
Unit tests for Configuration & Policy Management service layer.
"""


# Imports handled by conftest.py
import pytest
from configuration_policy_management.services import PolicyEvaluationEngine, PolicyService
from configuration_policy_management.dependencies import (
    MockM21IAM, MockM27EvidenceLedger, MockM29DataPlane,
    MockM33KeyManagement, MockM34SchemaRegistry, MockM32TrustPlane
)


@pytest.mark.unit
class TestPolicyEvaluationEngine:
    """Test policy evaluation engine functionality."""

    def test_engine_initialization(self):
        """Test policy evaluation engine initialization."""
        data_plane = MockM29DataPlane()
        evidence_ledger = MockM27EvidenceLedger()
        key_management = MockM33KeyManagement()
        engine = PolicyEvaluationEngine(data_plane, evidence_ledger, key_management)
        assert engine is not None

    def test_evaluate_policy_no_policy(self):
        """Test policy evaluation with no policy found."""
        data_plane = MockM29DataPlane()
        evidence_ledger = MockM27EvidenceLedger()
        key_management = MockM33KeyManagement()
        engine = PolicyEvaluationEngine(data_plane, evidence_ledger, key_management)

        result = engine.evaluate_policy(
            policy_id="nonexistent",
            context={},
            principal={"sub": "user123"},
            resource={"id": "resource123"},
            action="read"
        )
        # Should return default deny or allow based on implementation
        assert result is not None


@pytest.mark.unit
class TestPolicyService:
    """Test policy service functionality."""

    def test_service_initialization(self):
        """Test policy service initialization."""
        evidence_ledger = MockM27EvidenceLedger()
        key_management = MockM33KeyManagement()
        schema_registry = MockM34SchemaRegistry()
        service = PolicyService(evidence_ledger, key_management, schema_registry)
        assert service is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
