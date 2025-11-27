from __future__ import annotations

import pytest

from data_governance_privacy.services import DataGovernanceService  # type: ignore


@pytest.mark.dgp_regression
@pytest.mark.unit
def test_consent_roundtrip_allows_matching_scope(
    governance_service: DataGovernanceService,
    tenant_factory,
) -> None:
    tenant = tenant_factory.create()
    subject_id = "user-123"

    granted = governance_service.consent_service.grant_consent(
        tenant_id=tenant.tenant_id,
        data_subject_id=subject_id,
        purpose="research",
        legal_basis="legitimate_interest",
        data_categories=["pii", "telemetry"],
        granted_through="ide",
        metadata={"version": "2.0"},
    )

    check = governance_service.check_consent(
        tenant_id=tenant.tenant_id,
        data_subject_id=subject_id,
        purpose="research",
        data_categories=["pii"],
        legal_basis="legitimate_interest",
    )

    assert check["allowed"] is True
    assert check["consent_id"] == granted["consent_id"]
    assert check["legal_basis"] == "legitimate_interest"


@pytest.mark.dgp_regression
@pytest.mark.unit
def test_consent_missing_returns_denied(
    governance_service: DataGovernanceService,
    tenant_factory,
) -> None:
    tenant = tenant_factory.create()
    check = governance_service.check_consent(
        tenant_id=tenant.tenant_id,
        data_subject_id="unknown",
        purpose="marketing",
        data_categories=["pii"],
        legal_basis="consent",
    )
    assert check["allowed"] is False
    assert check["consent_id"] is None

