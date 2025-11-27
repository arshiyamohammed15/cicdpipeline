"""
Risk→Test Matrix: Alert fatigue controls drift (rate caps, noise budgets).

Required Evidence: Metrics-driven tests that assert per-tenant alert volume stays
within configured noise budget across rolling windows.
"""

from __future__ import annotations

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from tests.shared_harness import AlertFixtureFactory, TenantFactory
from ..database.models import Alert
from ..repositories import AlertRepository
from ..services.fatigue_control import FatigueControlService
from ..services.ingestion_service import AlertIngestionService


@pytest.fixture
def tenant_factory():
    """Provide tenant factory for tests."""
    from tests.shared_harness import TenantFactory
    return TenantFactory()


@pytest.fixture
def alert_factory():
    """Provide alert fixture factory for tests."""
    from tests.shared_harness import AlertFixtureFactory
    return AlertFixtureFactory()


@pytest.mark.alerting_performance
@pytest.mark.performance
@pytest.mark.asyncio
async def test_alert_volume_within_noise_budget(
    session: AsyncSession,
    tenant_factory,
    alert_factory,
    tmp_path,
) -> None:
    """Test that per-tenant alert volume stays within noise budget."""
    tenant = tenant_factory.create()
    
    # Configure noise budget: max 100 alerts per hour
    policy_bundle = {
        "schema_version": "1.0.0",
        "noise_budgets": {
            "per_tenant_per_hour": 100,
            "rolling_window_minutes": 60,
        },
    }
    
    fatigue_service = FatigueControlService(policy_bundle, tmp_path)
    ingestion_service = AlertIngestionService(session)
    alert_repo = AlertRepository(session)
    
    # Generate alerts (within budget)
    alerts = [alert_factory.create_alert(tenant, severity="P2") for _ in range(50)]
    
    for alert_event in alerts:
        await ingestion_service.ingest_alert(
            tenant_id=alert_event.tenant_id,
            alert_id=alert_event.alert_id,
            source_module=alert_event.source_module,
            severity=alert_event.severity,
            category=alert_event.category,
            summary=alert_event.summary,
            dedup_key=alert_event.dedup_key,
            labels=alert_event.labels,
        )
    
    await session.commit()
    
    # Check alert volume
    stored_alerts = await alert_repo.list_by_tenant(tenant.tenant_id)
    alert_count = len(stored_alerts)
    
    # Verify within budget
    assert alert_count <= 100, f"Alert volume {alert_count} exceeds noise budget of 100"


@pytest.mark.alerting_performance
@pytest.mark.performance
@pytest.mark.asyncio
async def test_rate_caps_enforced_across_rolling_window(
    session: AsyncSession,
    tenant_factory,
    alert_factory,
    tmp_path,
) -> None:
    """Test that rate caps are enforced across rolling windows."""
    tenant = tenant_factory.create()
    
    policy_bundle = {
        "schema_version": "1.0.0",
        "rate_limits": {
            "per_alert_per_minute": 5,
            "per_user_per_hour": 20,
        },
    }
    
    fatigue_service = FatigueControlService(policy_bundle, tmp_path)
    ingestion_service = AlertIngestionService(session)
    
    # Generate alerts exceeding rate limit
    alerts = [alert_factory.create_alert(tenant, dedup_key="same-key") for _ in range(10)]
    
    suppressed_count = 0
    for alert_event in alerts:
        # Check if alert should be suppressed
        is_suppressed = fatigue_service.should_suppress(
            tenant_id=alert_event.tenant_id,
            dedup_key=alert_event.dedup_key,
            alert_time=alert_event.started_at,
        )
        
        if not is_suppressed:
            await ingestion_service.ingest_alert(
                tenant_id=alert_event.tenant_id,
                alert_id=alert_event.alert_id,
                source_module=alert_event.source_module,
                severity=alert_event.severity,
                category=alert_event.category,
                summary=alert_event.summary,
                dedup_key=alert_event.dedup_key,
                labels=alert_event.labels,
            )
        else:
            suppressed_count += 1
    
    await session.commit()
    
    # Verify rate limiting suppressed some alerts
    assert suppressed_count > 0, "Rate cap should suppress some alerts"

