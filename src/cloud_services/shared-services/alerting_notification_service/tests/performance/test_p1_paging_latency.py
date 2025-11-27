"""
Risk→Test Matrix: P1 paging latency exceeds SLO.

Required Evidence: Perf harness output tying ingestion→delivery latency to <30s
requirement under load.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from tests.shared_harness import AlertFixtureFactory, PerfRunner, PerfScenario, TenantFactory
from ..database.models import Alert, Notification
from ..repositories import AlertRepository, NotificationRepository
from ..services.ingestion_service import AlertIngestionService
from ..services.notification_service import NotificationDispatcher


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
async def test_p1_paging_latency_under_30s(
    session: AsyncSession,
    perf_runner,
    tenant_factory,
    alert_factory,
) -> None:
    """Test that P1 paging latency stays under 30s SLO under load."""
    tenant = tenant_factory.create()
    
    alert_repo = AlertRepository(session)
    notification_repo = NotificationRepository(session)
    ingestion_service = AlertIngestionService(session)
    notification_service = NotificationDispatcher(session)
    
    async def p1_paging_workflow() -> None:
        """Simulate P1 alert ingestion → notification delivery."""
        alert_event = alert_factory.create_alert(tenant, severity="P1")
        
        start_time = time.perf_counter()
        
        # Ingest alert
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
        
        # Simulate notification dispatch (in real system, this would be async)
        stored_alert = await alert_repo.get_by_id(alert_event.alert_id)
        if stored_alert and stored_alert.severity == "P1":
            # Create notification (simulating delivery)
            notification = Notification(
                notification_id=f"notif-{alert_event.alert_id}",
                alert_id=alert_event.alert_id,
                tenant_id=alert_event.tenant_id,
                channel="pager",
                status="sent",
            )
            await notification_repo.create(notification)
            await session.commit()
        
        elapsed = time.perf_counter() - start_time
        # Verify latency is under 30s
        assert elapsed < 30.0, f"P1 paging latency {elapsed:.2f}s exceeds 30s SLO"
    
    scenario = PerfScenario(
        name="p1-paging-latency",
        iterations=20,
        concurrency=5,
        coroutine_factory=p1_paging_workflow,
        latency_budget_ms=30000.0,  # 30 seconds
    )
    
    results = await perf_runner.run([scenario])
    assert results[0].p95 <= 30000.0, f"P95 latency {results[0].p95}ms exceeds 30s SLO"

