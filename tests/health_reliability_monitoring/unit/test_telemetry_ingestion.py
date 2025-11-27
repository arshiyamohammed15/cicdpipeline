import asyncio
import pytest
from datetime import datetime, timezone

from health_reliability_monitoring.services.telemetry_ingestion_service import (
    TelemetryIngestionService,
)
from health_reliability_monitoring.models import TelemetryPayload


@pytest.mark.unit
@pytest.mark.asyncio
async def test_telemetry_ingestion_enforces_label_limit():
    service = TelemetryIngestionService()
    payload = TelemetryPayload(
        component_id="pm-4",
        tenant_id="tenant-1",
        plane="Tenant",
        environment="prod",
        timestamp=datetime.now(timezone.utc),
        metrics={"latency_p95_ms": 120},
        labels={f"k{i}": "v" for i in range(5)},
        telemetry_type="metrics",
    )

    await service.ingest(payload)
    drained = await service.drain()
    assert drained[0].component_id == "pm-4"


@pytest.mark.unit
def test_telemetry_ingestion_blocks_high_cardinality_on_model():
    with pytest.raises(ValueError):
        TelemetryPayload(
            component_id="pm-4",
            tenant_id="tenant-1",
            plane="Tenant",
            environment="prod",
            timestamp=datetime.now(timezone.utc),
            metrics={"latency_p95_ms": 120},
            labels={f"k{i}": "v" for i in range(120)},
            telemetry_type="metrics",
        )

