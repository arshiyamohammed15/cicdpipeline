#!/usr/bin/env python3
"""
Performance-focused tests validating latency targets using hermetic execution.
"""

from __future__ import annotations

from tests.privacy_imports import import_module

services_module = import_module("services")
DataGovernanceService = services_module.DataGovernanceService


def test_latency_targets_within_budget() -> None:
    service = DataGovernanceService()

    for _ in range(25):
        service.classify_data(
            tenant_id="tenant-perf",
            data_location="vault://perf",
            data_content={"email": "perf@example.com"},
            context={"actor_id": "perf"},
        )
        service.check_consent(
            tenant_id="tenant-perf",
            data_subject_id="subject-perf",
            purpose="analytics",
            data_categories=["contact_info"],
            legal_basis="consent",
        )
        service.query_lineage("tenant-perf", "non-existent")

    metrics = service.service_metrics()
    assert metrics["classification"]["latency_p95_ms"] < 100
    assert metrics["consent_p95_ms"] < 20
    assert metrics["privacy_p95_ms"] < 50 or metrics["privacy_p95_ms"] == 0
    assert metrics["lineage_p95_ms"] < 200
