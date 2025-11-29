"""
Prometheus metrics for Integration Adapters Module.

What: Metrics collection per FR-12
Why: Observability and monitoring
Reads/Writes: Prometheus metrics
Contracts: PRD FR-12 (Observability & Diagnostics)
Risks: Metric collection overhead, label cardinality
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

try:
    from prometheus_client import Counter, Histogram, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Fallback: Mock metrics
    class Counter:
        def __init__(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
    
    class Histogram:
        def __init__(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
    
    class Gauge:
        def __init__(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self


class MetricsRegistry:
    """Prometheus metrics registry for Integration Adapters."""

    _instance = None
    _initialized = False
    _metrics_created = False

    def __new__(cls):
        """Singleton pattern to avoid duplicate metrics."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize metrics registry."""
        # Check if metrics have already been created (class-level flag)
        if MetricsRegistry._metrics_created:
            return
        
        # Mark as created before creating metrics to prevent recursion
        MetricsRegistry._metrics_created = True
        
        # Request counts
        self.webhook_received = Counter(
            "integration_adapters_webhooks_received_total",
            "Total webhooks received",
            ["provider_id", "connection_id"]
        )
        
        self.events_normalized = Counter(
            "integration_adapters_events_normalized_total",
            "Total events normalized to SignalEnvelope",
            ["provider_id", "connection_id"]
        )
        
        self.actions_executed = Counter(
            "integration_adapters_actions_executed_total",
            "Total actions executed",
            ["provider_id", "connection_id", "action_type"]
        )
        
        # Error rates
        self.webhook_errors = Counter(
            "integration_adapters_webhook_errors_total",
            "Total webhook processing errors",
            ["provider_id", "connection_id", "error_type"]
        )
        
        self.action_errors = Counter(
            "integration_adapters_action_errors_total",
            "Total action execution errors",
            ["provider_id", "connection_id", "error_type"]
        )
        
        # Latencies
        self.webhook_latency = Histogram(
            "integration_adapters_webhook_processing_seconds",
            "Webhook processing latency",
            ["provider_id", "connection_id"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        )
        
        self.action_latency = Histogram(
            "integration_adapters_action_execution_seconds",
            "Action execution latency",
            ["provider_id", "connection_id", "action_type"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        # Circuit breaker
        self.circuit_opens = Counter(
            "integration_adapters_circuit_opens_total",
            "Total circuit breaker opens",
            ["provider_id", "connection_id"]
        )
        
        # Token refreshes
        self.token_refreshes = Counter(
            "integration_adapters_token_refreshes_total",
            "Total token refreshes",
            ["provider_id", "connection_id"]
        )

    def increment_webhook_received(
        self, provider_id: str, connection_id: UUID
    ) -> None:
        """Increment webhook received counter."""
        self.webhook_received.labels(
            provider_id=provider_id,
            connection_id=str(connection_id)
        ).inc()

    def increment_event_normalized(
        self, provider_id: str, connection_id: UUID
    ) -> None:
        """Increment event normalized counter."""
        self.events_normalized.labels(
            provider_id=provider_id,
            connection_id=str(connection_id)
        ).inc()

    def increment_action_executed(
        self, provider_id: str, connection_id: UUID, action_type: str = "unknown"
    ) -> None:
        """Increment action executed counter."""
        self.actions_executed.labels(
            provider_id=provider_id,
            connection_id=str(connection_id),
            action_type=action_type
        ).inc()

    def increment_webhook_error(
        self, provider_id: str, connection_id: UUID, error_type: str = "unknown"
    ) -> None:
        """Increment webhook error counter."""
        self.webhook_errors.labels(
            provider_id=provider_id,
            connection_id=str(connection_id),
            error_type=error_type
        ).inc()

    def increment_action_error(
        self, provider_id: str, connection_id: UUID, error_type: str = "unknown"
    ) -> None:
        """Increment action error counter."""
        self.action_errors.labels(
            provider_id=provider_id,
            connection_id=str(connection_id),
            error_type=error_type
        ).inc()

    def record_webhook_latency(
        self, provider_id: str, connection_id: UUID, latency: float
    ) -> None:
        """Record webhook processing latency."""
        self.webhook_latency.labels(
            provider_id=provider_id,
            connection_id=str(connection_id)
        ).observe(latency)

    def record_action_latency(
        self, provider_id: str, connection_id: UUID, action_type: str, latency: float
    ) -> None:
        """Record action execution latency."""
        self.action_latency.labels(
            provider_id=provider_id,
            connection_id=str(connection_id),
            action_type=action_type
        ).observe(latency)

    def increment_circuit_open(
        self, provider_id: str, connection_id: UUID
    ) -> None:
        """Increment circuit breaker open counter."""
        self.circuit_opens.labels(
            provider_id=provider_id,
            connection_id=str(connection_id)
        ).inc()

    def increment_token_refresh(
        self, provider_id: str, connection_id: UUID
    ) -> None:
        """Increment token refresh counter."""
        self.token_refreshes.labels(
            provider_id=provider_id,
            connection_id=str(connection_id)
        ).inc()


# Global metrics registry - use class-level singleton
def get_metrics_registry() -> MetricsRegistry:
    """Get global metrics registry instance (singleton)."""
    return MetricsRegistry()

