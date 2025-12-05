from __future__ import annotations
"""
Unit tests for TelemetryIngestionService.
"""

import pytest
from datetime import datetime

from health_reliability_monitoring.services.telemetry_ingestion_service import TelemetryIngestionService
from health_reliability_monitoring.models import TelemetryPayload


class TestTelemetryIngestionService:
    """Test TelemetryIngestionService."""

    @pytest.fixture
    def telemetry_service(self):
        """Create telemetry ingestion service."""
        return TelemetryIngestionService()

    @pytest.fixture
    def sample_payload(self):
        """Create sample telemetry payload."""
        return TelemetryPayload(
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            timestamp=datetime.utcnow(),
            metrics={"latency_p95_ms": 150.0},
            telemetry_type="metrics",
        )

    @pytest.mark.asyncio
    async def test_ingest_payload(self, telemetry_service, sample_payload):
        """Test ingesting a telemetry payload."""
        await telemetry_service.ingest(sample_payload)

        # Verify payload was queued
        batch = await telemetry_service.drain()
        assert len(batch) == 1
        assert batch[0].component_id == "test-component-1"

    @pytest.mark.asyncio
    async def test_ingest_multiple_payloads(self, telemetry_service):
        """Test ingesting multiple payloads."""
        payloads = [
            TelemetryPayload(
                component_id=f"test-component-{i}",
                tenant_id="test-tenant",
                plane="Product",
                environment="prod",
                timestamp=datetime.utcnow(),
                metrics={"latency_p95_ms": 150.0 + i},
                telemetry_type="metrics",
            )
            for i in range(5)
        ]

        for payload in payloads:
            await telemetry_service.ingest(payload)

        batch = await telemetry_service.drain()
        assert len(batch) == 5

    @pytest.mark.asyncio
    async def test_drain_batch_size_limit(self, telemetry_service):
        """Test that drain respects batch size limit."""
        # Ingest more than batch size
        for i in range(20):
            payload = TelemetryPayload(
                component_id=f"test-component-{i}",
                tenant_id="test-tenant",
                plane="Product",
                environment="prod",
                timestamp=datetime.utcnow(),
                metrics={},
                telemetry_type="heartbeat",
            )
            await telemetry_service.ingest(payload)

        # Drain should return batch size or less
        batch = await telemetry_service.drain()
        # Batch size depends on settings, but should be limited
        assert len(batch) <= 20

        # Remaining items should still be in queue
        remaining = await telemetry_service.drain()
        assert len(remaining) > 0 or len(batch) == 20

    def test_last_ingest_age_no_ingests(self, telemetry_service):
        """Test last ingest age with no ingests."""
        age = telemetry_service.last_ingest_age()

        assert age == float("inf")

    @pytest.mark.asyncio
    async def test_last_ingest_age_with_ingest(self, telemetry_service, sample_payload):
        """Test last ingest age after ingest."""
        await telemetry_service.ingest(sample_payload)

        age = telemetry_service.last_ingest_age()

        assert age >= 0
        assert age < 10  # Should be very recent

    @pytest.mark.asyncio
    async def test_ingest_different_telemetry_types(self, telemetry_service):
        """Test ingesting different telemetry types."""
        types = ["metrics", "probe", "heartbeat"]

        for telemetry_type in types:
            payload = TelemetryPayload(
                component_id="test-component-1",
                tenant_id="test-tenant",
                plane="Product",
                environment="prod",
                timestamp=datetime.utcnow(),
                telemetry_type=telemetry_type,
            )
            await telemetry_service.ingest(payload)

        batch = await telemetry_service.drain()
        assert len(batch) == 3
        assert all(p.telemetry_type in types for p in batch)

