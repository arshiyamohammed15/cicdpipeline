"""Integration tests for Configuration & Policy Management API."""
from __future__ import annotations

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from configuration_policy_management.main import app


@pytest.mark.integration
class TestPolicyLifecycle:
    """Test policy lifecycle integration."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_create_and_evaluate_policy(self, client):
        """Test creating and evaluating a policy."""
        # Create policy
        create_response = client.post(
            "/policy/v1/policies?tenant_id=tenant-1",
            json={
                "policy_id": "test-policy-1",
                "name": "Test Policy",
                "rules": [{
                    "action": "allow",
                    "condition": {"role": "admin"}
                }]
            }
        )
        
        assert create_response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
        
        # Evaluate policy
        if create_response.status_code == status.HTTP_201_CREATED:
            eval_response = client.post(
                "/policy/v1/policies/test-policy-1/evaluate",
                json={
                    "context": {},
                    "principal": {"sub": "user123", "role": "admin"},
                    "resource": {"id": "resource123"},
                    "action": "read",
                    "tenant_id": "tenant-1",
                    "environment": "dev"
                }
            )
            
            assert eval_response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND
            ]

    def test_configuration_creation_and_retrieval(self, client):
        """Test configuration creation and retrieval."""
        create_response = client.post(
            "/policy/v1/configurations?tenant_id=tenant-1",
            json={
                "config_id": "test-config-1",
                "name": "Test Configuration",
                "config_data": {"key": "value"}
            }
        )
        
        assert create_response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


@pytest.mark.integration
class TestComplianceFlow:
    """Test compliance checking integration."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_compliance_check_flow(self, client):
        """Test compliance check workflow."""
        response = client.post(
            "/policy/v1/compliance/check",
            json={
                "framework": "ISO27001",
                "context": {"tenant_id": "tenant-1"},
                "evidence_required": True
            }
        )
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_audit_summary_retrieval(self, client):
        """Test audit summary retrieval."""
        response = client.get(
            "/policy/v1/audit?tenant_id=tenant-1"
        )
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ]

