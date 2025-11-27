"""
Prometheus metrics for Health & Reliability Monitoring self-observability (NFR-5).
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram


telemetry_ingested_total = Counter(
    "health_reliability_monitoring_telemetry_ingested_total",
    "Number of telemetry payloads accepted",
    labelnames=("telemetry_type",),
)

evaluation_latency_seconds = Histogram(
    "health_reliability_monitoring_evaluation_latency_seconds",
    "Time spent evaluating telemetry batches",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

safe_to_act_decisions_total = Counter(
    "health_reliability_monitoring_safe_to_act_decisions_total",
    "Safe-to-Act decisions emitted",
    labelnames=("mode", "allowed"),
)

queue_depth_gauge = Gauge(
    "health_reliability_monitoring_ingestion_queue_depth",
    "Current telemetry queue depth",
)
