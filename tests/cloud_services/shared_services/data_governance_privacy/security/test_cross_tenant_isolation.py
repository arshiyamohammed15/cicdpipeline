from __future__ import annotations

# Imports handled by conftest.py

import pytest

from data_governance_privacy.services import DataGovernanceService  # type: ignore


@pytest.mark.dgp_security
@pytest.mark.security
def test_cross_tenant_export_is_denied(
    governance_service: DataGovernanceService,
    tenant_factory,
) -> None:
    tenant_a, tenant_b = tenant_factory.create_pair()
    service = governance_service

    service.policy_engine.register_policy(
        "policy-open",
        {"requires_consent": False},
    )
    service.iam.register_permission(tenant_a.tenant_id, "owner-a", "data:export")

    result = service.privacy_enforcement.enforce(
        tenant_id=tenant_a.tenant_id,
        user_id="attacker-from-b",
        action="data:export",
        resource="s3://tenant-a/pii.csv",
        policy_id="policy-open",
        context={"actor_tenant": tenant_b.tenant_id},
        classification_record=None,
        consent_result=None,
    )

    assert result["allowed"] is False
    assert "iam_permission_denied" in result["violations"]

