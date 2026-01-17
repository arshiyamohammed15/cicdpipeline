"""
SLI Metrics Exporter for ZeroUI Observability Layer.

Exports SLI values as OpenTelemetry metrics for time-series storage.
"""

import logging
from typing import Any, Dict, List

from .sli_calculator import SLIResult

logger = logging.getLogger(__name__)

try:
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False
    metrics = None  # type: ignore


class SLIMetricsExporter:
    """
    Exports SLI values as OpenTelemetry metrics.

    Creates metrics with labels for grouping dimensions (component, channel, etc.).
    """

    def __init__(self, otlp_endpoint: str = "http://localhost:4317"):
        """
        Initialize SLI metrics exporter.

        Args:
            otlp_endpoint: OTLP exporter endpoint
        """
        self._otlp_endpoint = otlp_endpoint
        self._meter = None

        if OTLP_AVAILABLE:
            self._init_meter()

    def _init_meter(self) -> None:
        """Initialize OpenTelemetry meter."""
        try:
            reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=self._otlp_endpoint),
                export_interval_millis=60000,  # Export every 60 seconds
            )
            provider = MeterProvider(metric_readers=[reader])
            metrics.set_meter_provider(provider)
            self._meter = metrics.get_meter(__name__)
            logger.info(f"SLI metrics exporter initialized: {self._otlp_endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize SLI metrics exporter: {e}", exc_info=True)

    def export_sli_results(self, results: List[SLIResult]) -> None:
        """
        Export SLI results as OpenTelemetry metrics.

        Args:
            results: List of SLIResult to export
        """
        if not self._meter or not OTLP_AVAILABLE:
            logger.debug("Meter not initialized, skipping SLI export")
            return

        try:
            # Group results by SLI ID
            by_sli_id: Dict[str, List[SLIResult]] = {}
            for result in results:
                if result.sli_id not in by_sli_id:
                    by_sli_id[result.sli_id] = []
                by_sli_id[result.sli_id].append(result)

            # Export each SLI
            for sli_id, sli_results in by_sli_id.items():
                self._export_sli(sli_id, sli_results)

        except Exception as e:
            logger.error(f"Failed to export SLI results: {e}", exc_info=True)

    def _export_sli(self, sli_id: str, results: List[SLIResult]) -> None:
        """
        Export a single SLI as metrics.

        Args:
            sli_id: SLI ID (e.g., "SLI-A")
            results: List of SLIResult for this SLI
        """
        if not self._meter:
            return

        try:
            # Create gauge metric for SLI value
            gauge = self._meter.create_up_down_counter(
                name=f"zeroui_sli_{sli_id.lower().replace('-', '_')}_value",
                description=f"{results[0].sli_name} (value)",
                unit="1",
            )

            # Create counter for numerator
            numerator_counter = self._meter.create_counter(
                name=f"zeroui_sli_{sli_id.lower().replace('-', '_')}_numerator",
                description=f"{results[0].sli_name} (numerator)",
                unit="1",
            )

            # Create counter for denominator
            denominator_counter = self._meter.create_counter(
                name=f"zeroui_sli_{sli_id.lower().replace('-', '_')}_denominator",
                description=f"{results[0].sli_name} (denominator)",
                unit="1",
            )

            # Export each result
            for result in results:
                # Build labels from grouping
                labels = result.grouping.copy()

                # Record value
                gauge.add(result.value, labels)

                # Record numerator and denominator
                numerator_counter.add(result.numerator, labels)
                denominator_counter.add(result.denominator, labels)

        except Exception as e:
            logger.error(f"Failed to export SLI {sli_id}: {e}", exc_info=True)
