"""Service layer for SIN stub."""
from __future__ import annotations

from typing import Dict, List, Any, Tuple
from datetime import datetime

from .models import SignalEnvelope, IngestStatus
from .producer_registry import ProducerRegistry
from .validation import ValidationEngine
from .normalization import NormalizationEngine
from .routing import RoutingEngine
from .deduplication import DeduplicationStore
from .dlq import DLQHandler
from .observability import MetricsRegistry, StructuredLogger
from .governance import GovernanceEnforcer


class SignalIngestionService:
    """Coordinates validation, normalization, deduplication, routing, and DLQ."""

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
        governance_enforcer: GovernanceEnforcer,
    ) -> None:
        self.producer_registry = producer_registry
        self.validation_engine = validation_engine
        self.normalization_engine = normalization_engine
        self.routing_engine = routing_engine
        self.deduplication_store = deduplication_store
        self.dlq_handler = dlq_handler
        self.metrics = metrics_registry
        self.logger = structured_logger
        self.governance_enforcer = governance_enforcer

    async def ingest(self, signals: List[SignalEnvelope]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        results: List[Dict[str, Any]] = []
        summary = {"accepted": 0, "rejected": 0, "dlq": 0, "total": len(signals)}

        for sig in signals:
            # Deduplication
            if self.deduplication_store.is_duplicate(sig.signal_id):
                results.append(
                    {
                        "signal_id": sig.signal_id,
                        "status": IngestStatus.REJECTED,
                        "reason": "duplicate",
                        "error_code": "DUPLICATE",
                    }
                )
                summary["rejected"] += 1
                continue

            status, reason, error_code, warnings = self.validation_engine.validate(sig)
            if status == IngestStatus.ACCEPTED:
                normalized = self.normalization_engine.normalize(sig)
                self.routing_engine.route(normalized)
                self.metrics.inc("signals_ingested")
                self.logger.info("signal_ingested", signal_id=sig.signal_id, producer_id=sig.producer_id)
                result_entry: Dict[str, Any] = {"signal_id": sig.signal_id, "status": IngestStatus.ACCEPTED}
                if warnings:
                    result_entry["warnings"] = warnings
                results.append(result_entry)
                summary["accepted"] += 1
            else:
                send_to_dlq = status == IngestStatus.DLQ or error_code in {"MISSING_REQUIRED_FIELDS", "GOVERNANCE_VIOLATION"}
                if send_to_dlq:
                    entry = await self.dlq_handler.send_to_dlq(sig.model_dump(), error_code, reason)
                    results.append(
                        {
                            "signal_id": sig.signal_id,
                            "status": IngestStatus.DLQ,
                            "reason": reason,
                            "error_code": error_code,
                            "dlq_id": entry["dlq_id"],
                        }
                    )
                    summary["dlq"] += 1
                else:
                    results.append(
                        {
                            "signal_id": sig.signal_id,
                            "status": IngestStatus.REJECTED,
                            "reason": reason,
                            "error_code": error_code,
                        }
                    )
                    summary["rejected"] += 1

        return results, summary
