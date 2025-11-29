"""
Risk→Test Matrix: Deduplication/correlation regressions create alert storms.

Required Evidence: Golden-path regression comparing input burst vs. deduped
incident count, enforced per PRD FR-3.
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
from alerting_notification_service.database.models import Alert
from alerting_notification_service.repositories import AlertRepository, IncidentRepository
from alerting_notification_service.services.correlation_service import CorrelationService
from alerting_notification_service.services.ingestion_service import AlertIngestionService


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


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_alert_burst_deduplication_golden_path(
    session: AsyncSession,
    tenant_factory,
    alert_factory,
) -> None:
    """Golden-path regression: input burst vs. deduped incident count."""
    tenant = tenant_factory.create()
    
    # Create burst of alerts with same dedup_key
    dedup_key = f"dedup-test-{tenant.tenant_id}"
    alerts = alert_factory.create_alert_burst(tenant, count=10, dedup_key=dedup_key)
    
    alert_repo = AlertRepository(session)
    incident_repo = IncidentRepository(session)
    correlation_service = CorrelationService(session)
    ingestion_service = AlertIngestionService(session)
    
    # Ingest all alerts
    for alert_event in alerts:
        # Convert AlertEvent to Alert object
        alert = Alert(
            alert_id=alert_event.alert_id,
            tenant_id=alert_event.tenant_id,
            source_module=alert_event.source_module,
            plane="Tenant",  # Default plane
            environment="prod",  # Default environment
            component_id=f"comp-{alert_event.alert_id}",  # Default component
            severity=alert_event.severity,
            category=alert_event.category,
            summary=alert_event.summary,
            labels=alert_event.labels,
            started_at=alert_event.started_at,
            last_seen_at=alert_event.started_at,
            dedup_key=alert_event.dedup_key,
        )
        await ingestion_service.ingest(alert)
    
    await session.commit()
    
    # Correlation happens automatically during ingest() via correlation_service.correlate()
    # No need to call process_pending_alerts() separately
    
    # Verify: should have 1 incident (all alerts deduped)
    incidents = await incident_repo.list_by_tenant(tenant.tenant_id)
    assert len(incidents) == 1, f"Expected 1 incident, got {len(incidents)}"
    
    # Verify: all alerts should be linked to same incident
    stored_alerts = await alert_repo.list_by_tenant(tenant.tenant_id)
    incident_ids = {alert.incident_id for alert in stored_alerts if alert.incident_id}
    assert len(incident_ids) == 1, "All alerts should be in same incident"


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_deduplication_preserves_distinct_incidents(
    session: AsyncSession,
    tenant_factory,
    alert_factory,
) -> None:
    """Verify distinct dedup_keys create separate incidents."""
    tenant = tenant_factory.create()
    
    # Create alerts with different dedup_keys
    alerts_a = alert_factory.create_alert_burst(tenant, count=5, dedup_key="dedup-a")
    alerts_b = alert_factory.create_alert_burst(tenant, count=5, dedup_key="dedup-b")
    
    ingestion_service = AlertIngestionService(session)
    correlation_service = CorrelationService(session)
    
    for alert_event in alerts_a + alerts_b:
        # Convert AlertEvent to Alert object
        alert = Alert(
            alert_id=alert_event.alert_id,
            tenant_id=alert_event.tenant_id,
            source_module=alert_event.source_module,
            plane="Tenant",  # Default plane
            environment="prod",  # Default environment
            component_id=f"comp-{alert_event.alert_id}",  # Default component
            severity=alert_event.severity,
            category=alert_event.category,
            summary=alert_event.summary,
            labels=alert_event.labels,
            started_at=alert_event.started_at,
            last_seen_at=alert_event.started_at,
            dedup_key=alert_event.dedup_key,
        )
        await ingestion_service.ingest(alert)
    
    await session.commit()
    
    # Correlation happens automatically during ingest() via correlation_service.correlate()
    # No need to call process_pending_alerts() separately
    
    # Should have 2 incidents (one per dedup_key)
    incident_repo = IncidentRepository(session)
    incidents = await incident_repo.list_by_tenant(tenant.tenant_id)
    assert len(incidents) == 2, f"Expected 2 incidents, got {len(incidents)}"

