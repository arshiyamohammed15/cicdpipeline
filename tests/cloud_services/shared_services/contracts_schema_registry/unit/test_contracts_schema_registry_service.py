"""
Unit tests for Contracts & Schema Registry service layer.
"""


# Imports handled by conftest.py
import pytest
from contracts_schema_registry.services import SchemaService, ContractService
from contracts_schema_registry.dependencies import (
    MockM33KMS, MockM27EvidenceLedger, MockM29DataPlane, MockM21IAM
)


@pytest.mark.unit
class TestSchemaService:
    """Test schema service functionality."""

    def test_service_initialization(self):
        """Test schema service initialization."""
        kms = MockM33KMS()
        evidence_ledger = MockM27EvidenceLedger()
        data_plane = MockM29DataPlane()
        iam = MockM21IAM()

        service = SchemaService(
            kms=kms,
            evidence_ledger=evidence_ledger,
            data_plane=data_plane,
            iam=iam
        )
        assert service is not None


@pytest.mark.unit
class TestContractService:
    """Test contract service functionality."""

    def test_service_initialization(self):
        """Test contract service initialization."""
        kms = MockM33KMS()
        evidence_ledger = MockM27EvidenceLedger()
        data_plane = MockM29DataPlane()
        iam = MockM21IAM()

        service = ContractService(
            kms=kms,
            evidence_ledger=evidence_ledger,
            data_plane=data_plane,
            iam=iam
        )
        assert service is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
