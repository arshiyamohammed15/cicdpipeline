"""
Integration test: MMM Subscription (IT-UBI-02).

Per PRD Section 13.2: Test signal emission to event stream for MMM consumption.
"""


# Imports handled by conftest.py
import pytest
import asyncio
from datetime import datetime, timezone
from user_behaviour_intelligence.streaming.publisher import EventStreamPublisher
from user_behaviour_intelligence.streaming.event_bus import InMemoryEventBus
from user_behaviour_intelligence.models import (
    BehaviouralSignal,
    ActorScope,
    Dimension,
    SignalType,
    Severity,
    SignalStatus,
)


@pytest.mark.integration
class TestMMMSubscription:
    """Test MMM signal subscription."""

    @pytest.mark.asyncio
    async def test_signal_emission_to_stream(self):
        """Test that signals are emitted to event stream in correct format."""
        event_bus = InMemoryEventBus()
        publisher = EventStreamPublisher(event_bus=event_bus)
        
        # Create test signal
        signal = BehaviouralSignal(
            signal_id="test-signal-1",
            tenant_id="test-tenant",
            actor_scope=ActorScope.ACTOR,
            actor_or_group_id="actor-1",
            dimension=Dimension.ACTIVITY,
            signal_type=SignalType.RISK,
            score=75.0,
            severity=Severity.WARN,
            status=SignalStatus.ACTIVE,
            evidence_refs=[],
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            resolved_at=None
        )
        
        # Publish signal
        success = await publisher.publish_signal(signal)
        assert success is True
        
        # Verify signal was published to event bus
        # In production, would verify MMM received signal
        assert publisher.signals_published == 1

