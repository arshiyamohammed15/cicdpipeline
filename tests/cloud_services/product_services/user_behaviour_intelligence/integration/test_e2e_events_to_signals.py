"""
Integration test: End-to-End from Events to Signals (IT-UBI-01).

Per PRD Section 13.2: Test full pipeline from PM-3 events to UBI signals.
"""


# Imports handled by conftest.py
import pytest
from datetime import datetime
from user_behaviour_intelligence.integrations.pm3_client import PM3Client
from user_behaviour_intelligence.processors.event_mapper import EventMapper
from user_behaviour_intelligence.processors.event_ingestion import EventIngestionPipeline
from user_behaviour_intelligence.config import ConfigurationManager


class TestE2EEventsToSignals:
    """Test end-to-end event processing."""

    def test_event_processing_pipeline(self):
        """Test event processing from PM-3 SignalEnvelope to UBI BehaviouralEvent."""
        # Initialize components
        config_manager = ConfigurationManager()
        event_mapper = EventMapper()
        ingestion_pipeline = EventIngestionPipeline(config_manager)
        
        # Create test SignalEnvelope
        signal_envelope = {
            "signal_id": "test-signal-1",
            "tenant_id": "test-tenant",
            "actor_id": "actor-1",
            "signal_type": "file_edited",
            "occurred_at": datetime.utcnow().isoformat(),
            "ingested_at": datetime.utcnow().isoformat(),
            "payload": {"file_path": "src/main.py"},
            "resource": {"service_name": "IDE", "actor_type": "human"},
            "schema_version": "1.0.0"
        }
        
        # Map to BehaviouralEvent
        behavioural_event = event_mapper.map_signal_envelope(signal_envelope)
        
        assert behavioural_event is not None
        assert behavioural_event.event_id == "test-signal-1"
        assert behavioural_event.tenant_id == "test-tenant"
        assert behavioural_event.event_type == "file_edited"
        
        # Ingest event
        success = ingestion_pipeline.ingest_event(behavioural_event)
        assert success is True

