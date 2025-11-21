"""
Governance and privacy enforcement for Signal Ingestion & Normalization (SIN) Module.

What: Privacy and governance enforcement per PRD F10
Why: Enforce ZeroUI privacy and governance rules at signal boundaries
Reads/Writes: Signal redaction/transformation (no file I/O)
Contracts: PRD §4.10 (F10)
Risks: Privacy violations if redaction fails, cross-tenant leakage
"""

import logging
from typing import Dict, Any, List, Optional

from .models import SignalEnvelope
from .dependencies import MockM29DataGovernance

logger = logging.getLogger(__name__)


class GovernanceError(Exception):
    """Exception raised by governance engine."""
    pass


class GovernanceEnforcer:
    """
    Governance and privacy enforcer per F10.

    Per PRD F10:
    - Enforce tenant isolation at all stages
    - Apply field-level redaction and/or dropping of disallowed payloads
    - Respect residency requirements
    - Provide configurable retention
    """

    def __init__(self, data_governance: Optional[MockM29DataGovernance] = None):
        """
        Initialize governance enforcer.

        Args:
            data_governance: Data governance dependency
        """
        self.data_governance = data_governance or MockM29DataGovernance()

    def enforce_tenant_isolation(self, signal: SignalEnvelope, expected_tenant_id: str) -> tuple[bool, Optional[str]]:
        """
        Enforce tenant isolation per F10.

        Args:
            signal: SignalEnvelope to check
            expected_tenant_id: Expected tenant ID (from IAM context)

        Returns:
            (is_valid, error_message) tuple
        """
        if signal.tenant_id != expected_tenant_id:
            return False, f"Tenant isolation violation: signal tenant_id {signal.tenant_id} != expected {expected_tenant_id}"

        return True, None

    def apply_redaction(self, signal: SignalEnvelope) -> tuple[SignalEnvelope, List[str]]:
        """
        Apply field-level redaction per F10.

        Args:
            signal: SignalEnvelope to redact

        Returns:
            (redacted_signal, redacted_fields) tuple
        """
        redacted_fields = []
        redacted_payload = signal.payload.copy()

        # Get disallowed fields from data governance
        disallowed_fields = self.data_governance.get_disallowed_fields(
            signal.tenant_id,
            signal.producer_id,
            signal.signal_type
        )

        # Drop disallowed fields
        for field in disallowed_fields:
            if field in redacted_payload:
                del redacted_payload[field]
                redacted_fields.append(field)
                logger.debug(f"Field redacted (dropped): {field}")

        # Get redaction rules
        redaction_rules = self.data_governance.get_redaction_rules(
            signal.tenant_id,
            signal.producer_id,
            signal.signal_type
        )

        # Apply redaction rules
        for field, action in redaction_rules.items():
            if field in redacted_payload:
                if action == "drop":
                    del redacted_payload[field]
                    redacted_fields.append(field)
                    logger.debug(f"Field redacted (dropped): {field}")
                elif action == "redact":
                    redacted_payload[field] = "[REDACTED]"
                    redacted_fields.append(field)
                    logger.debug(f"Field redacted (masked): {field}")
                elif action == "hash":
                    # Hash the value
                    import hashlib
                    value = str(redacted_payload[field])
                    redacted_payload[field] = hashlib.sha256(value.encode()).hexdigest()[:16]
                    redacted_fields.append(field)
                    logger.debug(f"Field redacted (hashed): {field}")

        # Create redacted signal
        redacted_signal = SignalEnvelope(
            signal_id=signal.signal_id,
            tenant_id=signal.tenant_id,
            environment=signal.environment,
            producer_id=signal.producer_id,
            actor_id=signal.actor_id,
            signal_kind=signal.signal_kind,
            signal_type=signal.signal_type,
            occurred_at=signal.occurred_at,
            ingested_at=signal.ingested_at,
            trace_id=signal.trace_id,
            span_id=signal.span_id,
            correlation_id=signal.correlation_id,
            resource=signal.resource,
            payload=redacted_payload,
            schema_version=signal.schema_version,
            sequence_no=signal.sequence_no
        )

        return redacted_signal, redacted_fields

    def check_residency(self, signal: SignalEnvelope) -> tuple[bool, Optional[str]]:
        """
        Check data residency requirements per F10.

        Args:
            signal: SignalEnvelope to check

        Returns:
            (complies, error_message) tuple
        """
        # Get classification
        classification = self.data_governance.get_classification(signal.tenant_id, signal.signal_type)

        if classification:
            # Check if classification requires specific residency
            # For now, assume all signals can be processed (implementation can add residency checks)
            # In production, this would check against residency rules
            pass

        return True, None

    def validate_governance(self, signal: SignalEnvelope) -> tuple[bool, Optional[str], List[str]]:
        """
        Validate signal against governance rules per F10.

        Args:
            signal: SignalEnvelope to validate

        Returns:
            (is_valid, error_message, violations) tuple
        """
        violations = []

        # Check for disallowed fields
        disallowed_fields = self.data_governance.get_disallowed_fields(
            signal.tenant_id,
            signal.producer_id,
            signal.signal_type
        )

        for field in disallowed_fields:
            if field in signal.payload:
                violations.append(f"Disallowed field present: {field}")

        # Check classification
        classification = self.data_governance.get_classification(signal.tenant_id, signal.signal_type)
        if classification and 'classification' in signal.payload:
            signal_classification = signal.payload.get('classification', {}).get('sensitivity')
            if signal_classification and signal_classification != classification:
                violations.append(f"Classification mismatch: {signal_classification} != {classification}")

        if violations:
            return False, f"Governance violations: {', '.join(violations)}", violations

        return True, None, []

