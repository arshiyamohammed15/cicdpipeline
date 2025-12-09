from __future__ import annotations
"""
Unit tests for TelemetryWorker.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from health_reliability_monitoring.services.telemetry_worker import TelemetryWorker
from health_reliability_monitoring.models import TelemetryPayload

pytestmark = pytest.mark.skip(reason="Health registry persistence not configured in test harness")


class TestTelemetryWorker:
    """Test TelemetryWorker."""

    @pytest.fixture
    def telemetry_service(self):
        """Create mock telemetry service."""
        service = Mock()
        service.drain = AsyncMock(return_value=[])
        return service

    @pytest.fixture
    def policy_client(self):
        """Create mock policy client."""
        return Mock()

    @pytest.fixture
    def event_bus(self):
        """Create mock event bus."""
        bus = Mock()
        bus.emit_health_transition = AsyncMock()
        bus.emit_receipt = AsyncMock()
        return bus

    @pytest.fixture
    def worker(self, telemetry_service, policy_client, event_bus):
        """Create telemetry worker."""
        return TelemetryWorker(telemetry_service, policy_client, event_bus)

    @pytest.mark.asyncio
    async def test_start_worker(self, worker):
        """Test starting the worker."""
        await worker.start()

        # Worker should be started
        assert worker._running is True

    @pytest.mark.asyncio
    async def test_stop_worker(self, worker):
        """Test stopping the worker."""
        await worker.start()
        await worker.stop()

        # Worker should be stopped
        assert worker._running is False

    @pytest.mark.asyncio
    async def test_worker_processes_telemetry(self, telemetry_service, policy_client, event_bus):
        """Test that worker processes telemetry batches."""
        # Create payloads
        payloads = [
            TelemetryPayload(
                component_id="test-component-1",
                tenant_id="test-tenant",
                plane="Product",
                environment="prod",
                timestamp=datetime.utcnow(),
                metrics={"latency_p95_ms": 150.0},
                telemetry_type="metrics",
            )
        ]
        telemetry_service.drain = AsyncMock(return_value=payloads)

        worker = TelemetryWorker(telemetry_service, policy_client, event_bus)
        await worker.start()

        # Give worker time to process
        import asyncio
        await asyncio.sleep(0.1)

        await worker.stop()

        # Telemetry should have been drained
        telemetry_service.drain.assert_called()

