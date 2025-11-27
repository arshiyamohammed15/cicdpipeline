from __future__ import annotations

import pytest

from data_governance_privacy.services import DataGovernanceService  # type: ignore


@pytest.mark.dgp_regression
@pytest.mark.integration
def test_multistep_consent_and_privacy_enforcement(
    governance_service: DataGovernanceService,
    tenant_factory,
) -> None:
    tenant = tenant_factory.create()
    service = governance_service
    user_id = "analyst-1"

    service.policy_engine.register_policy(
        "policy-consent-required",
        {"requires_consent": True},
    )
    service.iam.register_permission(tenant.tenant_id, user_id, "data:export")

    consent = service.consent_service.grant_consent(
        tenant_id=tenant.tenant_id,
        data_subject_id="actor-42",
        purpose="analytics",
        legal_basis="consent",
        data_categories=["pii"],
        granted_through="edge",
        metadata={"version": "1.1"},
    )

    consent_check = service.check_consent(
        tenant_id=tenant.tenant_id,
        data_subject_id="actor-42",
        purpose="analytics",
        data_categories=["pii"],
        legal_basis="consent",
    )
    assert consent_check["allowed"] is True
    assert consent_check["consent_id"] == consent["consent_id"]

    classification = service.classify_data(
        tenant_id=tenant.tenant_id,
        data_location="s3://tenant/pii.csv",
        data_content={"document": "Customer 123, email admin@example.com"},
        context={"actor_id": user_id},
    )

    enforcement = service.enforce_privacy(
        tenant_id=tenant.tenant_id,
        user_id=user_id,
        action="data:export",
        resource="s3://tenant/pii.csv",
        policy_id="policy-consent-required",
        context={"requested_via": "api"},
        classification_record=classification,
        consent_result=consent_check,
    )

    assert enforcement["allowed"] is True
    assert enforcement["receipt_id"]

