from __future__ import annotations

import asyncio

import pytest

from data_governance_privacy.services import DataGovernanceService  # type: ignore
from data_governance_privacy.tests.harness import PerfRunner, PerfScenario


@pytest.mark.dgp_performance
@pytest.mark.performance
@pytest.mark.asyncio
async def test_classification_p95_under_budget(
    perf_runner: PerfRunner,
    tenant_factory,
) -> None:
    service = DataGovernanceService()
    tenant = tenant_factory.create()

    async def classify_once() -> None:
        await asyncio.to_thread(
            service.classify_data,
            tenant.tenant_id,
            "s3://tenant/data.json",
            {"email": "owner@example.com", "card": "4111111111111111"},
            {"actor_id": "perf"},
        )

    scenario = PerfScenario(
        name="classification",
        iterations=25,
        concurrency=5,
        coroutine_factory=classify_once,
        latency_budget_ms=100,
    )

    results = await perf_runner.run([scenario])
    assert results[0].p95 <= 100


@pytest.mark.dgp_performance
@pytest.mark.performance
@pytest.mark.asyncio
async def test_consent_check_p95_under_budget(
    perf_runner: PerfRunner,
    tenant_factory,
) -> None:
    service = DataGovernanceService()
    tenant = tenant_factory.create()
    subject = "perf-user"
    service.consent_service.grant_consent(
        tenant_id=tenant.tenant_id,
        data_subject_id=subject,
        purpose="analytics",
        legal_basis="consent",
        data_categories=["pii"],
        granted_through="api",
    )

    async def consent_once() -> None:
        await asyncio.to_thread(
            service.check_consent,
            tenant.tenant_id,
            subject,
            "analytics",
            ["pii"],
            "consent",
        )

    scenario = PerfScenario(
        name="consent-check",
        iterations=25,
        concurrency=5,
        coroutine_factory=consent_once,
        latency_budget_ms=20,
    )

    results = await perf_runner.run([scenario])
    assert results[0].p95 <= 20

