from __future__ import annotations
#!/usr/bin/env python3
"""
Security-focused tests validating tenant isolation and breach prevention.
"""

import pytest
from tests.privacy_imports import import_module

services_module = import_module("services")
DataGovernanceService = services_module.DataGovernanceService


@pytest.mark.dgp_security
@pytest.mark.security
def test_tenant_isolation_enforced() -> None:
    service = DataGovernanceService()

    consent = service.check_consent(
        tenant_id="tenant-sec-a",
        data_subject_id="subject-sec",
        purpose="analytics",
        data_categories=["contact_info"],
        legal_basis="consent",
    )
    decision = service.enforce_privacy(
        tenant_id="tenant-sec-a",
        user_id="user-no-access",
        action="export",
        resource="tenant-sec-b-data",
        policy_id="policy-sec",
        context={},
        classification_record=None,
        consent_result=consent,
    )
    assert decision["allowed"] is False
    assert "iam_permission_denied" in decision["violations"]


@pytest.mark.dgp_security
@pytest.mark.security
def test_receipts_not_visible_cross_tenant() -> None:
    service = DataGovernanceService()
    service.submit_rights_request(
        tenant_id="tenant-sec-a",
        data_subject_id="subject-sec",
        right_type="access",
        verification_data={"ticket": "SEC-123"},
    )
    receipts = service.evidence_ledger.get_receipts_by_tenant("tenant-sec-b")
    assert receipts == []
