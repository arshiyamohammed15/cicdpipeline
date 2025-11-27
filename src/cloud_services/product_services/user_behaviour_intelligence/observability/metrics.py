"""
Metrics Registry for UBI Module (EPC-9).

What: Prometheus-format metrics per PRD NFR-5
Why: Enable monitoring and alerting
Reads/Writes: Metrics emission
Contracts: UBI PRD NFR-5
Risks: Metrics overhead
"""

import logging
import os
from typing import Dict, Any
from collections import defaultdict

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Fallback metrics storage if prometheus_client not available
    _metrics_store = defaultdict(int)

logger = logging.getLogger(__name__)

# Metrics definitions per PRD NFR-5
if PROMETHEUS_AVAILABLE:
    # Counters
    events_processed_total = Counter(
        'ubi_events_processed_total',
        'Total number of events processed',
        ['tenant_id', 'event_type', 'status']
    )
    
    signals_generated_total = Counter(
        'ubi_signals_generated_total',
        'Total number of signals generated',
        ['tenant_id', 'dimension', 'signal_type']
    )
    
    anomalies_total = Counter(
        'ubi_anomalies_total',
        'Total number of anomalies detected',
        ['tenant_id', 'dimension', 'severity']
    )
    
    receipt_emission_total = Counter(
        'ubi_receipt_emission_total',
        'Total number of receipts emitted',
        ['tenant_id', 'status']
    )
    
    # Histograms
    feature_computation_duration_seconds = Histogram(
        'ubi_feature_computation_duration_seconds',
        'Feature computation duration in seconds',
        ['tenant_id', 'feature_name'],
        buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
    )
    
    baseline_recompute_duration_seconds = Histogram(
        'ubi_baseline_recompute_duration_seconds',
        'Baseline recompute duration in seconds',
        ['tenant_id', 'actor_scope'],
        buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0]
    )
    
    api_request_duration_seconds = Histogram(
        'ubi_api_request_duration_seconds',
        'API request duration in seconds',
        ['tenant_id', 'endpoint', 'method'],
        buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
    )
    
    # Gauges
    queue_size = Gauge(
        'ubi_queue_size',
        'Current event queue size',
        ['tenant_id']
    )
else:
    # Fallback metrics objects
    class FallbackCounter:
        def __init__(self, name, description, labels=None):
            self.name = name
            self.description = description
            self.labels = labels or []
        
        def inc(self, **labels):
            key = f"{self.name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
            _metrics_store[key] = _metrics_store.get(key, 0) + 1
    
    class FallbackHistogram:
        def __init__(self, name, description, labels=None, buckets=None):
            self.name = name
            self.description = description
            self.labels = labels or []
            self.buckets = buckets or []
        
        def observe(self, value, **labels):
            key = f"{self.name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
            if key not in _metrics_store:
                _metrics_store[key] = []
            _metrics_store[key].append(value)
    
    class FallbackGauge:
        def __init__(self, name, description, labels=None):
            self.name = name
            self.description = description
            self.labels = labels or []
        
        def set(self, value, **labels):
            key = f"{self.name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
            _metrics_store[key] = value
    
    events_processed_total = FallbackCounter('ubi_events_processed_total', 'Total number of events processed')
    signals_generated_total = FallbackCounter('ubi_signals_generated_total', 'Total number of signals generated')
    anomalies_total = FallbackCounter('ubi_anomalies_total', 'Total number of anomalies detected')
    receipt_emission_total = FallbackCounter('ubi_receipt_emission_total', 'Total number of receipts emitted')
    feature_computation_duration_seconds = FallbackHistogram('ubi_feature_computation_duration_seconds', 'Feature computation duration')
    baseline_recompute_duration_seconds = FallbackHistogram('ubi_baseline_recompute_duration_seconds', 'Baseline recompute duration')
    api_request_duration_seconds = FallbackHistogram('ubi_api_request_duration_seconds', 'API request duration')
    queue_size = FallbackGauge('ubi_queue_size', 'Current event queue size')


