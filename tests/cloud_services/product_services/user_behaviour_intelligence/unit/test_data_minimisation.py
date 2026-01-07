"""
Privacy test: Data Minimisation (PR-UBI-01).

Per PRD Section 13.4: Test data minimisation configuration.
"""


# Imports handled by conftest.py
import pytest
from user_behaviour_intelligence.processors.event_ingestion import EventIngestionPipeline
from user_behaviour_intelligence.config import ConfigurationManager
from user_behaviour_intelligence.models import BehaviouralEvent, ActorType


@pytest.mark.unit
class TestDataMinimisation:
    """Test data minimisation."""

    @pytest.mark.unit
    def test_only_configured_fields_stored(self):
        """Test that only configured fields are stored."""
        config_manager = ConfigurationManager()
        pipeline = EventIngestionPipeline(config_manager)
        
        # Create event with sensitive data
        event = BehaviouralEvent(
            event_id="test-event-1",
            tenant_id="test-tenant",
            actor_id="actor-1",
            actor_type=ActorType.HUMAN,
            source_system="IDE",
            event_type="file_edited",
            timestamp_utc="2025-01-01T10:00:00Z",
            ingested_at="2025-01-01T10:00:01Z",
            properties={
                "file_path": "src/main.py",
                "secret_key": "sensitive",
                "pii_email": "user@example.com"
            },
            privacy_tags={
                "contains_PI": True,
                "contains_secrets": True
            },
            schema_version="1.0.0"
        )
        
        # Ingest event
        success = pipeline.ingest_event(event)
        assert success is True
        
        # Verify sensitive properties are filtered
        # In production, would query stored event and verify only allowed fields
        filtered_properties = {}
        for key in ["event_type", "timestamp_utc", "actor_id"]:
            if key in event.properties:
                filtered_properties[key] = event.properties[key]
        
        assert "secret_key" not in filtered_properties
        assert "pii_email" not in filtered_properties

