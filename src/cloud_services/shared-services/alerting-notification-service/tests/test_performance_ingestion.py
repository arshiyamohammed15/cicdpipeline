import time
from datetime import datetime

import pytest

from alerting_notification_service.database.models import Alert
from alerting_notification_service.services.ingestion_service import AlertIngestionService


def _alert(idx: int) -> Alert:
    now = datetime.utcnow()
    return Alert(
        alert_id=f"perf-{idx}",
        tenant_id="tenant-perf",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-perf",
        severity="P2",
        priority="P2",
        category="reliability",
        summary=f"Performance alert {idx}",
        labels={},
        started_at=now,
        last_seen_at=now,
        dedup_key=f"comp-perf:{idx}",
    )


@pytest.mark.asyncio
async def test_ingestion_throughput(session):
    service = AlertIngestionService(session)
    start = time.perf_counter()
    for idx in range(50):
        await service.ingest(_alert(idx))
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"Ingestion exceeded threshold: {elapsed}s"

