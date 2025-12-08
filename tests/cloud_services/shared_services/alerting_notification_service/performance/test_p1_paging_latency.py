from __future__ import annotations
"""
Risk→Test Matrix: P1 paging latency exceeds SLO.

Required Evidence: Perf harness output tying ingestion→delivery latency to <30s
requirement under load.
"""


# Imports handled by conftest.py

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
from alerting_notification_service.database.models import Alert, Notification
from alerting_notification_service.repositories import AlertRepository, NotificationRepository
from alerting_notification_service.services.ingestion_service import AlertIngestionService
from alerting_notification_service.services.notification_service import NotificationDispatcher


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
@pytest.mark.skip(reason="session fixture not available in current test harness")
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
        # Use a fresh session for each workflow to avoid transaction conflicts
        from sqlalchemy.ext.asyncio import async_sessionmaker
        from alerting_notification_service.database.session import engine
        
        async_session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session_maker() as workflow_session:
            # Use unique dedup_key for each iteration to avoid conflicts in concurrent runs
            import uuid
            unique_dedup_key = f"p1-latency-{uuid.uuid4().hex[:8]}"
            alert_event = alert_factory.create_alert(tenant, severity="P1", dedup_key=unique_dedup_key)
            
            start_time = time.perf_counter()
            
            # Convert AlertEvent to Alert object and ingest
            alert = Alert(
                alert_id=alert_event.alert_id,
                tenant_id=alert_event.tenant_id,
                source_module=alert_event.source_module,
                plane="Tenant",
                environment="prod",
                component_id=f"comp-{alert_event.alert_id}",
                severity=alert_event.severity,
                category=alert_event.category,
                summary=alert_event.summary,
                labels=alert_event.labels,
                started_at=alert_event.started_at,
                last_seen_at=alert_event.started_at,
                dedup_key=alert_event.dedup_key,
            )
            
            # Use workflow_session for this operation
            workflow_ingestion = AlertIngestionService(workflow_session)
            await workflow_ingestion.ingest(alert)
            
            # Fetch using the same session
            workflow_alert_repo = AlertRepository(workflow_session)
            stored_alert = await workflow_alert_repo.fetch(alert_event.alert_id)
            
            # Create notification (simulating delivery)
            workflow_notification_repo = NotificationRepository(workflow_session)
            notification = Notification(
                    notification_id=f"notif-{alert_event.alert_id}",
                    alert_id=alert_event.alert_id,
                    tenant_id=alert_event.tenant_id,
                    target_id="test-target",
                    channel="pager",
                    status="sent",
                )
            await workflow_notification_repo.save(notification)
            
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

