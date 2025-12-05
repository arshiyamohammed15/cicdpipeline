"""
Unit test: Feature Calculation Correctness (UT-UBI-01).

Per PRD Section 13.1: Test feature computation from synthetic events.
"""


# Imports handled by conftest.py
import pytest
from datetime import datetime, timedelta
from user_behaviour_intelligence.features.computation import FeatureComputationService
from user_behaviour_intelligence.models import ActorScope, Dimension


class TestFeatureComputation:
    """Test feature computation correctness."""

    def test_focus_session_length_avg(self):
        """Test focus session length average computation."""
        service = FeatureComputationService()
        
        # Create synthetic events representing focused work
        window_start = datetime.utcnow() - timedelta(hours=24)
        window_end = datetime.utcnow()
        
        events = [
            {"event_type": "focus_session_started", "timestamp_utc": (window_start + timedelta(hours=i)).isoformat()}
            for i in range(5)
        ]
        
        feature = service.compute_feature(
            tenant_id="test-tenant",
            actor_scope=ActorScope.ACTOR,
            actor_or_group_id="actor-1",
            feature_name="focus_session_length_avg",
            window_start=window_start,
            window_end=window_end,
            events=events
        )
        
        assert feature is not None
        assert feature.feature_name == "focus_session_length_avg"
        assert feature.dimension == Dimension.FLOW

    def test_context_switch_rate(self):
        """Test context switch rate computation."""
        service = FeatureComputationService()
        
        window_start = datetime.utcnow() - timedelta(hours=24)
        window_end = datetime.utcnow()
        
        events = [
            {"event_type": "context_switch", "timestamp_utc": (window_start + timedelta(hours=i)).isoformat()}
            for i in range(10)
        ]
        
        feature = service.compute_feature(
            tenant_id="test-tenant",
            actor_scope=ActorScope.ACTOR,
            actor_or_group_id="actor-1",
            feature_name="context_switches_per_hour",
            window_start=window_start,
            window_end=window_end,
            events=events
        )
        
        assert feature is not None
        assert feature.feature_name == "context_switches_per_hour"
        assert feature.value >= 0

