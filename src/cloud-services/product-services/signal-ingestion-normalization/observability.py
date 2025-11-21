"""
Observability for Signal Ingestion & Normalization (SIN) Module.

What: Metrics, logs, and health checks per PRD F9
Why: Make the ingestion pipeline observable and debuggable
Reads/Writes: Metrics collection, structured logging
Contracts: PRD §4.9 (F9)
Risks: Metric explosion, unbounded label cardinality, log volume
"""

import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class MetricsRegistry:
    """
    Metrics registry for SIN pipeline observability per F9.

    Per PRD F9:
    - Ingested signals per tenant/producer/type
    - Validation failures per cause
    - DLQ counts
    - End-to-end latency (producer → normalized)
    - Backlog size, lag, and processing throughput
    """

    def __init__(self):
        """Initialize metrics registry."""
        # Counters
        self.signals_ingested: Dict[str, int] = defaultdict(int)  # key: tenant_id:producer_id:signal_type
        self.validation_failures: Dict[str, int] = defaultdict(int)  # key: error_code
        self.dlq_counts: Dict[str, int] = defaultdict(int)  # key: tenant_id:producer_id:signal_type
        self.duplicates_discarded: int = 0

        # Latency tracking
        self.latency_samples: List[float] = []  # milliseconds
        self.max_latency_samples = 1000  # Keep last 1000 samples

        # Throughput tracking
        self.signals_processed_per_minute: List[tuple[datetime, int]] = []

        # Backlog tracking
        self.backlog_size: int = 0
        self.processing_lag_seconds: float = 0.0

    def record_signal_ingested(self, tenant_id: str, producer_id: str, signal_type: str) -> None:
        """
        Record signal ingestion.

        Args:
            tenant_id: Tenant ID
            producer_id: Producer ID
            signal_type: Signal type
        """
        key = f"{tenant_id}:{producer_id}:{signal_type}"
        self.signals_ingested[key] += 1

    def record_validation_failure(self, error_code: str) -> None:
        """
        Record validation failure.

        Args:
            error_code: Error code
        """
        self.validation_failures[error_code] += 1

    def record_dlq_entry(self, tenant_id: str, producer_id: str, signal_type: str) -> None:
        """
        Record DLQ entry.

        Args:
            tenant_id: Tenant ID
            producer_id: Producer ID
            signal_type: Signal type
        """
        key = f"{tenant_id}:{producer_id}:{signal_type}"
        self.dlq_counts[key] += 1

    def record_latency(self, latency_ms: float) -> None:
        """
        Record end-to-end latency.

        Args:
            latency_ms: Latency in milliseconds
        """
        self.latency_samples.append(latency_ms)
        if len(self.latency_samples) > self.max_latency_samples:
            self.latency_samples = self.latency_samples[-self.max_latency_samples:]

    def record_throughput(self, signals_count: int) -> None:
        """
        Record processing throughput.

        Args:
            signals_count: Number of signals processed in current minute
        """
        now = datetime.utcnow()
        self.signals_processed_per_minute.append((now, signals_count))
        # Keep last 60 minutes
        cutoff = now.timestamp() - 3600
        self.signals_processed_per_minute = [
            (ts, count) for ts, count in self.signals_processed_per_minute
            if ts.timestamp() > cutoff
        ]

    def update_backlog(self, size: int, lag_seconds: float) -> None:
        """
        Update backlog metrics.

        Args:
            size: Backlog size
            lag_seconds: Processing lag in seconds
        """
        self.backlog_size = size
        self.processing_lag_seconds = lag_seconds

    def record_duplicate_discarded(self) -> None:
        """Record duplicate signal discarded."""
        self.duplicates_discarded += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics.

        Returns:
            Metrics dictionary
        """
        # Calculate latency percentiles
        latency_p50 = None
        latency_p95 = None
        latency_p99 = None
        if self.latency_samples:
            sorted_latencies = sorted(self.latency_samples)
            n = len(sorted_latencies)
            latency_p50 = sorted_latencies[int(n * 0.50)]
            latency_p95 = sorted_latencies[int(n * 0.95)]
            latency_p99 = sorted_latencies[int(n * 0.99)]

        # Calculate throughput
        throughput_per_minute = 0
        if self.signals_processed_per_minute:
            recent = [count for _, count in self.signals_processed_per_minute[-10:]]
            if recent:
                throughput_per_minute = sum(recent) / len(recent)

        return {
            'signals_ingested_total': sum(self.signals_ingested.values()),
            'signals_ingested_by_key': dict(self.signals_ingested),
            'validation_failures_total': sum(self.validation_failures.values()),
            'validation_failures_by_code': dict(self.validation_failures),
            'dlq_counts_total': sum(self.dlq_counts.values()),
            'dlq_counts_by_key': dict(self.dlq_counts),
            'duplicates_discarded': self.duplicates_discarded,
            'latency_p50_ms': latency_p50,
            'latency_p95_ms': latency_p95,
            'latency_p99_ms': latency_p99,
            'latency_samples_count': len(self.latency_samples),
            'throughput_per_minute': throughput_per_minute,
            'backlog_size': self.backlog_size,
            'processing_lag_seconds': self.processing_lag_seconds
        }

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.signals_ingested.clear()
        self.validation_failures.clear()
        self.dlq_counts.clear()
        self.duplicates_discarded = 0
        self.latency_samples.clear()
        self.signals_processed_per_minute.clear()
        self.backlog_size = 0
        self.processing_lag_seconds = 0.0


class StructuredLogger:
    """
    Structured logger for SIN pipeline per F9.

    Per PRD F9: Structured logs for failures and retries (with correlation IDs).
    """

    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """
        Initialize structured logger.

        Args:
            logger_instance: Python logger instance (default: module logger)
        """
        self.logger = logger_instance or logger

    def log_ingestion_start(self, signal_id: str, tenant_id: str, producer_id: str, correlation_id: Optional[str] = None) -> None:
        """Log signal ingestion start."""
        self.logger.info(
            "Signal ingestion started",
            extra={
                'signal_id': signal_id,
                'tenant_id': tenant_id,
                'producer_id': producer_id,
                'correlation_id': correlation_id,
                'event': 'ingestion_start'
            }
        )

    def log_ingestion_success(self, signal_id: str, tenant_id: str, producer_id: str, latency_ms: float, correlation_id: Optional[str] = None) -> None:
        """Log signal ingestion success."""
        self.logger.info(
            "Signal ingested successfully",
            extra={
                'signal_id': signal_id,
                'tenant_id': tenant_id,
                'producer_id': producer_id,
                'latency_ms': latency_ms,
                'correlation_id': correlation_id,
                'event': 'ingestion_success'
            }
        )

    def log_validation_failure(self, signal_id: str, error_code: str, error_message: str, correlation_id: Optional[str] = None) -> None:
        """Log validation failure."""
        self.logger.warning(
            "Signal validation failed",
            extra={
                'signal_id': signal_id,
                'error_code': error_code,
                'error_message': error_message,
                'correlation_id': correlation_id,
                'event': 'validation_failure'
            }
        )

    def log_dlq_entry(self, signal_id: str, dlq_id: str, error_code: str, retry_count: int, correlation_id: Optional[str] = None) -> None:
        """Log DLQ entry creation."""
        self.logger.error(
            "Signal routed to DLQ",
            extra={
                'signal_id': signal_id,
                'dlq_id': dlq_id,
                'error_code': error_code,
                'retry_count': retry_count,
                'correlation_id': correlation_id,
                'event': 'dlq_entry'
            }
        )

    def log_retry(self, signal_id: str, attempt: int, max_retries: int, correlation_id: Optional[str] = None) -> None:
        """Log retry attempt."""
        self.logger.warning(
            "Retrying signal processing",
            extra={
                'signal_id': signal_id,
                'attempt': attempt,
                'max_retries': max_retries,
                'correlation_id': correlation_id,
                'event': 'retry'
            }
        )

    def log_duplicate_discarded(self, signal_id: str, producer_id: str, correlation_id: Optional[str] = None) -> None:
        """Log duplicate signal discarded."""
        self.logger.debug(
            "Duplicate signal discarded",
            extra={
                'signal_id': signal_id,
                'producer_id': producer_id,
                'correlation_id': correlation_id,
                'event': 'duplicate_discarded'
            }
        )

    def log_governance_violation(self, signal_id: str, violation_type: str, details: Dict[str, Any], correlation_id: Optional[str] = None) -> None:
        """Log governance violation."""
        self.logger.warning(
            "Governance violation detected",
            extra={
                'signal_id': signal_id,
                'violation_type': violation_type,
                'details': details,
                'correlation_id': correlation_id,
                'event': 'governance_violation'
            }
        )


class HealthChecker:
    """
    Health checker for SIN pipeline per F9.

    Per PRD F9: Readiness / liveness for ingestion components.
    """

    def __init__(self):
        """Initialize health checker."""
        self.ready = True
        self.checks: Dict[str, bool] = {
            'deduplication_store': True,
            'dlq_store': True,
            'schema_registry': True,
            'downstream_consumers': True
        }
        self.start_time = datetime.utcnow()

    def set_check_status(self, check_name: str, status: bool) -> None:
        """
        Set status for a health check.

        Args:
            check_name: Check name
            status: Check status
        """
        self.checks[check_name] = status
        # Overall ready if all checks pass
        self.ready = all(self.checks.values())

    def is_ready(self) -> bool:
        """
        Check if service is ready.

        Returns:
            True if ready, False otherwise
        """
        return self.ready

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status.

        Returns:
            Health status dictionary
        """
        return {
            'status': 'healthy' if self.ready else 'unhealthy',
            'ready': self.ready,
            'checks': self.checks.copy(),
            'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds()
        }

