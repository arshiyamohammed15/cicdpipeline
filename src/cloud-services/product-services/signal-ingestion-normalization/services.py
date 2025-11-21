"""
Service layer for Signal Ingestion & Normalization (SIN) Module.

What: Main orchestration service coordinating validation → normalization → routing → deduplication
Why: Encapsulates business logic and coordinates all SIN components
Reads/Writes: Signal processing pipeline (no file I/O)
Contracts: PRD §4 Functional Requirements
Risks: Service must handle errors gracefully and maintain observability
"""

import logging
import time
from typing import List, Dict, Any, Optional

from .models import (
    SignalEnvelope, IngestStatus, SignalIngestResult, IngestResponse,
    ErrorCode, CoercionWarning
)
from .producer_registry import ProducerRegistry
from .validation import ValidationEngine
from .normalization import NormalizationEngine
from .routing import RoutingEngine
from .deduplication import DeduplicationStore
from .dlq import DLQHandler, MAX_RETRY_ATTEMPTS
from .observability import MetricsRegistry, StructuredLogger
from .governance import GovernanceEnforcer

logger = logging.getLogger(__name__)


class SignalIngestionService:
    """
    Main signal ingestion service orchestrating the complete pipeline.

    Per PRD: Coordinates validation → normalization → routing → deduplication
    """

    def __init__(
        self,
        producer_registry: ProducerRegistry,
        validation_engine: ValidationEngine,
        normalization_engine: NormalizationEngine,
        routing_engine: RoutingEngine,
        deduplication_store: DeduplicationStore,
        dlq_handler: DLQHandler,
        metrics_registry: MetricsRegistry,
        structured_logger: StructuredLogger,
        governance_enforcer: GovernanceEnforcer
    ):
        """
        Initialize signal ingestion service.

        Args:
            producer_registry: Producer registry
            validation_engine: Validation engine
            normalization_engine: Normalization engine
            routing_engine: Routing engine
            deduplication_store: Deduplication store
            dlq_handler: DLQ handler
            metrics_registry: Metrics registry
            structured_logger: Structured logger
            governance_enforcer: Governance enforcer
        """
        self.producer_registry = producer_registry
        self.validation_engine = validation_engine
        self.normalization_engine = normalization_engine
        self.routing_engine = routing_engine
        self.deduplication_store = deduplication_store
        self.dlq_handler = dlq_handler
        self.metrics_registry = metrics_registry
        self.structured_logger = structured_logger
        self.governance_enforcer = governance_enforcer

    def ingest_signal(self, signal: SignalEnvelope, tenant_id: Optional[str] = None) -> SignalIngestResult:
        """
        Ingest a single signal through the complete pipeline.

        Args:
            signal: SignalEnvelope to ingest
            tenant_id: Expected tenant ID (from IAM context)

        Returns:
            SignalIngestResult
        """
        start_time = time.time()
        correlation_id = signal.correlation_id or signal.signal_id

        # Log ingestion start
        self.structured_logger.log_ingestion_start(
            signal.signal_id,
            signal.tenant_id,
            signal.producer_id,
            correlation_id
        )

        # Enforce tenant isolation
        if tenant_id and signal.tenant_id != tenant_id:
            error = f"Tenant isolation violation: signal tenant_id {signal.tenant_id} != expected {tenant_id}"
            self.structured_logger.log_validation_failure(
                signal.signal_id,
                ErrorCode.TENANT_ISOLATION_VIOLATION.value,
                error,
                correlation_id
            )
            self.metrics_registry.record_validation_failure(ErrorCode.TENANT_ISOLATION_VIOLATION.value)
            return SignalIngestResult(
                signal_id=signal.signal_id,
                status=IngestStatus.REJECTED,
                error_code=ErrorCode.TENANT_ISOLATION_VIOLATION,
                error_message=error
            )

        # Check for duplicates
        if self.deduplication_store.is_duplicate(signal):
            self.structured_logger.log_duplicate_discarded(
                signal.signal_id,
                signal.producer_id,
                correlation_id
            )
            self.metrics_registry.record_duplicate_discarded()
            return SignalIngestResult(
                signal_id=signal.signal_id,
                status=IngestStatus.REJECTED,
                error_code=None,
                error_message="Duplicate signal discarded"
            )

        # Check ordering
        in_order, ordering_warning = self.deduplication_store.check_ordering(signal)
        warnings = []
        if ordering_warning:
            warnings.append(ordering_warning)

        # Validate signal
        is_valid, validation_error, coercion_warnings = self.validation_engine.validate(signal)
        warnings.extend([w.warning_message for w in coercion_warnings])

        if not is_valid:
            # Check if should retry
            if self.dlq_handler.should_retry(signal.signal_id):
                retry_count = self.dlq_handler.record_retry(signal.signal_id)
                self.structured_logger.log_retry(
                    signal.signal_id,
                    retry_count,
                    MAX_RETRY_ATTEMPTS,
                    correlation_id
                )
                # Return rejected status (caller can retry)
                self.metrics_registry.record_validation_failure(validation_error.error_code.value)
                return SignalIngestResult(
                    signal_id=signal.signal_id,
                    status=IngestStatus.REJECTED,
                    error_code=validation_error.error_code,
                    error_message=validation_error.error_message,
                    warnings=warnings
                )
            else:
                # Permanent failure - route to DLQ
                original_signal = signal.model_dump()
                dlq_id = self.dlq_handler.add_to_dlq(
                    signal,
                    validation_error.error_code,
                    validation_error.error_message,
                    original_signal
                )
                self.structured_logger.log_dlq_entry(
                    signal.signal_id,
                    dlq_id,
                    validation_error.error_code.value,
                    self.dlq_handler.retry_counts.get(signal.signal_id, 0),
                    correlation_id
                )
                self.metrics_registry.record_dlq_entry(
                    signal.tenant_id,
                    signal.producer_id,
                    signal.signal_type
                )
                self.metrics_registry.record_validation_failure(validation_error.error_code.value)
                return SignalIngestResult(
                    signal_id=signal.signal_id,
                    status=IngestStatus.DLQ,
                    error_code=validation_error.error_code,
                    error_message=validation_error.error_message,
                    dlq_id=dlq_id,
                    warnings=warnings
                )

        # Apply governance (redaction)
        redacted_signal, redacted_fields = self.governance_enforcer.apply_redaction(signal)
        if redacted_fields:
            warnings.append(f"Fields redacted: {', '.join(redacted_fields)}")

        # Normalize signal
        try:
            # Create a copy of coercion_warnings list to avoid mutation issues
            normalization_warnings = []
            # Get contract version from producer registry for proper transformation rule lookup
            contract_version = self.producer_registry.get_contract_version(
                redacted_signal.producer_id,
                redacted_signal.signal_type
            )
            normalized_signal = self.normalization_engine.normalize(
                redacted_signal,
                normalization_warnings,
                contract_version=contract_version
            )
            # Extend warnings from normalization (these are new warnings, not duplicates)
            warnings.extend([w.warning_message for w in normalization_warnings])
            # Extend warnings from validation coercion (already collected, avoid duplicates)
            # Note: coercion_warnings from validation are already added to warnings at line 136
        except Exception as e:
            logger.error(f"Normalization error for signal {signal.signal_id}: {e}")
            # Record normalization error (not validation failure)
            self.metrics_registry.record_validation_failure(ErrorCode.NORMALIZATION_ERROR.value)
            # Note: In a more sophisticated metrics system, we might have separate methods
            # for normalization errors vs validation errors, but for now we use the same method
            return SignalIngestResult(
                signal_id=signal.signal_id,
                status=IngestStatus.REJECTED,
                error_code=ErrorCode.NORMALIZATION_ERROR,
                error_message=str(e),
                warnings=warnings
            )

        # Enrich signal with actor and resource context (per PRD F5)
        # Note: Actor and resource context should be extracted from signal or external sources
        # For now, enrich() will apply classification if not already applied in normalize()
        try:
            # Extract actor context from signal if available
            actor_context = None
            if normalized_signal.actor_id:
                actor_context = {'actor_id': normalized_signal.actor_id}
                # Check if payload has additional actor context
                if 'actor_context' in normalized_signal.payload:
                    actor_context.update(normalized_signal.payload['actor_context'])
            
            # Extract resource context from signal.resource if available
            resource_context = None
            if normalized_signal.resource:
                resource_context = normalized_signal.resource.model_dump(exclude_none=True)
            
            # Enrich signal (this will also apply classification if enrich() is called)
            enriched_signal = self.normalization_engine.enrich(
                normalized_signal,
                actor_context=actor_context,
                resource_context=resource_context
            )
            normalized_signal = enriched_signal
        except Exception as e:
            logger.warning(f"Enrichment error for signal {signal.signal_id}: {e}, continuing without enrichment")
            # Don't fail on enrichment errors, just log and continue

        # Route signal
        try:
            routing_results = self.routing_engine.route_signal(normalized_signal)
            # Handle empty routing results (no routing rules match)
            if not routing_results:
                logger.warning(f"No routing rules matched for signal {signal.signal_id} (signal_type: {signal.signal_type})")
                # If no routing rules match, this is not necessarily an error
                # Some signals may not need routing, or routing rules may not be configured yet
                # Continue processing as accepted (signal is valid, just not routed)
            else:
                routing_success = any(success for _, _, success in routing_results)
                if not routing_success:
                    # Check if should retry
                    if self.dlq_handler.should_retry(signal.signal_id):
                        retry_count = self.dlq_handler.record_retry(signal.signal_id)
                        self.structured_logger.log_retry(
                            signal.signal_id,
                            retry_count,
                            MAX_RETRY_ATTEMPTS,
                            correlation_id
                        )
                        return SignalIngestResult(
                            signal_id=signal.signal_id,
                            status=IngestStatus.REJECTED,
                            error_code=ErrorCode.ROUTING_ERROR,
                            error_message="Routing failed, will retry",
                            warnings=warnings
                        )
                    else:
                        # Permanent failure - route to DLQ
                        original_signal = signal.model_dump()
                        dlq_id = self.dlq_handler.add_to_dlq(
                            signal,
                            ErrorCode.ROUTING_ERROR,
                            "Routing failed after retries",
                            original_signal
                        )
                        self.structured_logger.log_dlq_entry(
                            signal.signal_id,
                            dlq_id,
                            ErrorCode.ROUTING_ERROR.value,
                            self.dlq_handler.retry_counts.get(signal.signal_id, 0),
                            correlation_id
                        )
                        self.metrics_registry.record_dlq_entry(
                            signal.tenant_id,
                            signal.producer_id,
                            signal.signal_type
                        )
                        return SignalIngestResult(
                            signal_id=signal.signal_id,
                            status=IngestStatus.DLQ,
                            error_code=ErrorCode.ROUTING_ERROR,
                            error_message="Routing failed after retries",
                            dlq_id=dlq_id,
                            warnings=warnings
                        )
        except Exception as e:
            logger.error(f"Routing error for signal {signal.signal_id}: {e}")
            # Record routing error (not validation failure)
            self.metrics_registry.record_validation_failure(ErrorCode.ROUTING_ERROR.value)
            # Note: In a more sophisticated metrics system, we might have separate methods
            # for routing errors vs validation errors, but for now we use the same method
            return SignalIngestResult(
                signal_id=signal.signal_id,
                status=IngestStatus.REJECTED,
                error_code=ErrorCode.ROUTING_ERROR,
                error_message=str(e),
                warnings=warnings
            )

        # Mark as processed (deduplication)
        self.deduplication_store.mark_processed(normalized_signal)

        # Record metrics
        latency_ms = (time.time() - start_time) * 1000
        self.metrics_registry.record_signal_ingested(
            signal.tenant_id,
            signal.producer_id,
            signal.signal_type
        )
        self.metrics_registry.record_latency(latency_ms)

        # Log success
        self.structured_logger.log_ingestion_success(
            signal.signal_id,
            signal.tenant_id,
            signal.producer_id,
            latency_ms,
            correlation_id
        )

        return SignalIngestResult(
            signal_id=signal.signal_id,
            status=IngestStatus.ACCEPTED,
            warnings=warnings
        )

    def ingest_signals(self, signals: List[SignalEnvelope], tenant_id: Optional[str] = None) -> IngestResponse:
        """
        Ingest multiple signals.

        Args:
            signals: List of SignalEnvelope to ingest
            tenant_id: Expected tenant ID (from IAM context)

        Returns:
            IngestResponse
        """
        results = []
        for signal in signals:
            result = self.ingest_signal(signal, tenant_id)
            results.append(result)

        # Calculate summary
        total = len(results)
        accepted = sum(1 for r in results if r.status == IngestStatus.ACCEPTED)
        rejected = sum(1 for r in results if r.status == IngestStatus.REJECTED)
        dlq = sum(1 for r in results if r.status == IngestStatus.DLQ)

        summary = {
            'total': total,
            'accepted': accepted,
            'rejected': rejected,
            'dlq': dlq
        }

        return IngestResponse(results=results, summary=summary)

