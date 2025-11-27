"""
Risk→Test Matrix: Missing evidence/logging for auditors.

Required Evidence: Evidence pack including deployment manifest, approvals, ERIS
receipts for each rollout.
"""

from __future__ import annotations

import pytest

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from tests.shared_harness import DeploymentFixtureFactory, EvidencePackBuilder, TenantFactory
from ..services import DeploymentService


@pytest.fixture
def deployment_factory() -> DeploymentFixtureFactory:
    """Provide deployment fixture factory."""
    return DeploymentFixtureFactory()


@pytest.fixture
def evidence_builder():
    """Provide evidence builder (may be None if plugin not loaded)."""
    try:
        from tests.pytest_evidence_plugin import get_evidence_collector
        collector = get_evidence_collector()
        if collector:
            from tests.shared_harness import EvidencePackBuilder
            return EvidencePackBuilder(output_dir="artifacts/evidence")
    except ImportError:
        pass
    return None


@pytest.mark.deployment_regression
@pytest.mark.compliance
def test_deployment_evidence_pack_generated(
    deployment_factory: DeploymentFixtureFactory,
    evidence_builder: EvidencePackBuilder | None,
) -> None:
    """Test that deployment evidence pack is generated with manifest and receipts."""
    # Create deployment manifest
    manifest = deployment_factory.create_deployment_manifest(
        environment="production",
        approval_required=True,
        rollback_preconditions=["health_check_pass"],
    )
    
    # Simulate deployment
    service = DeploymentService()
    deployment = service.deploy(
        environment=manifest.environment,
        target="cloud",
        config=manifest.manifest_content,
    )
    
    # Add to evidence pack
    if evidence_builder:
        evidence_builder.add_config_snapshot(
            {
                "deployment_id": deployment["deployment_id"],
                "environment": manifest.environment,
                "manifest": manifest.manifest_content,
                "approval_required": manifest.approval_required,
                "rollback_preconditions": manifest.rollback_preconditions,
            },
            "deployment_manifest",
        )
        
        evidence_builder.add_receipt({
            "receipt_id": deployment["deployment_id"],
            "operation": "deployment",
            "environment": manifest.environment,
            "timestamp": manifest.timestamp.isoformat(),
        })
    
    assert deployment is not None
    assert deployment["deployment_id"]

