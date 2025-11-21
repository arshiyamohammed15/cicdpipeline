"""
Validation engine for Signal Ingestion & Normalization (SIN) Module.

What: Validation & Schema Enforcement engine per PRD F4
Why: Ensure incoming signals conform to schemas and governance rules
Reads/Writes: Signal validation (no file I/O)
Contracts: PRD §4.4 (F4)
Risks: Validation failures must be handled gracefully, recoverable errors should be coerced
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

from .models import SignalEnvelope, ErrorCode, CoercionWarning
from .models import ValidationError as ModelValidationError
from .producer_registry import ProducerRegistry
from .governance import GovernanceEnforcer
from .dependencies import MockM34SchemaRegistry

logger = logging.getLogger(__name__)


class ValidationEngineError(Exception):
    """Exception raised by validation engine."""
    pass


class ValidationEngine:
    """
    Validation and schema enforcement engine per F4.

    Per PRD F4:
    - Structural validation against SignalEnvelope schema
    - Type/value validation (units, enums, ranges)
    - Governance validation (disallowed fields, classification)
    - Tenant/producer validation
    - Recoverable error coercion (unit conversion)
    - Non-recoverable error routing to DLQ
    """

    def __init__(self, producer_registry: ProducerRegistry, governance_enforcer: GovernanceEnforcer,
                 schema_registry: Optional[MockM34SchemaRegistry] = None):
        """
        Initialize validation engine.

        Args:
            producer_registry: Producer registry
            governance_enforcer: Governance enforcer
            schema_registry: Schema registry
        """
        self.producer_registry = producer_registry
        self.governance_enforcer = governance_enforcer
        self.schema_registry = schema_registry or MockM34SchemaRegistry()

    def validate_structure(self, signal: SignalEnvelope) -> tuple[bool, Optional[ModelValidationError]]:
        """
        Validate signal structure against SignalEnvelope schema per F4.

        Args:
            signal: SignalEnvelope to validate

        Returns:
            (is_valid, validation_error) tuple
        """
        # Check required fields
        if not signal.signal_id:
            return False, ModelValidationError(
                error_code=ErrorCode.SCHEMA_VIOLATION,
                error_message="signal_id is required",
                field_path="signal_id"
            )

        if not signal.tenant_id:
            return False, ModelValidationError(
                error_code=ErrorCode.SCHEMA_VIOLATION,
                error_message="tenant_id is required",
                field_path="tenant_id"
            )

        if not signal.producer_id:
            return False, ModelValidationError(
                error_code=ErrorCode.SCHEMA_VIOLATION,
                error_message="producer_id is required",
                field_path="producer_id"
            )

        if not signal.signal_type:
            return False, ModelValidationError(
                error_code=ErrorCode.SCHEMA_VIOLATION,
                error_message="signal_type is required",
                field_path="signal_type"
            )

        if not signal.payload:
            return False, ModelValidationError(
                error_code=ErrorCode.SCHEMA_VIOLATION,
                error_message="payload is required",
                field_path="payload"
            )

        return True, None

    def validate_producer(self, signal: SignalEnvelope) -> tuple[bool, Optional[ModelValidationError]]:
        """
        Validate producer registration and signal type allowance per F4.

        Args:
            signal: SignalEnvelope to validate

        Returns:
            (is_valid, validation_error) tuple
        """
        # Check producer is registered
        producer = self.producer_registry.get_producer(signal.producer_id)
        if not producer:
            return False, ModelValidationError(
                error_code=ErrorCode.PRODUCER_NOT_REGISTERED,
                error_message=f"Producer {signal.producer_id} is not registered",
                field_path="producer_id"
            )

        # Check signal type is allowed
        if not self.producer_registry.is_signal_type_allowed(
            signal.producer_id,
            signal.signal_kind,
            signal.signal_type
        ):
            return False, ModelValidationError(
                error_code=ErrorCode.SIGNAL_TYPE_NOT_ALLOWED,
                error_message=f"Signal type {signal.signal_type} not allowed for producer {signal.producer_id}",
                field_path="signal_type"
            )

        return True, None

    def validate_contract(self, signal: SignalEnvelope) -> tuple[bool, Optional[ModelValidationError]]:
        """
        Validate signal against data contract per F4.

        Args:
            signal: SignalEnvelope to validate

        Returns:
            (is_valid, validation_error) tuple
        """
        is_valid, error_message = self.producer_registry.validate_signal_contract(signal)
        if not is_valid:
            return False, ModelValidationError(
                error_code=ErrorCode.SCHEMA_VIOLATION,
                error_message=error_message or "Contract validation failed",
                field_path="payload"
            )

        return True, None

    def validate_governance(self, signal: SignalEnvelope) -> tuple[bool, Optional[ModelValidationError], List[str]]:
        """
        Validate signal against governance rules per F4.

        Args:
            signal: SignalEnvelope to validate

        Returns:
            (is_valid, validation_error, violations) tuple
        """
        is_valid, error_message, violations = self.governance_enforcer.validate_governance(signal)
        if not is_valid:
            return False, ModelValidationError(
                error_code=ErrorCode.GOVERNANCE_VIOLATION,
                error_message=error_message or "Governance validation failed",
                field_path="payload",
                details={'violations': violations}
            ), violations

        return True, None, []

    def validate_type_and_value(self, signal: SignalEnvelope) -> tuple[bool, Optional[ModelValidationError], List[CoercionWarning]]:
        """
        Validate type and value constraints per F4 (with recoverable coercion).

        Args:
            signal: SignalEnvelope to validate

        Returns:
            (is_valid, validation_error, coercion_warnings) tuple
        """
        warnings = []
        contract_version = self.producer_registry.get_contract_version(signal.producer_id, signal.signal_type)
        if not contract_version:
            return True, None, warnings  # No contract to validate against

        contract = self.producer_registry.get_contract(signal.signal_type, contract_version)
        if not contract:
            return True, None, warnings  # No contract to validate against

        # Validate enum values
        if contract.enum_values:
            for field, allowed_values in contract.enum_values.items():
                if field in signal.payload:
                    value = signal.payload[field]
                    if value not in allowed_values:
                        return False, ModelValidationError(
                            error_code=ErrorCode.SCHEMA_VIOLATION,
                            error_message=f"Field '{field}' value '{value}' not in allowed enum values: {allowed_values}",
                            field_path=f"payload.{field}"
                        ), warnings

        # Validate value ranges
        if contract.allowed_value_ranges:
            for field, range_spec in contract.allowed_value_ranges.items():
                if field in signal.payload:
                    value = signal.payload[field]
                    if isinstance(value, (int, float)):
                        min_val = range_spec.get('min')
                        max_val = range_spec.get('max')
                        if min_val is not None and value < min_val:
                            return False, ModelValidationError(
                                error_code=ErrorCode.SCHEMA_VIOLATION,
                                error_message=f"Field '{field}' value {value} < min {min_val}",
                                field_path=f"payload.{field}"
                            ), warnings
                        if max_val is not None and value > max_val:
                            return False, ModelValidationError(
                                error_code=ErrorCode.SCHEMA_VIOLATION,
                                error_message=f"Field '{field}' value {value} > max {max_val}",
                                field_path=f"payload.{field}"
                            ), warnings

        # Validate units (recoverable - can be coerced)
        if contract.allowed_units:
            for field, allowed_units in contract.allowed_units.items():
                if field in signal.payload:
                    unit_field = f"{field}_unit"
                    if unit_field in signal.payload:
                        unit = signal.payload[unit_field]
                        if unit not in allowed_units:
                            # This is a recoverable error - we can try to convert
                            # For now, just warn
                            warnings.append(CoercionWarning(
                                field_path=f"payload.{unit_field}",
                                original_value=unit,
                                coerced_value=allowed_units[0] if allowed_units else unit,
                                warning_message=f"Unit '{unit}' not in allowed units {allowed_units}, may be coerced"
                            ))

        return True, None, warnings

    def validate(self, signal: SignalEnvelope) -> tuple[bool, Optional[ModelValidationError], List[CoercionWarning]]:
        """
        Perform complete validation per F4.

        Args:
            signal: SignalEnvelope to validate

        Returns:
            (is_valid, validation_error, coercion_warnings) tuple
        """
        warnings = []

        # Structural validation
        is_valid, error = self.validate_structure(signal)
        if not is_valid:
            return False, error, warnings

        # Producer validation
        is_valid, error = self.validate_producer(signal)
        if not is_valid:
            return False, error, warnings

        # Contract validation
        is_valid, error = self.validate_contract(signal)
        if not is_valid:
            return False, error, warnings

        # Type and value validation (with coercion warnings)
        is_valid, error, coercion_warnings = self.validate_type_and_value(signal)
        warnings.extend(coercion_warnings)
        if not is_valid:
            return False, error, warnings

        # Governance validation
        is_valid, error, violations = self.validate_governance(signal)
        if not is_valid:
            return False, error, warnings

        return True, None, warnings

