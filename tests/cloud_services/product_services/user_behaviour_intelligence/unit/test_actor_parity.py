"""
Unit test: Actor Parity (UT-UBI-05).

Per PRD Section 13.1: Test that features and scores are computed identically for human and AI agents.
"""


# Imports handled by conftest.py
import pytest
from user_behaviour_intelligence.features.computation import FeatureComputationService
from user_behaviour_intelligence.models import ActorScope, Dimension
from datetime import datetime, timedelta


@pytest.mark.unit
class TestActorParity:
    """Test actor parity in feature computation."""

    @pytest.mark.unit
    def test_human_and_ai_identical_features(self):
        """Test that identical event patterns produce identical features for human and AI."""
        service = FeatureComputationService()
        
        window_start = datetime.utcnow() - timedelta(hours=24)
        window_end = datetime.utcnow()
        
        # Create identical events for human and AI
        human_events = [
            {"event_type": "file_edited", "timestamp_utc": (window_start + timedelta(hours=i)).isoformat()}
            for i in range(10)
        ]
        
        ai_events = [
            {"event_type": "file_edited", "timestamp_utc": (window_start + timedelta(hours=i)).isoformat()}
            for i in range(10)
        ]
        
        # Compute features for both
        human_feature = service.compute_feature(
            tenant_id="test-tenant",
            actor_scope=ActorScope.ACTOR,
            actor_or_group_id="human-actor",
            feature_name="event_count_24h",
            window_start=window_start,
            window_end=window_end,
            events=human_events
        )
        
        ai_feature = service.compute_feature(
            tenant_id="test-tenant",
            actor_scope=ActorScope.ACTOR,
            actor_or_group_id="ai-actor",
            feature_name="event_count_24h",
            window_start=window_start,
            window_end=window_end,
            events=ai_events
        )
        
        assert human_feature is not None
        assert ai_feature is not None
        assert human_feature.value == ai_feature.value
        assert human_feature.feature_name == ai_feature.feature_name
        assert human_feature.dimension == ai_feature.dimension

