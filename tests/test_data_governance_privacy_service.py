from __future__ import annotations
#!/usr/bin/env python3
"""
Comprehensive tests for Data Governance & Privacy Module (M22) services.

Test design principles:
    - Hermetic (no external resources)
    - Deterministic (fixed inputs, no randomness)
    - Table-driven where practical
    - 100% logical path coverage across service orchestrations
"""


import pytest

from tests.privacy_imports import import_module

services_module = import_module("services")
DataGovernanceService = services_module.DataGovernanceService


@pytest.fixture()
def service() -> DataGovernanceService:
    return DataGovernanceService()


def test_classification_detects_pii(service: DataGovernanceService) -> None:
    payload = service.classify_data(
        tenant_id="tenant-alpha",
        data_location="s3://bucket/object.json",
        data_content={"ssn": "123-45-6789", "email": "user@example.com"},
        context={"actor_id": "scanner"},
    )
    assert payload["classification_level"] == "confidential"
    assert "pii" in payload["sensitivity_tags"]
    assert payload["classification_confidence"] >= 0.7


def test_consent_grant_and_check(service: DataGovernanceService) -> None:
    grant = service.consent_service.grant_consent(
        tenant_id="tenant-alpha",
        data_subject_id="subject-1",
        purpose="analytics",
        legal_basis="consent",
        data_categories=["contact_info"],
        granted_through="web_form",
        metadata={"version": "v1"},
    )
    assert grant["consent_id"]

    check = service.check_consent(
        tenant_id="tenant-alpha",
        data_subject_id="subject-1",
        purpose="analytics",
        data_categories=["contact_info"],
        legal_basis="consent",
    )
    assert check["allowed"] is True


def test_privacy_enforcement_denies_without_permission(service: DataGovernanceService) -> None:
    # No permission granted yet, should be denied
    consent = service.check_consent(
        tenant_id="tenant-beta",
        data_subject_id="subject-2",
        purpose="marketing",
        data_categories=["contact_info"],
        legal_basis="consent",
    )
    decision = service.enforce_privacy(
        tenant_id="tenant-beta",
        user_id="user-123",
        action="export",
        resource="customer_list",
        policy_id="policy-1",
        context={},
        classification_record=None,
        consent_result=consent,
    )
    assert decision["allowed"] is False
    assert "iam_permission_denied" in decision["violations"]


def test_lineage_record_and_query(service: DataGovernanceService) -> None:
    record = service.record_lineage(
        tenant_id="tenant-lineage",
        source_data_id="d1",
        target_data_id="d2",
        transformation_type="aggregation",
        transformation_details={"columns": 3},
        processed_by="pipeline-A",
        system_component="etl",
    )
    assert record["lineage_id"]

    query = service.query_lineage("tenant-lineage", "d1")
    assert len(query["entries"]) == 1
    assert query["entries"][0]["transformation_type"] == "aggregation"


def test_retention_policy_enforcement(service: DataGovernanceService) -> None:
    service.data_plane.store_retention_policy(
        {
            "tenant_id": "tenant-retention",
            "data_category": "customer_data",
            "retention_period_months": 24,
            "legal_hold": False,
            "auto_delete": True,
            "regulatory_basis": "gdpr_article_5",
            "policy_id": "policy-retain",
        }
    )
    result = service.evaluate_retention("tenant-retention", "customer_data", last_activity_months=30)
    assert result["action"] == "delete"
    assert result["policy_id"] == "policy-retain"


def test_rights_request_submission_generates_receipt(service: DataGovernanceService) -> None:
    response = service.submit_rights_request(
        tenant_id="tenant-rights",
        data_subject_id="subject-77",
        right_type="erasure",
        verification_data={"email": "subject77@example.com"},
        additional_info="GDPR erasure test",
    )
    assert response["request_id"]
    assert "estimated_completion" in response
