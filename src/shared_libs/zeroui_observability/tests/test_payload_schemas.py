"""
Tests for payload schemas (OBS-01).

Validates all 12 event payload schemas.
"""

import json
import unittest
from pathlib import Path

try:
    import jsonschema
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception  # type: ignore

from ..contracts.payloads.schema_loader import load_schema, validate_payload

# Schema directory
_SCHEMA_DIR = Path(__file__).parent.parent / "contracts" / "payloads"
_FIXTURES_DIR = _SCHEMA_DIR / "fixtures" / "valid"


class TestPayloadSchemas(unittest.TestCase):
    """Test payload schema validation."""

    @classmethod
    def setUpClass(cls):
        """Load all schemas."""
        if not JSONSCHEMA_AVAILABLE:
            raise unittest.SkipTest("jsonschema not available")

        cls.schemas = {}
        event_types = [
            "error.captured.v1",
            "prompt.validation.result.v1",
            "memory.access.v1",
            "memory.validation.v1",
            "evaluation.result.v1",
            "user.flag.v1",
            "bias.scan.result.v1",
            "retrieval.eval.v1",
            "failure.replay.bundle.v1",
            "perf.sample.v1",
            "privacy.audit.v1",
            "alert.noise_control.v1",
        ]
        for event_type in event_types:
            schema = load_schema(event_type)
            if schema:
                cls.schemas[event_type] = schema

    def test_all_schemas_load(self):
        """Test all 12 schemas can be loaded."""
        self.assertEqual(len(self.schemas), 12)

    def test_error_captured_v1_valid(self):
        """Test valid error.captured.v1 payload."""
        fixture_path = _FIXTURES_DIR / "error_captured_v1.json"
        if fixture_path.exists():
            with open(fixture_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            is_valid, error = validate_payload("error.captured.v1", payload)
            self.assertTrue(is_valid, f"Validation failed: {error}")

    def test_error_captured_v1_missing_required(self):
        """Test error.captured.v1 with missing required fields."""
        payload = {
            "error_class": "architecture",
            "error_code": "ERR_001"
            # Missing: stage, message_fingerprint, input_fingerprint, etc.
        }
        is_valid, error = validate_payload("error.captured.v1", payload)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_prompt_validation_result_v1_valid(self):
        """Test valid prompt.validation.result.v1 payload."""
        payload = {
            "prompt_id": "prompt_001",
            "prompt_version": "v1.2.3",
            "test_suite_id": "suite_001",
            "test_case_id": "case_001",
            "status": "pass"
        }
        is_valid, error = validate_payload("prompt.validation.result.v1", payload)
        self.assertTrue(is_valid, f"Validation failed: {error}")

    def test_memory_access_v1_valid(self):
        """Test valid memory.access.v1 payload."""
        payload = {
            "memory_store_id": "store_001",
            "operation": "read",
            "key_fingerprint": "a3f5e8b2c1d4f6a7e9b1c3d5f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5",
            "result": "hit",
            "component": "edge_agent",
            "channel": "ide"
        }
        is_valid, error = validate_payload("memory.access.v1", payload)
        self.assertTrue(is_valid, f"Validation failed: {error}")

    def test_evaluation_result_v1_valid(self):
        """Test valid evaluation.result.v1 payload."""
        payload = {
            "evaluation_run_id": "run_001",
            "eval_suite_id": "suite_001",
            "method": "automated",
            "component": "backend",
            "channel": "backend",
            "metrics": [
                {
                    "metric_name": "accuracy",
                    "metric_value": 0.95
                }
            ]
        }
        is_valid, error = validate_payload("evaluation.result.v1", payload)
        self.assertTrue(is_valid, f"Validation failed: {error}")

    def test_evaluation_result_v1_invalid_metrics(self):
        """Test evaluation.result.v1 with invalid metrics structure."""
        payload = {
            "evaluation_run_id": "run_001",
            "eval_suite_id": "suite_001",
            "method": "automated",
            "component": "backend",
            "channel": "backend",
            "metrics": [
                {
                    "metric_name": "accuracy"
                    # Missing: metric_value
                }
            ]
        }
        is_valid, error = validate_payload("evaluation.result.v1", payload)
        self.assertFalse(is_valid)

    def test_retrieval_eval_v1_valid(self):
        """Test valid retrieval.eval.v1 payload."""
        payload = {
            "retrieval_run_id": "run_001",
            "corpus_id": "corpus_001",
            "query_fingerprint": "a3f5e8b2c1d4f6a7e9b1c3d5f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5",
            "top_k": 5,
            "component": "backend",
            "channel": "backend",
            "relevance_score": 0.85,
            "timeliness_score": 0.90,
            "relevance_compliant": True,
            "timeliness_compliant": True
        }
        is_valid, error = validate_payload("retrieval.eval.v1", payload)
        self.assertTrue(is_valid, f"Validation failed: {error}")

    def test_failure_replay_bundle_v1_valid(self):
        """Test valid failure.replay.bundle.v1 payload."""
        payload = {
            "replay_id": "replay_001",
            "trigger_event_id": "evt_123",
            "included_event_ids": ["evt_123", "evt_124", "evt_125"],
            "checksum": "a3f5e8b2c1d4f6a7e9b1c3d5f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5",
            "storage_ref": "s3://bucket/path/to/bundle.json"
        }
        is_valid, error = validate_payload("failure.replay.bundle.v1", payload)
        self.assertTrue(is_valid, f"Validation failed: {error}")

    def test_failure_replay_bundle_v1_empty_event_ids(self):
        """Test failure.replay.bundle.v1 with empty included_event_ids fails."""
        payload = {
            "replay_id": "replay_001",
            "trigger_event_id": "evt_123",
            "included_event_ids": [],  # Invalid: minItems=1
            "checksum": "a3f5e8b2c1d4f6a7e9b1c3d5f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5",
            "storage_ref": "s3://bucket/path/to/bundle.json"
        }
        is_valid, error = validate_payload("failure.replay.bundle.v1", payload)
        self.assertFalse(is_valid)

    def test_perf_sample_v1_valid(self):
        """Test valid perf.sample.v1 payload."""
        payload = {
            "operation": "decision",
            "latency_ms": 150,
            "component": "backend",
            "channel": "backend",
            "cache_hit": True,
            "async_path": False,
            "queue_depth": 0
        }
        is_valid, error = validate_payload("perf.sample.v1", payload)
        self.assertTrue(is_valid, f"Validation failed: {error}")

    def test_perf_sample_v1_negative_latency(self):
        """Test perf.sample.v1 with negative latency fails."""
        payload = {
            "operation": "decision",
            "latency_ms": -1,  # Invalid: minimum=0
            "component": "backend",
            "channel": "backend"
        }
        is_valid, error = validate_payload("perf.sample.v1", payload)
        self.assertFalse(is_valid)

    def test_privacy_audit_v1_valid(self):
        """Test valid privacy.audit.v1 payload."""
        payload = {
            "audit_id": "audit_001",
            "operation": "data_access",
            "component": "backend",
            "channel": "backend",
            "encryption_in_transit": True,
            "encryption_at_rest": True,
            "access_control_enforced": True
        }
        is_valid, error = validate_payload("privacy.audit.v1", payload)
        self.assertTrue(is_valid, f"Validation failed: {error}")

    def test_alert_noise_control_v1_valid(self):
        """Test valid alert.noise_control.v1 payload."""
        payload = {
            "alert_id": "alert_001",
            "alert_fingerprint": "a3f5e8b2c1d4f6a7e9b1c3d5f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5",
            "decision": "suppress",
            "window": "5m",
            "component": "alerting"
        }
        is_valid, error = validate_payload("alert.noise_control.v1", payload)
        self.assertTrue(is_valid, f"Validation failed: {error}")


if __name__ == "__main__":
    unittest.main()