class MetricsRegistry:
    """
    Metrics registry for UBI observability.

    Per UBI PRD NFR-5: Emit Prometheus-format metrics.
    """

    def __init__(self):
        """Initialize metrics registry."""
        self._use_prometheus = (
            os.getenv("UBI_OBSERVABILITY_MODE", "").lower() == "prometheus"
            and PROMETHEUS_AVAILABLE
        )

    def increment_events_processed(
        self,
        tenant_id: str,
        event_type: str,
        status: str
    ) -> None:
        """
        Increment events processed counter.

        Args:
            tenant_id: Tenant identifier
            event_type: Event type
            status: Processing status (success/failure)
        """
        if self._use_prometheus:
            events_processed_total.labels(
                tenant_id=tenant_id,
                event_type=event_type,
                status=status
            ).inc()
        else:
            events_processed_total.inc(tenant_id=tenant_id, event_type=event_type, status=status)

    def increment_signals_generated(
        self,
        tenant_id: str,
        dimension: str,
        signal_type: str
    ) -> None:
        """
        Increment signals generated counter.

        Args:
            tenant_id: Tenant identifier
            dimension: Dimension
            signal_type: Signal type
        """
        if self._use_prometheus:
            signals_generated_total.labels(
                tenant_id=tenant_id,
                dimension=dimension,
                signal_type=signal_type
            ).inc()
        else:
            signals_generated_total.inc(tenant_id=tenant_id, dimension=dimension, signal_type=signal_type)

    def increment_anomalies(
        self,
        tenant_id: str,
        dimension: str,
        severity: str
    ) -> None:
        """
        Increment anomalies counter.

        Args:
            tenant_id: Tenant identifier
            dimension: Dimension
            severity: Severity level
        """
        if self._use_prometheus:
            anomalies_total.labels(
                tenant_id=tenant_id,
                dimension=dimension,
                severity=severity
            ).inc()
        else:
            anomalies_total.inc(tenant_id=tenant_id, dimension=dimension, severity=severity)

    def record_feature_computation_duration(
        self,
        tenant_id: str,
        feature_name: str,
        duration_seconds: float
    ) -> None:
        """
        Record feature computation duration.

        Args:
            tenant_id: Tenant identifier
            feature_name: Feature name
            duration_seconds: Duration in seconds
        """
        if self._use_prometheus:
            feature_computation_duration_seconds.labels(
                tenant_id=tenant_id,
                feature_name=feature_name
            ).observe(duration_seconds)
        else:
            feature_computation_duration_seconds.observe(duration_seconds, tenant_id=tenant_id, feature_name=feature_name)

    def record_baseline_recompute_duration(
        self,
        tenant_id: str,
        actor_scope: str,
        duration_seconds: float
    ) -> None:
        """
        Record baseline recompute duration.

        Args:
            tenant_id: Tenant identifier
            actor_scope: Actor scope
            duration_seconds: Duration in seconds
        """
        if self._use_prometheus:
            baseline_recompute_duration_seconds.labels(
                tenant_id=tenant_id,
                actor_scope=actor_scope
            ).observe(duration_seconds)
        else:
            baseline_recompute_duration_seconds.observe(duration_seconds, tenant_id=tenant_id, actor_scope=actor_scope)

    def record_api_request_duration(
        self,
        tenant_id: str,
        endpoint: str,
        method: str,
        duration_seconds: float
    ) -> None:
        """
        Record API request duration.

        Args:
            tenant_id: Tenant identifier
            endpoint: API endpoint
            method: HTTP method
            duration_seconds: Duration in seconds
        """
        if self._use_prometheus:
            api_request_duration_seconds.labels(
                tenant_id=tenant_id,
                endpoint=endpoint,
                method=method
            ).observe(duration_seconds)
        else:
            api_request_duration_seconds.observe(duration_seconds, tenant_id=tenant_id, endpoint=endpoint, method=method)

    def set_queue_size(self, tenant_id: str, size: int) -> None:
        """
        Set queue size gauge.

        Args:
            tenant_id: Tenant identifier
            size: Queue size
        """
        if self._use_prometheus:
            queue_size.labels(tenant_id=tenant_id).set(size)
        else:
            queue_size.set(size, tenant_id=tenant_id)

    def increment_receipt_emission(
        self,
        tenant_id: str,
        status: str
    ) -> None:
        """
        Increment receipt emission counter.

        Args:
            tenant_id: Tenant identifier
            status: Emission status (success/failure)
        """
        if self._use_prometheus:
            receipt_emission_total.labels(
                tenant_id=tenant_id,
                status=status
            ).inc()
        else:
            receipt_emission_total.inc(tenant_id=tenant_id, status=status)


def get_metrics_text() -> str:
    """
    Get Prometheus format metrics text.

    Returns:
        Prometheus format metrics string
    """
    if PROMETHEUS_AVAILABLE:
        return generate_latest(REGISTRY).decode('utf-8')
    else:
        # Fallback: generate simple Prometheus format
        lines = []
        for key, value in _metrics_store.items():
            if isinstance(value, list):
                # Histogram
                lines.append(f"# TYPE {key.split(':')[0]} histogram")
                lines.append(f"{key.split(':')[0]}_count {len(value)}")
                if value:
                    lines.append(f"{key.split(':')[0]}_sum {sum(value)}")
            else:
                # Counter or Gauge
                lines.append(f"# TYPE {key.split(':')[0]} counter")
                lines.append(f"{key} {value}")
        return '\n'.join(lines) + '\n'

