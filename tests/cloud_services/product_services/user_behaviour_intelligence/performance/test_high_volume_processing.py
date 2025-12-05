"""
Performance test: High Volume Event Processing (PT-UBI-01).

Per PRD Section 13.3: Test high-volume event processing SLOs.
"""


# Imports handled by conftest.py
import pytest
import time
from user_behaviour_intelligence.processors.event_ingestion import EventIngestionPipeline
from user_behaviour_intelligence.config import ConfigurationManager
from user_behaviour_intelligence.models import BehaviouralEvent, ActorType


class TestHighVolumeProcessing:
    """Test high-volume event processing."""

    def test_1000_events_per_second_throughput(self):
        """Test that system can process 1000 events/second."""
        config_manager = ConfigurationManager()
        pipeline = EventIngestionPipeline(config_manager, max_queue_size=2000)
        
        events = []
        for i in range(1000):
            event = BehaviouralEvent(
                event_id=f"event-{i}",
                tenant_id="test-tenant",
                actor_id="actor-1",
                actor_type=ActorType.HUMAN,
                source_system="IDE",
                event_type="file_edited",
                timestamp_utc="2025-01-01T10:00:00Z",
                ingested_at="2025-01-01T10:00:01Z",
                properties={"file_path": f"src/file_{i}.py"},
                privacy_tags={},
                schema_version="1.0.0"
            )
            events.append(event)
        
        # Process events and measure time
        start_time = time.time()
        for event in events:
            pipeline.ingest_event(event)
        end_time = time.time()
        
        duration = end_time - start_time
        throughput = len(events) / duration
        
        # Assert: 1000 events/second throughput
        assert throughput >= 1000, f"Throughput {throughput} events/second < 1000"
        
        # Assert: Queue size within limits
        assert pipeline.get_queue_size() < 1000

