"""
Performance test: High Webhook Volume (PT-IA-01).

What: Test webhook processing under high volume
Why: Ensure system meets latency and throughput requirements
Coverage Target: Performance requirements per NFR-1, NFR-2
"""

from __future__ import annotations

import pytest
import time
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from services.signal_mapper import SignalMapper


class TestHighWebhookVolume:
    """Test high webhook volume performance."""

    def test_signal_mapping_performance(self):
        """Test signal mapping performance."""
        mapper = SignalMapper()
        
        provider_event = {
            "action": "opened",
            "pull_request": {"number": 123, "title": "Test"},
            "repository": {"full_name": "org/repo"},
        }
        
        # Measure mapping latency
        start_time = time.perf_counter()
        for _ in range(100):
            mapper.map_provider_event_to_signal_envelope(
                provider_id="github",
                connection_id="connection-123",
                tenant_id="tenant-123",
                provider_event=provider_event,
                provider_event_type="pull_request.opened",
                occurred_at=datetime.utcnow(),
            )
        end_time = time.perf_counter()
        
        avg_latency_ms = ((end_time - start_time) / 100) * 1000
        
        # Should be fast (mapping should be < 10ms per event)
        assert avg_latency_ms < 10

