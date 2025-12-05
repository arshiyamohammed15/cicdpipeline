from __future__ import annotations
"""
Deployment-specific fixtures for test harness.
"""


from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from .tenants import TenantProfile


@dataclass
class EnvironmentConfig:
    """Synthetic environment configuration for parity testing."""

    environment: str  # dev/staging/prod
    config_hash: str
    resource_inventory: Dict[str, List[str]]
    terraform_state_version: str
    timestamp: datetime


@dataclass
class DeploymentManifest:
    """Synthetic deployment manifest for testing."""

    deployment_id: str
    environment: str
    manifest_content: Dict[str, Any]
    approval_required: bool
    rollback_preconditions: List[str]
    timestamp: datetime


class DeploymentFixtureFactory:
    """Generates deployment fixtures for testing."""

    def create_environment_config(
        self,
        environment: str,
        *,
        resource_count: int = 10,
    ) -> EnvironmentConfig:
        import hashlib

        resources = {f"resource-{i}": [f"type-{i % 3}"] for i in range(resource_count)}
        config_blob = f"{environment}:{resources}"
        config_hash = hashlib.sha256(config_blob.encode()).hexdigest()

        return EnvironmentConfig(
            environment=environment,
            config_hash=config_hash,
            resource_inventory=resources,
            terraform_state_version=f"v1.0.{uuid4().hex[:4]}",
            timestamp=datetime.utcnow(),
        )

    def create_deployment_manifest(
        self,
        environment: str,
        *,
        approval_required: bool = True,
        rollback_preconditions: List[str] | None = None,
    ) -> DeploymentManifest:
        return DeploymentManifest(
            deployment_id=f"deploy-{uuid4().hex[:8]}",
            environment=environment,
            manifest_content={
                "services": ["api", "worker"],
                "replicas": 3,
                "image_tag": "v1.2.3",
            },
            approval_required=approval_required,
            rollback_preconditions=rollback_preconditions or ["health_check_pass", "smoke_test_pass"],
            timestamp=datetime.utcnow(),
        )

    def create_parity_matrix(
        self, environments: List[str]
    ) -> Dict[str, EnvironmentConfig]:
        """Create configs for multiple environments to test parity."""
        return {env: self.create_environment_config(env) for env in environments}

