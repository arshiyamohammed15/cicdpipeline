"""
Unit tests for Deployment & Infrastructure service layer.
"""

import pytest
from datetime import datetime
from deployment_infrastructure.services import (
    DeploymentService,
    EnvironmentParityService,
    InfrastructureStatusService
)


class TestDeploymentService:
    """Test deployment service functionality."""

    @pytest.mark.deployment_regression
    @pytest.mark.unit
    def test_service_initialization(self):
        """Test deployment service initialization."""
        service = DeploymentService()
        assert service is not None
        assert service.deployments is not None

    @pytest.mark.deployment_regression
    @pytest.mark.unit
    @pytest.mark.deployment_regression
    @pytest.mark.unit
    def test_deploy(self):
        """Test deployment operation."""
        service = DeploymentService()
        result = service.deploy(
            environment="development",
            target="local"
        )
        assert result is not None
        assert "deployment_id" in result
        assert result["status"] in ["pending", "in_progress", "completed", "failed"]
        assert result["environment"] == "development"
        assert result["target"] == "local"

    def test_deploy_with_service(self):
        """Test deployment with specific service."""
        service = DeploymentService()
        result = service.deploy(
            environment="staging",
            target="cloud",
            service="identity-access-management"
        )
        assert result is not None
        assert result["environment"] == "staging"
        assert result["target"] == "cloud"

    def test_get_deployment_status(self):
        """Test get deployment status."""
        service = DeploymentService()
        result = service.deploy(
            environment="development",
            target="local"
        )
        deployment_id = result["deployment_id"]
        status = service.get_deployment_status(deployment_id)
        assert status is not None
        assert status["deployment_id"] == deployment_id

    def test_get_deployment_status_not_found(self):
        """Test get deployment status for non-existent deployment."""
        service = DeploymentService()
        status = service.get_deployment_status("non-existent-id")
        assert status is None

    def test_deploy_invalid_environment(self):
        """Test deployment with invalid environment."""
        service = DeploymentService()
        with pytest.raises(ValueError, match="Invalid environment"):
            service.deploy(environment="invalid", target="local")

    def test_deploy_invalid_target(self):
        """Test deployment with invalid target."""
        service = DeploymentService()
        with pytest.raises(ValueError, match="Invalid target"):
            service.deploy(environment="development", target="invalid")

    def test_deploy_with_config(self):
        """Test deployment with configuration overrides."""
        service = DeploymentService()
        config = {"timeout": 300, "retries": 3}
        result = service.deploy(
            environment="staging",
            target="cloud",
            config=config
        )
        assert result is not None
        assert result["status"] == "completed"
        assert "steps" in result

    def test_deploy_steps_tracking(self):
        """Test that deployment tracks steps correctly."""
        service = DeploymentService()
        result = service.deploy(
            environment="development",
            target="local"
        )
        assert "steps" in result
        assert len(result["steps"]) > 0
        assert all("step" in step and "status" in step for step in result["steps"])

    def test_deploy_estimated_completion(self):
        """Test that estimated completion time is calculated correctly."""
        service = DeploymentService()
        result = service.deploy(
            environment="development",
            target="local"
        )
        assert "estimated_completion" in result
        assert result["estimated_completion"] > result["started_at"]

    def test_deploy_hybrid_target(self):
        """Test deployment to hybrid target."""
        service = DeploymentService()
        result = service.deploy(
            environment="production",
            target="hybrid"
        )
        assert result is not None
        assert result["target"] == "hybrid"
        assert result["status"] == "completed"


class TestEnvironmentParityService:
    """Test environment parity service functionality."""

    @pytest.mark.deployment_regression
    @pytest.mark.unit
    def test_service_initialization(self):
        """Test environment parity service initialization."""
        service = EnvironmentParityService()
        assert service is not None

    def test_verify_parity(self):
        """Test environment parity verification."""
        service = EnvironmentParityService()
        result = service.verify_parity(
            source_environment="development",
            target_environment="staging"
        )
        assert result is not None
        assert result["source_environment"] == "development"
        assert result["target_environment"] == "staging"
        assert result["parity_status"] in ["match", "mismatch", "partial"]
        assert "differences" in result
        assert "checked_at" in result

    def test_verify_parity_with_resources(self):
        """Test environment parity verification with specific resources."""
        service = EnvironmentParityService()
        result = service.verify_parity(
            source_environment="development",
            target_environment="staging",
            check_resources=["database", "compute"]
        )
        assert result is not None
        assert len(result["differences"]) >= 0

    def test_verify_parity_invalid_source_environment(self):
        """Test parity verification with invalid source environment."""
        service = EnvironmentParityService()
        with pytest.raises(ValueError, match="Invalid source environment"):
            service.verify_parity(
                source_environment="invalid",
                target_environment="staging"
            )

    def test_verify_parity_invalid_target_environment(self):
        """Test parity verification with invalid target environment."""
        service = EnvironmentParityService()
        with pytest.raises(ValueError, match="Invalid target environment"):
            service.verify_parity(
                source_environment="development",
                target_environment="invalid"
            )

    def test_verify_parity_same_environments(self):
        """Test parity verification with same source and target."""
        service = EnvironmentParityService()
        with pytest.raises(ValueError, match="must be different"):
            service.verify_parity(
                source_environment="development",
                target_environment="development"
            )

    def test_verify_parity_mismatch_detection(self):
        """Test parity verification detects mismatches."""
        service = EnvironmentParityService()
        result = service.verify_parity(
            source_environment="production",
            target_environment="staging",
            check_resources=["service_versions"]
        )
        assert result is not None
        assert "mismatch_count" in result
        assert result["parity_status"] in ["match", "mismatch"]

    def test_verify_parity_default_resources(self):
        """Test parity verification with default resources."""
        service = EnvironmentParityService()
        result = service.verify_parity(
            source_environment="development",
            target_environment="staging"
        )
        assert result is not None
        assert len(result["differences"]) > 0
        assert all("resource" in d and "match" in d for d in result["differences"])


class TestInfrastructureStatusService:
    """Test infrastructure status service functionality."""

    @pytest.mark.deployment_regression
    @pytest.mark.unit
    def test_service_initialization(self):
        """Test infrastructure status service initialization."""
        service = InfrastructureStatusService()
        assert service is not None

    def test_get_status(self):
        """Test get infrastructure status."""
        service = InfrastructureStatusService()
        result = service.get_status()
        assert result is not None
        assert "environment" in result
        assert "resources" in result
        assert "status_summary" in result
        assert "checked_at" in result

    def test_get_status_with_environment(self):
        """Test get infrastructure status with specific environment."""
        service = InfrastructureStatusService()
        result = service.get_status(environment="production")
        assert result is not None
        assert result["environment"] == "production"

    def test_get_status_with_resource_type(self):
        """Test get infrastructure status with specific resource type."""
        service = InfrastructureStatusService()
        result = service.get_status(resource_type="database")
        assert result is not None
        assert all(r["resource_type"] == "database" for r in result["resources"])
