"""
Risk→Test Matrix: Cross-tenant data leak via export/consent APIs.

Required Evidence: Multi-tenant negative tests proving Tenant A tokens can never
read/export Tenant B data, including tampered payloads and parallel sessions.
"""

from __future__ import annotations

import pytest

from data_governance_privacy.services import DataGovernanceService  # type: ignore
from data_governance_privacy.tests.harness import IAMTokenFactory, TenantFactory


@pytest.mark.dgp_security
@pytest.mark.security
def test_cross_tenant_export_denied_with_tampered_payload(
    governance_service: DataGovernanceService,
    tenant_factory: TenantFactory,
    token_factory: IAMTokenFactory,
) -> None:
    """Test that tampered tenant_id in payload is rejected."""
    tenant_a, tenant_b = tenant_factory.create_pair()
    service = governance_service
    
    # Grant permission only to Tenant A
    service.iam.register_permission(tenant_a.tenant_id, "user-a", "data:export")
    service.policy_engine.register_policy("policy-export", {"requires_consent": False})
    
    # Create token for Tenant A
    token_a = token_factory.issue_token(tenant_id=tenant_a.tenant_id, user_id="user-a")
    
    # Attempt to export Tenant B data using Tenant A token with tampered payload
    result = service.privacy_enforcement.enforce(
        tenant_id=tenant_b.tenant_id,  # Tampered: using Tenant B ID
        user_id="user-a",
        action="data:export",
        resource="s3://tenant-b/pii.csv",
        policy_id="policy-export",
        context={"actor_tenant": tenant_a.tenant_id},
        classification_record=None,
        consent_result=None,
        override_token=token_a.token,
    )
    
    assert result["allowed"] is False
    assert "iam_permission_denied" in result["violations"]


@pytest.mark.dgp_security
@pytest.mark.security
def test_cross_tenant_export_denied_parallel_sessions(
    governance_service: DataGovernanceService,
    tenant_factory: TenantFactory,
    token_factory: IAMTokenFactory,
) -> None:
    """Test that parallel sessions from different tenants cannot access each other's data."""
    tenant_a, tenant_b = tenant_factory.create_pair()
    service = governance_service
    
    service.iam.register_permission(tenant_a.tenant_id, "user-a", "data:export")
    service.iam.register_permission(tenant_b.tenant_id, "user-b", "data:export")
    service.policy_engine.register_policy("policy-export", {"requires_consent": False})
    
    token_a = token_factory.issue_token(tenant_id=tenant_a.tenant_id, user_id="user-a")
    token_b = token_factory.issue_token(tenant_id=tenant_b.tenant_id, user_id="user-b")
    
    # Session A tries to access Tenant B data
    result_a = service.privacy_enforcement.enforce(
        tenant_id=tenant_b.tenant_id,
        user_id="user-a",
        action="data:export",
        resource="s3://tenant-b/pii.csv",
        policy_id="policy-export",
        context={"actor_tenant": tenant_a.tenant_id},
        classification_record=None,
        consent_result=None,
        override_token=token_a.token,
    )
    
    # Session B tries to access Tenant A data
    result_b = service.privacy_enforcement.enforce(
        tenant_id=tenant_a.tenant_id,
        user_id="user-b",
        action="data:export",
        resource="s3://tenant-a/pii.csv",
        policy_id="policy-export",
        context={"actor_tenant": tenant_b.tenant_id},
        classification_record=None,
        consent_result=None,
        override_token=token_b.token,
    )
    
    assert result_a["allowed"] is False
    assert result_b["allowed"] is False
    assert "iam_permission_denied" in result_a["violations"]
    assert "iam_permission_denied" in result_b["violations"]

