from __future__ import annotations
"""
Comprehensive tests for Data Governance & Privacy (M22) services.

These tests are derived from the acceptance criteria and test cases defined in
`docs/architecture/modules/DATA_GOVERNANCE_AND_PRIVACY_MODULE.md`, covering:
    - Functional: classification, consent lifecycle, rights workflows
    - Integration: privacy enforcement + IAM/policy integration
    - Performance: latency budgets (classification <=100ms, consent <=20ms)
    - Security: tenant isolation checks
"""


# Imports handled by conftest.py

from time import perf_counter
from typing import Dict
from uuid import uuid4

import pytest

from data_governance_privacy.dependencies import (
    MockM21IAM,
    MockM23PolicyManagement,
    MockM27EvidenceLedger,
    MockM29DataPlane,
    MockM33KeyManagement,
)
from data_governance_privacy.services import (
    ConsentManagementService,
    DataGovernanceService,
    DataRightsService,
    PrivacyEnforcementService,
    RetentionManagementService,
)


def _pii_payload(email: str = "alice@example.com") -> Dict[str, str]:
    return {
        "full_name": "Alice Example",
        "email": email,
        "ssn": "123-45-6789",
        "notes": "VIP customer",
    }


def test_classification_accuracy_and_latency_budget():
    data_plane = MockM29DataPlane()
    kms = MockM33KeyManagement()
    service = DataGovernanceService(data_plane=data_plane, kms=kms)

    latencies = []
    for _ in range(20):
        start = perf_counter()
        record = service.classify_data(
            tenant_id="tenant-privacy",
            data_location="s3://secure/pii.csv",
            data_content=_pii_payload(),
            context={"actor_id": "ml-engine"},
        )
        latencies.append((perf_counter() - start) * 1000)
        assert "pii" in record["sensitivity_tags"]
        assert record["classification_level"] in {"confidential", "restricted"}
        assert record["data_content_hash"]

    assert max(latencies) < 100, "Classification must meet 100ms budget"
    metrics = service.classification_engine.metrics()
    assert metrics["latency_p95_ms"] < 100


def test_consent_lifecycle_grant_check_withdraw():
    data_plane = MockM29DataPlane()
    service = ConsentManagementService(data_plane, MockM33KeyManagement())

    granted = service.grant_consent(
        tenant_id="tenant-privacy",
        data_subject_id="user-123",
        purpose="analytics",
        legal_basis="consent",
        data_categories=["usage"],
        granted_through="web-form",
    )
    assert granted["consent_id"]

    check = service.check_consent(
        tenant_id="tenant-privacy",
        data_subject_id="user-123",
        purpose="analytics",
        data_categories=["usage"],
        required_legal_basis="consent",
    )
    assert check["allowed"] is True
    assert check["latency_ms"] < 20

    assert service.withdraw_consent(check["consent_id"])
    check_after_withdraw = service.check_consent(
        tenant_id="tenant-privacy",
        data_subject_id="user-123",
        purpose="analytics",
        data_categories=["usage"],
        required_legal_basis="consent",
    )
    assert check_after_withdraw["allowed"] is False


def test_privacy_enforcement_requires_consent_and_policy():
    policy_engine = MockM23PolicyManagement()
    policy_engine.register_policy(
        "policy-consent",
        {"requires_consent": True, "min_classification_level": ["confidential", "restricted"]},
    )
    iam = MockM21IAM()
    iam.register_permission("tenant-privacy", "analyst-1", "read")
    enforcement = PrivacyEnforcementService(policy_engine, iam, MockM27EvidenceLedger())
    classification = {
        "classification_level": "confidential",
        "sensitivity_tags": ["pii"],
    }

    denied = enforcement.enforce(
        tenant_id="tenant-privacy",
        user_id="analyst-1",
        action="read",
        resource="dashboards",
        policy_id="policy-consent",
        context={"channel": "api"},
        classification_record=classification,
        consent_result={"allowed": False},
    )
    assert denied["allowed"] is False
    assert "consent_denied" in denied["violations"]

    allowed = enforcement.enforce(
        tenant_id="tenant-privacy",
        user_id="analyst-1",
        action="read",
        resource="dashboards",
        policy_id="policy-consent",
        context={"channel": "api"},
        classification_record=classification,
        consent_result={"allowed": True},
    )
    assert allowed["allowed"] is True
    assert allowed["latency_ms"] < 50


