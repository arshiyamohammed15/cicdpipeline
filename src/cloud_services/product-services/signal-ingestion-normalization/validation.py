"""Validation engine stub."""
from __future__ import annotations

from typing import Dict, List, Tuple

from .models import SignalEnvelope, IngestStatus
from .producer_registry import ProducerRegistry, ProducerRegistryError


class ValidationEngine:
    """Lightweight validation enforcing producer registration and contracts."""

    def __init__(self, producer_registry: ProducerRegistry, governance_enforcer, schema_registry) -> None:
        self.producer_registry = producer_registry
        self.governance_enforcer = governance_enforcer
        self.schema_registry = schema_registry

    def validate(self, signal: SignalEnvelope) -> Tuple[IngestStatus, str, str, List[str]]:
        warnings: List[str] = []
        try:
            producer = self.producer_registry.get_producer(signal.producer_id)
        except ProducerRegistryError as exc:
            return IngestStatus.REJECTED, str(exc), "PRODUCER_NOT_REGISTERED", warnings

        if signal.signal_kind not in producer.allowed_signal_kinds:
            return IngestStatus.REJECTED, "signal kind not allowed", "SIGNAL_KIND_NOT_ALLOWED", warnings
        if signal.signal_type not in producer.allowed_signal_types:
            return IngestStatus.REJECTED, "signal type not allowed", "SIGNAL_TYPE_NOT_ALLOWED", warnings

        contract_version = producer.contract_versions.get(signal.signal_type, "1.0.0")
        contract = self.schema_registry.get_contract(signal.signal_type, contract_version)
        if not contract:
            return IngestStatus.REJECTED, "contract not found", "CONTRACT_NOT_FOUND", warnings

        required: List[str] = contract.get("required_fields", [])
        missing = [field for field in required if field not in signal.payload]
        if missing:
            return IngestStatus.REJECTED, f"missing required fields: {missing}", "MISSING_REQUIRED_FIELDS", warnings

        governance_result = self.governance_enforcer.enforce(signal.model_dump())
        if not governance_result.get("allowed", True):
            return IngestStatus.REJECTED, "governance violation", "GOVERNANCE_VIOLATION", warnings
        if governance_result.get("redactions"):
            warnings.append("fields redacted per governance policy")

        return IngestStatus.ACCEPTED, "ok", "ACCEPTED", warnings
