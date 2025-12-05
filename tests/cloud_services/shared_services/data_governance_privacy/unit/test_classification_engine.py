from __future__ import annotations

# Imports handled by conftest.py

import pytest

from data_governance_privacy.services import DataGovernanceService  # type: ignore


@pytest.mark.dgp_regression
@pytest.mark.unit
def test_classification_detects_financial_data(
    governance_service: DataGovernanceService,
    tenant_factory,
) -> None:
    tenant = tenant_factory.create()
    payload = {
        "email": "delegate@example.com",
        "card": "4111 1111 1111 1111",
        "notes": "customer escalated outage",
    }

    record = governance_service.classify_data(
        tenant_id=tenant.tenant_id,
        data_location="s3://tenant-data/documents/1",
        data_content={"doc": payload},
        context={"actor_id": "automated_scan"},
    )

    assert "financial" in record["sensitivity_tags"]
    assert record["classification_level"] == "restricted"
    assert record["performance"]["p95_ms"] <= 100


@pytest.mark.dgp_regression
@pytest.mark.unit
def test_classification_honors_hints_and_confidence(
    governance_service: DataGovernanceService,
    tenant_factory,
) -> None:
    tenant = tenant_factory.create()
    payload = {"summary": "internal roadmap", "body": "Q4 OKR updates"}

    record = governance_service.classify_data(
        tenant_id=tenant.tenant_id,
        data_location="s3://tenant-data/documents/roadmap",
        data_content=payload,
        context={"actor_id": "product_ops"},
        hints=["proprietary"],
    )

    assert "proprietary" in record["sensitivity_tags"]
    assert record["classification_confidence"] >= 0.75
    assert record["review_required"] is False

