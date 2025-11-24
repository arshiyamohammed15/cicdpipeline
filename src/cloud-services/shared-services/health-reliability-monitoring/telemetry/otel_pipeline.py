"""
OpenTelemetry collector bootstrap for Health & Reliability Monitoring ingestion workers.

Provides helpers to configure exporters and validate telemetry payloads before they
enter the evaluation engine.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable

try:
    from opentelemetry import metrics
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
except ImportError:  # pragma: no cover
    metrics = None
    OTLPMetricExporter = None
    MeterProvider = None
    PeriodicExportingMetricReader = None

from ..config import load_settings

logger = logging.getLogger(__name__)
settings = load_settings()


@dataclass
class TelemetryGuards:
    """Guardrail definitions per NFR-4."""

    max_labels: int = settings.telemetry.label_cardinality_limit
    max_metrics_per_payload: int = 64

    def validate_labels(self, labels: Dict[str, str]) -> None:
        if len(labels) > self.max_labels:
            raise ValueError(f"Label cardinality {len(labels)} exceeds limit {self.max_labels}")

    def validate_metrics(self, metrics_payload: Dict[str, float]) -> None:
        if len(metrics_payload) > self.max_metrics_per_payload:
            raise ValueError("Too many metrics in payload")


def configure_meter_provider() -> None:
    """Wire OTLP exporter for Health & Reliability Monitoring metrics."""
    if not metrics:
        logger.warning("OpenTelemetry not installed; skipping meter provider configuration")
        return

    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=settings.telemetry.otel_exporter_endpoint)
    )
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    logger.info("Configured OpenTelemetry meter provider", extra={"endpoint": settings.telemetry.otel_exporter_endpoint})

