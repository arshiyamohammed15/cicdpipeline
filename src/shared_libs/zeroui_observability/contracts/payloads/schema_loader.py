"""
Schema loader utility for ZeroUI Observability Layer payload schemas.

Loads and validates JSON schemas for event payloads.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import jsonschema
    from jsonschema import ValidationError, validate
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception  # type: ignore

logger = logging.getLogger(__name__)

# Schema directory
_SCHEMA_DIR = Path(__file__).parent

# Event type to schema file mapping
_EVENT_TYPE_TO_SCHEMA = {
    "error.captured.v1": "error_captured_v1.json",
    "prompt.validation.result.v1": "prompt_validation_result_v1.json",
    "memory.access.v1": "memory_access_v1.json",
    "memory.validation.v1": "memory_validation_v1.json",
    "evaluation.result.v1": "evaluation_result_v1.json",
    "user.flag.v1": "user_flag_v1.json",
    "bias.scan.result.v1": "bias_scan_result_v1.json",
    "retrieval.eval.v1": "retrieval_eval_v1.json",
    "failure.replay.bundle.v1": "failure_replay_bundle_v1.json",
    "perf.sample.v1": "perf_sample_v1.json",
    "privacy.audit.v1": "privacy_audit_v1.json",
    "alert.noise_control.v1": "alert_noise_control_v1.json",
}

# Cache for loaded schemas
_SCHEMA_CACHE: Dict[str, Dict[str, Any]] = {}


def load_schema(event_type: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON schema for an event type.

    Args:
        event_type: Event type identifier (e.g., "error.captured.v1")

    Returns:
        Schema dictionary or None if not found
    """
    if not JSONSCHEMA_AVAILABLE:
        logger.warning("jsonschema not available, schema validation disabled")
        return None

    # Check cache first
    if event_type in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[event_type]

    # Get schema file path
    schema_file = _EVENT_TYPE_TO_SCHEMA.get(event_type)
    if not schema_file:
        logger.error(f"Unknown event type: {event_type}")
        return None

    schema_path = _SCHEMA_DIR / schema_file
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return None

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
            _SCHEMA_CACHE[event_type] = schema
            return schema
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load schema {schema_path}: {e}")
        return None


def validate_payload(event_type: str, payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate payload against event type schema.

    Args:
        event_type: Event type identifier
        payload: Payload dictionary to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not JSONSCHEMA_AVAILABLE:
        logger.warning("jsonschema not available, skipping validation")
        return True, None

    schema = load_schema(event_type)
    if not schema:
        return False, f"Schema not found for event type: {event_type}"

    try:
        validate(instance=payload, schema=schema)
        return True, None
    except ValidationError as e:
        error_msg = f"Validation failed: {e.message} at {'.'.join(str(p) for p in e.path)}"
        return False, error_msg


def get_schema_path(event_type: str) -> Optional[Path]:
    """
    Get file path for an event type schema.

    Args:
        event_type: Event type identifier

    Returns:
        Path to schema file or None if not found
    """
    schema_file = _EVENT_TYPE_TO_SCHEMA.get(event_type)
    if not schema_file:
        return None
    return _SCHEMA_DIR / schema_file
