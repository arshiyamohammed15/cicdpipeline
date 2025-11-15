"""
Unit tests for Key Management Service service layer.
"""

import pytest
from key_management_service.services import KMSService
from key_management_service.hsm import MockHSM
from key_management_service.dependencies import (
    MockM27EvidenceLedger, MockM29DataPlane, MockM32TrustPlane, MockM21IAM
)


class TestKMSService:
    """Test KMS service functionality."""

    def test_service_initialization(self):
        """Test KMS service initialization."""
        hsm = MockHSM()
        evidence_ledger = MockM27EvidenceLedger()
        data_plane = MockM29DataPlane()
        trust_plane = MockM32TrustPlane()
        iam = MockM21IAM()

        service = KMSService(
            hsm=hsm,
            evidence_ledger=evidence_ledger,
            data_plane=data_plane,
            trust_plane=trust_plane,
            iam=iam
        )
        assert service is not None
        assert service.hsm is not None
        assert service.lifecycle_manager is not None

    def test_get_metrics(self):
        """Test metrics retrieval."""
        hsm = MockHSM()
        evidence_ledger = MockM27EvidenceLedger()
        data_plane = MockM29DataPlane()
        trust_plane = MockM32TrustPlane()
        iam = MockM21IAM()

        service = KMSService(
            hsm=hsm,
            evidence_ledger=evidence_ledger,
            data_plane=data_plane,
            trust_plane=trust_plane,
            iam=iam
        )
        metrics = service.get_metrics()
        assert "key_generation_count" in metrics
        assert "signing_count" in metrics
        assert "verification_count" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
