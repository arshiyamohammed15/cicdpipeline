"""Metrics utilities for Alerting & Notification Service."""
from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

from ..config import get_settings

settings = get_settings()

ALERT_INGEST_COUNTER = Counter(
    f"{settings.observability.metrics_namespace}_alerts_ingested_total",
    "Number of alerts ingested",
    ["severity"],
)

NOTIFICATION_COUNTER = Counter(
    f"{settings.observability.metrics_namespace}_notifications_total",
    "Notifications sent",
    ["channel", "status"],
)

DEDUP_LATENCY = Histogram(
    f"{settings.observability.metrics_namespace}_dedup_latency_seconds",
    "Latency of deduplication pipeline",
)

QUEUE_DEPTH = Gauge(
    f"{settings.observability.metrics_namespace}_queue_depth",
    "Notification queue depth",
)

STREAM_SUBSCRIBERS = Gauge(
    f"{settings.observability.metrics_namespace}_stream_subscribers",
    "Number of active alert stream subscribers",
)

AUTOMATION_EXECUTIONS = Counter(
    f"{settings.observability.metrics_namespace}_automation_executions_total",
    "Automation hook executions",
    ["status"],
)


def register_metrics():
    # Import-time definition registers metrics once; placeholder for future hooks.
    return True