def test_retention_policy_enforcement_actions():
    data_plane = MockM29DataPlane()
    retention = RetentionManagementService(data_plane)
    data_plane.store_retention_policy(
        {
            "policy_id": str(uuid4()),
            "tenant_id": "tenant-privacy",
            "data_category": "logs",
            "retention_period_months": 12,
            "auto_delete": True,
            "regulatory_basis": "GDPR",
        }
    )
    decision = retention.evaluate_retention("tenant-privacy", "logs", last_activity_months=18)
    assert decision["action"] == "delete"
    assert decision["regulatory_basis"] == "GDPR"


def test_rights_request_tenant_isolation():
    data_plane = MockM29DataPlane()
    iam = MockM21IAM()
    rights = DataRightsService(data_plane, iam)
    request = rights.submit_request(
        tenant_id="tenant-A",
        data_subject_id="user-tenant-a",
        right_type="erasure",
        verification_data={"gov_id": "***"},
    )
    # Tenant A can update
    updated = rights.update_request_status("tenant-A", request["request_id"], "completed", "processor-1")
    assert updated and updated["status"] == "completed"
    # Tenant B must not see Tenant A request
    assert rights.update_request_status("tenant-B", request["request_id"], "completed", "processor-2") is None


def test_end_to_end_classification_consent_enforcement_flow():
    service = DataGovernanceService()
    policy_engine = service.policy_engine
    policy_engine.register_policy(
        "policy-e2e",
        {"requires_consent": True, "min_classification_level": ["confidential", "restricted"]},
    )
    service.iam.register_permission("tenant-privacy", "analyst-42", "read")

    classification = service.classify_data(
        tenant_id="tenant-privacy",
        data_location="gs://pii/raw.json",
        data_content=_pii_payload("bob@example.com"),
        context={"actor_id": "pipeline"},
    )
    consent_record = service.consent_service.grant_consent(
        tenant_id="tenant-privacy",
        data_subject_id="user-42",
        purpose="analytics",
        legal_basis="consent",
        data_categories=["usage"],
        granted_through="web-form",
    )
    consent_state = service.check_consent(
        tenant_id="tenant-privacy",
        data_subject_id="user-42",
        purpose="analytics",
        data_categories=["usage"],
        legal_basis="consent",
    )
    assert consent_state["allowed"] is True

    enforcement = service.enforce_privacy(
        tenant_id="tenant-privacy",
        user_id="analyst-42",
        action="read",
        resource="analytics_dashboard",
        policy_id="policy-e2e",
        context={"channel": "ui"},
        classification_record=classification,
        consent_result=consent_state,
    )
    assert enforcement["allowed"] is True
    assert enforcement["receipt_id"]
    assert enforcement["p95_ms"] < 50


def test_data_lineage_latency_reporting():
    data_plane = MockM29DataPlane()
    service = DataGovernanceService(data_plane=data_plane)
    record = service.record_lineage(
        tenant_id="tenant-privacy",
        source_data_id="src-1",
        target_data_id="tgt-1",
        transformation_type="masking",
        transformation_details={"fields": ["email"]},
        processed_by="pipeline-1",
        system_component="spark-job",
    )
    assert record["lineage_id"]

    query = service.query_lineage("tenant-privacy", "src-1")
    assert query["entries"]
    assert query["latency_ms"] < 200


@pytest.mark.parametrize(
    "last_activity,expected_action",
    [
        (3, "retain"),
        (15, "delete"),
    ],
)
def test_retention_matrix_with_legal_hold(last_activity, expected_action):
    data_plane = MockM29DataPlane()
    retention = RetentionManagementService(data_plane)
    data_plane.store_retention_policy(
        {
            "policy_id": str(uuid4()),
            "tenant_id": "tenant-privacy",
            "data_category": "purchases",
            "retention_period_months": 12,
            "auto_delete": True,
            "legal_hold": expected_action == "retain",
            "regulatory_basis": "CCPA",
        }
    )
    decision = retention.evaluate_retention("tenant-privacy", "purchases", last_activity)
    assert decision["action"] == expected_action


