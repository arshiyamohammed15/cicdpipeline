#!/usr/bin/env python3
"""
Functional test cases mapped to PRD TC-FUNC scenarios.
"""

from __future__ import annotations

from tests.privacy_imports import import_module

services_module = import_module("services")
DataGovernanceService = services_module.DataGovernanceService


def test_func_classification_workflow() -> None:
    service = DataGovernanceService()
    result = service.classify_data(
        tenant_id="tenant-func",
        data_location="fs://records.csv",
        data_content={"customer": {"email": "functional@example.com"}},
        context={"actor_id": "func"},
    )
    assert result["classification_level"] in {"internal", "confidential"}
    assert isinstance(result["performance"]["latency_ms"], float)


def test_func_consent_lifecycle() -> None:
    service = DataGovernanceService()
    grant = service.consent_service.grant_consent(
        tenant_id="tenant-func",
        data_subject_id="subject-func",
        purpose="service_improvement",
        legal_basis="consent",
        data_categories=["behavioral_data"],
        granted_through="api",
        metadata={"version": "2025.1"},
    )
    assert grant["consent_id"]
    check = service.check_consent(
        tenant_id="tenant-func",
        data_subject_id="subject-func",
        purpose="service_improvement",
        data_categories=["behavioral_data"],
        legal_basis="consent",
    )
    assert check["allowed"] is True
    assert service.consent_service.withdraw_consent(grant["consent_id"], reason="requested") is True


def test_func_right_to_erasure_flow() -> None:
    service = DataGovernanceService()
    response = service.submit_rights_request(
        tenant_id="tenant-func",
        data_subject_id="subject-func",
        right_type="erasure",
        verification_data={"ticket": "FUNC-ERASURE-1"},
        additional_info="functional test",
    )
    assert response["request_id"]
    updated = service.rights_service.update_request_status(
        tenant_id="tenant-func",
        request_id=response["request_id"],
        status="completed",
        processed_by="automation",
        notes="Erasure complete",
    )
    assert updated and updated["status"] == "completed"


def test_func_lineage_tracking() -> None:
    service = DataGovernanceService()
    service.record_lineage(
        tenant_id="tenant-func",
        source_data_id="source-A",
        target_data_id="dataset-B",
        transformation_type="enrichment",
        transformation_details={"fields": ["country", "region"]},
        processed_by="pipeline-func",
        system_component="data_fabric",
    )
    lineage = service.query_lineage("tenant-func", "source-A")
    assert lineage["entries"]
