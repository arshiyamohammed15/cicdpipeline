"""
Schema Guard processor for ZeroUI Observability Layer.

Validates event envelope (zero_ui.obsv.event.v1) and payload schemas.
Rejects invalid events with reason_code and emits validation metrics.
"""

import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import jsonschema
    from jsonschema import ValidationError, validate
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception  # type: ignore

from ....contracts.event_types import EventType, get_event_type
from ....contracts.payloads.schema_loader import load_schema, validate_payload
from ..validation_metrics import ValidationMetrics

logger = logging.getLogger(__name__)


class RejectionReason(str, Enum):
    """Rejection reason codes for invalid events."""

    INVALID_ENVELOPE = "invalid_envelope"
    INVALID_PAYLOAD = "invalid_payload"
    MISSING_EVENT_TYPE = "missing_event_type"
    UNKNOWN_EVENT_TYPE = "unknown_event_type"
    SCHEMA_LOAD_ERROR = "schema_load_error"
    VALIDATION_ERROR = "validation_error"


@dataclass
class ValidationResult:
    """Result of schema validation."""

    is_valid: bool
    reason_code: Optional[str] = None
    error_message: Optional[str] = None
    validation_duration_ms: float = 0.0


class SchemaGuardProcessor:
    """
    Schema Guard processor for OpenTelemetry Collector.

    Validates:
    - Event envelope schema (zero_ui.obsv.event.v1)
    - Payload schemas (12 event types)

    Emits metrics for validation results and rejections.
    """

    def __init__(
        self,
        enabled: bool = True,
        schema_dir: Optional[str] = None,
        reject_on_invalid: bool = True,
        sample_invalid_events: bool = False,
        sample_rate: float = 0.1,
    ):
        """
        Initialize Schema Guard processor.

        Args:
            enabled: Whether validation is enabled
            schema_dir: Directory containing schemas (optional, uses default)
            reject_on_invalid: Reject invalid events (default: True)
            sample_invalid_events: Sample invalid events for debugging (default: False)
            sample_rate: Sample rate for invalid events (default: 0.1)
        """
        self._enabled = enabled
        self._reject_on_invalid = reject_on_invalid
        self._sample_invalid_events = sample_invalid_events
        self._sample_rate = sample_rate
        self._metrics = ValidationMetrics()

        # Load envelope schema
        if JSONSCHEMA_AVAILABLE:
            self._envelope_schema = self._load_envelope_schema()
        else:
            logger.warning("jsonschema not available, schema validation disabled")
            self._envelope_schema = None

    def _load_envelope_schema(self) -> Optional[Dict[str, Any]]:
        """Load envelope schema from Phase 0 contracts."""
        try:
            from pathlib import Path
            schema_path = Path(__file__).parent.parent.parent.parent.parent / "contracts" / "envelope_schema.json"
            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load envelope schema: {e}")
        return None

    def validate_event(self, event: Dict[str, Any]) -> ValidationResult:
        """
        Validate event against envelope and payload schemas.

        Args:
            event: Event dictionary (zero_ui.obsv.event.v1 envelope)

        Returns:
            ValidationResult with validation outcome
        """
        if not self._enabled:
            return ValidationResult(is_valid=True)

        start_time = time.perf_counter()

        try:
            # Step 1: Validate envelope schema
            if self._envelope_schema:
                try:
                    validate(instance=event, schema=self._envelope_schema)
                except ValidationError as e:
                    self._metrics.record_rejection(RejectionReason.INVALID_ENVELOPE.value)
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    return ValidationResult(
                        is_valid=False,
                        reason_code=RejectionReason.INVALID_ENVELOPE.value,
                        error_message=f"Envelope validation failed: {e.message}",
                        validation_duration_ms=elapsed_ms,
                    )

            # Step 2: Extract event type
            event_type = event.get("event_type")
            if not event_type:
                self._metrics.record_rejection(RejectionReason.MISSING_EVENT_TYPE.value)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return ValidationResult(
                    is_valid=False,
                    reason_code=RejectionReason.MISSING_EVENT_TYPE.value,
                    error_message="Missing event_type field",
                    validation_duration_ms=elapsed_ms,
                )

            # Step 3: Validate event type is known
            if not EventType.is_valid_event_type(event_type):
                self._metrics.record_rejection(RejectionReason.UNKNOWN_EVENT_TYPE.value)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return ValidationResult(
                    is_valid=False,
                    reason_code=RejectionReason.UNKNOWN_EVENT_TYPE.value,
                    error_message=f"Unknown event type: {event_type}",
                    validation_duration_ms=elapsed_ms,
                )

            # Step 4: Validate payload schema
            payload = event.get("payload", {})
            is_valid, error = validate_payload(event_type, payload)
            if not is_valid:
                self._metrics.record_rejection(RejectionReason.INVALID_PAYLOAD.value)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return ValidationResult(
                    is_valid=False,
                    reason_code=RejectionReason.INVALID_PAYLOAD.value,
                    error_message=error or "Payload validation failed",
                    validation_duration_ms=elapsed_ms,
                )

            # Validation passed
            self._metrics.record_validation(True, (time.perf_counter() - start_time) * 1000)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ValidationResult(
                is_valid=True,
                validation_duration_ms=elapsed_ms,
            )

        except Exception as e:
            logger.error(f"Schema validation error: {e}", exc_info=True)
            self._metrics.record_rejection(RejectionReason.VALIDATION_ERROR.value)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ValidationResult(
                is_valid=False,
                reason_code=RejectionReason.VALIDATION_ERROR.value,
                error_message=f"Validation error: {str(e)}",
                validation_duration_ms=elapsed_ms,
            )

    def process_log_record(self, log_record: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Process OTLP log record (event).

        Args:
            log_record: OTLP log record containing event data

        Returns:
            Tuple of (should_accept, rejection_reason)
        """
        if not self._enabled:
            return True, None

        # Extract event from log record body
        body = log_record.get("body", {})
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return False, "Invalid JSON in log body"

        # Validate event
        result = self.validate_event(body)

        if result.is_valid:
            return True, None

        # Invalid event - check if we should reject or sample
        if self._reject_on_invalid:
            return False, result.reason_code

        # Sample invalid events if enabled
        if self._sample_invalid_events:
            import random
            if random.random() < self._sample_rate:
                logger.warning(f"Sampled invalid event: {result.reason_code} - {result.error_message}")
                return True, None  # Accept for sampling

        return False, result.reason_code

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get validation metrics.

        Returns:
            Dictionary of metrics
        """
        return self._metrics.get_metrics()

