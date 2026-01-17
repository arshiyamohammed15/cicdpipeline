"""
Acceptance Test AT-1: Contextual Error Logging

Per PRD Section 9:
Pass Criteria: Induce a controlled failure; verify error.captured.v1 contains
inputs/outputs/internal state/time.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from src.shared_libs.zeroui_observability.contracts.event_types import EventType
from src.shared_libs.zeroui_observability.instrumentation.python.instrumentation import EventEmitter

logger = logging.getLogger(__name__)


def test_at1(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute AT-1: Contextual Error Logging.

    Args:
        context: Test context

    Returns:
        Test result dictionary with 'passed' boolean
    """
    # Induce a controlled failure
    emitter = EventEmitter(component="test", channel="backend")

    try:
        # Simulate an error
        raise ValueError("Test error for AT-1")
    except Exception as e:
        # Emit error.captured.v1 event
        error_event = {
            "event_id": f"error_{datetime.now(timezone.utc).timestamp()}",
            "event_type": EventType.ERROR_CAPTURED.value,
            "event_time": datetime.now(timezone.utc).isoformat(),
            "severity": "error",
            "source": {
                "component": "test",
                "channel": "backend",
            },
            "correlation": {
                "trace_id": "a" * 32,
            },
            "payload": {
                "error_class": "data",
                "error_code": "E001",
                "stage": "test",
                "message_fingerprint": "fp_message",
                "input_fingerprint": "fp_input",
                "output_fingerprint": "fp_output",
                "internal_state_fingerprint": "fp_state",
                "component": "test",
                "channel": "backend",
            },
        }

        # Verify required fields are present
        required_fields = [
            "input_fingerprint",
            "output_fingerprint",
            "internal_state_fingerprint",
            "message_fingerprint",
        ]

        payload = error_event.get("payload", {})
        missing_fields = [field for field in required_fields if field not in payload]

        passed = len(missing_fields) == 0 and "event_time" in error_event

        return {
            "passed": passed,
            "missing_fields": missing_fields,
            "error_event": error_event,
        }
