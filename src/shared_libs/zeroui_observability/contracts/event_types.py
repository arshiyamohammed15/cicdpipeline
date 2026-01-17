"""
Event type registry for ZeroUI Observability Layer.

Defines the 12 minimum required event types per PRD Section 4.2.
"""

from enum import Enum
from typing import Optional


class EventType(str, Enum):
    """
    Enumeration of all required event types for ZeroUI Observability Layer.

    Per PRD Section 4.2, these 12 event types are the minimum required set
    to support monitoring, evaluation, and false-positive handling.
    """

    # Error and failure tracking
    ERROR_CAPTURED = "error.captured.v1"
    FAILURE_REPLAY_BUNDLE = "failure.replay.bundle.v1"

    # Prompt and validation
    PROMPT_VALIDATION_RESULT = "prompt.validation.result.v1"

    # Memory management
    MEMORY_ACCESS = "memory.access.v1"
    MEMORY_VALIDATION = "memory.validation.v1"

    # Evaluation and quality
    EVALUATION_RESULT = "evaluation.result.v1"
    USER_FLAG = "user.flag.v1"

    # Bias detection
    BIAS_SCAN_RESULT = "bias.scan.result.v1"

    # Retrieval evaluation
    RETRIEVAL_EVAL = "retrieval.eval.v1"

    # Performance
    PERF_SAMPLE = "perf.sample.v1"

    # Privacy and security
    PRIVACY_AUDIT = "privacy.audit.v1"

    # Alerting and noise control
    ALERT_NOISE_CONTROL = "alert.noise_control.v1"

    # Forecasting (Phase 3)
    FORECAST_SIGNAL = "forecast.signal.v1"

    @classmethod
    def all_event_types(cls) -> list[str]:
        """
        Get all event type identifiers as strings.

        Returns:
            List of all event type identifiers
        """
        return [event_type.value for event_type in cls]

    @classmethod
    def is_valid_event_type(cls, event_type: str) -> bool:
        """
        Check if an event type string is valid.

        Args:
            event_type: Event type string to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            cls(event_type)
            return True
        except ValueError:
            return False


def get_event_type(event_type: str) -> Optional[EventType]:
    """
    Get EventType enum from string, or None if invalid.

    Args:
        event_type: Event type string

    Returns:
        EventType enum or None if invalid
    """
    try:
        return EventType(event_type)
    except ValueError:
        return None
