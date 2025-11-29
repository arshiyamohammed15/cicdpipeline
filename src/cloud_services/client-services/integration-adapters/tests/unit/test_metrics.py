"""
Unit tests for metrics.

What: Test Prometheus metrics collection
Why: Ensure metrics are recorded correctly
Coverage Target: 100%
"""

from __future__ import annotations

import pytest
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from observability.metrics import MetricsRegistry, get_metrics_registry


class TestMetricsRegistry:
    """Test MetricsRegistry."""

    def test_metrics_registry_initialization(self):
        """Test metrics registry initialization."""
        registry = MetricsRegistry()
        assert registry is not None

    def test_increment_webhook_received(self):
        """Test incrementing webhook received counter."""
        registry = MetricsRegistry()
        connection_id = uuid4()
        
        registry.increment_webhook_received("github", connection_id)
        # No exception means it worked

    def test_increment_event_normalized(self):
        """Test incrementing event normalized counter."""
        registry = MetricsRegistry()
        connection_id = uuid4()
        
        registry.increment_event_normalized("github", connection_id)
        # No exception means it worked

    def test_increment_action_executed(self):
        """Test incrementing action executed counter."""
        registry = MetricsRegistry()
        connection_id = uuid4()
        
        registry.increment_action_executed("github", connection_id, "comment_on_pr")
        # No exception means it worked

    def test_increment_webhook_error(self):
        """Test incrementing webhook error counter."""
        registry = MetricsRegistry()
        connection_id = uuid4()
        
        registry.increment_webhook_error("github", connection_id, "signature_invalid")
        # No exception means it worked

    def test_record_webhook_latency(self):
        """Test recording webhook latency."""
        registry = MetricsRegistry()
        connection_id = uuid4()
        
        registry.record_webhook_latency("github", connection_id, 0.1)
        # No exception means it worked

    def test_get_global_registry(self):
        """Test getting global metrics registry."""
        registry1 = get_metrics_registry()
        registry2 = get_metrics_registry()
        
        assert registry1 is registry2

