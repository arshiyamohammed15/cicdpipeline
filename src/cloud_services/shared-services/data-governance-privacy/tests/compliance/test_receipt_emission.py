from __future__ import annotations

import pytest

from data_governance_privacy.services import DataGovernanceService  # type: ignore


@pytest.mark.dgp_compliance
@pytest.mark.compliance
def test_privacy_enforcement_emits_receipt(
    governance_service: DataGovernanceService,
    tenant_factory,
) -> None:
    tenant = tenant_factory.create()
    user_id = "compliance-user"
    service = governance_service
    service.policy_engine.register_policy("policy-basic", {"requires_consent": False})
    service.iam.register_permission(tenant.tenant_id, user_id, "data:read")

    enforcement = service.enforce_privacy(
        tenant_id=tenant.tenant_id,
        user_id=user_id,
        action="data:read",
        resource="s3://tenant/data.csv",
        policy_id="policy-basic",
        context={"requested_via": "api"},
        classification_record=None,
        consent_result=None,
    )

    receipts = service.evidence_ledger.get_receipts_by_tenant(tenant.tenant_id)
    assert enforcement["receipt_id"] in {receipt["receipt_id"] for receipt in receipts}

