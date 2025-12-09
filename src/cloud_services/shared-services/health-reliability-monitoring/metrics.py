"""
Prometheus metrics for Health & Reliability Monitoring self-observability (NFR-5).

Guarded to reuse existing collectors when modules are imported multiple times
during test collection (prevents duplicated timeseries errors).
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, REGISTRY


def _get_or_create(metric_cls, name: str, documentation: str, **kwargs):
    existing = getattr(REGISTRY, "_names_to_collectors", {}).get(name)
    if existing:
        return existing
    return metric_cls(name, documentation, registry=REGISTRY, **kwargs)


telemetry_ingested_total = _get_or_create(
    Counter,
    "health_reliability_monitoring_telemetry_ingested_total",
    "Number of telemetry payloads accepted",
    labelnames=("telemetry_type",),
)

evaluation_latency_seconds = _get_or_create(
    Histogram,
    "health_reliability_monitoring_evaluation_latency_seconds",
    "Time spent evaluating telemetry batches",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

safe_to_act_decisions_total = _get_or_create(
    Counter,
    "health_reliability_monitoring_safe_to_act_decisions_total",
    "Safe-to-Act decisions emitted",
    labelnames=("mode", "allowed"),
)

queue_depth_gauge = _get_or_create(
    Gauge,
    "health_reliability_monitoring_ingestion_queue_depth",
    "Current telemetry queue depth",
)
