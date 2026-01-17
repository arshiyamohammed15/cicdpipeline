"""
Tests for SLI calculator (OBS-08).

Tests all 7 SLIs with fixtures and edge cases.
"""

import unittest
from datetime import datetime

from ..sli.sli_calculator import SLICalculator, SLIResult
from ..contracts.event_types import EventType


class TestSLICalculator(unittest.TestCase):
    """Test SLI calculator."""

    def setUp(self):
        """Set up SLI calculator."""
        self.calculator = SLICalculator()

    def test_compute_sli_a_success_rate(self):
        """Test SLI-A: End-to-End Decision Success Rate."""
        traces = [
            {
                "parent_span_id": None,  # Root span
                "attributes": {
                    "component": "backend",
                    "channel": "backend",
                    "run_outcome": "success",
                },
            },
            {
                "parent_span_id": None,
                "attributes": {
                    "component": "backend",
                    "channel": "backend",
                    "run_outcome": "success",
                },
            },
            {
                "parent_span_id": None,
                "attributes": {
                    "component": "backend",
                    "channel": "backend",
                    "run_outcome": "failure",
                },
            },
        ]
        results = self.calculator.compute_sli_a(traces)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].sli_id, "SLI-A")
        self.assertEqual(results[0].value, 2.0 / 3.0)  # 2 success / 3 total
        self.assertEqual(results[0].numerator, 2.0)
        self.assertEqual(results[0].denominator, 3.0)

    def test_compute_sli_a_zero_traffic(self):
        """Test SLI-A with zero traffic."""
        results = self.calculator.compute_sli_a([])
        self.assertEqual(len(results), 0)  # No groups, no results

    def test_compute_sli_b_latency(self):
        """Test SLI-B: End-to-End Latency."""
        traces = [
            {
                "parent_span_id": None,
                "attributes": {"component": "backend", "channel": "backend"},
                "start_time": 1000.0,
                "end_time": 1150.0,  # 150ms
            },
            {
                "parent_span_id": None,
                "attributes": {"component": "backend", "channel": "backend"},
                "start_time": 2000.0,
                "end_time": 2200.0,  # 200ms
            },
        ]
        perf_samples = [
            {
                "event_type": EventType.PERF_SAMPLE.value,
                "payload": {
                    "operation": "decision",
                    "latency_ms": 100,
                    "component": "backend",
                    "channel": "backend",
                },
            },
        ]
        results = self.calculator.compute_sli_b(traces, perf_samples)
        self.assertGreater(len(results), 0)
        result = results[0]
        self.assertEqual(result.sli_id, "SLI-B")
        self.assertIn("p50", result.metadata)
        self.assertIn("p95", result.metadata)
        self.assertIn("p99", result.metadata)

    def test_compute_sli_c_error_coverage(self):
        """Test SLI-C: Error Capture Coverage."""
        error_events = [
            {
                "event_type": EventType.ERROR_CAPTURED.value,
                "payload": {
                    "error_class": "architecture",
                    "error_code": "ERR_001",
                    "stage": "retrieval",
                    "message_fingerprint": "a3f5e8b2c1d4f6a7e9b1c3d5f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5",
                    "input_fingerprint": "b4g6f9c2d5e7a8f0b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6",
                    "output_fingerprint": "c5h7g0d3e6f8b9g1c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5",
                    "internal_state_fingerprint": "d6i8h1e4f7g9c0h2d4e6f8g0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8",
                    "component": "backend",
                    "channel": "backend",
                },
            },
        ]
        error_traces = [
            {
                "parent_span_id": None,
                "status": "error",
                "attributes": {
                    "component": "backend",
                    "channel": "backend",
                    "error_class": "architecture",
                },
            },
            {
                "parent_span_id": None,
                "status": "error",
                "attributes": {
                    "component": "backend",
                    "channel": "backend",
                    "error_class": "architecture",
                },
            },
        ]
        results = self.calculator.compute_sli_c(error_events, error_traces)
        self.assertGreater(len(results), 0)
        result = results[0]
        self.assertEqual(result.sli_id, "SLI-C")
        self.assertEqual(result.value, 1.0 / 2.0)  # 1 captured / 2 total errors
        self.assertEqual(result.numerator, 1.0)
        self.assertEqual(result.denominator, 2.0)

    def test_compute_sli_d_prompt_validation(self):
        """Test SLI-D: Prompt Validation Pass Rate."""
        events = [
            {
                "event_type": EventType.PROMPT_VALIDATION_RESULT.value,
                "payload": {
                    "prompt_id": "prompt_001",
                    "prompt_version": "v1.0.0",
                    "test_suite_id": "suite_001",
                    "test_case_id": "case_001",
                    "status": "pass",
                },
            },
            {
                "event_type": EventType.PROMPT_VALIDATION_RESULT.value,
                "payload": {
                    "prompt_id": "prompt_001",
                    "prompt_version": "v1.0.0",
                    "test_suite_id": "suite_001",
                    "test_case_id": "case_002",
                    "status": "pass",
                },
            },
            {
                "event_type": EventType.PROMPT_VALIDATION_RESULT.value,
                "payload": {
                    "prompt_id": "prompt_001",
                    "prompt_version": "v1.0.0",
                    "test_suite_id": "suite_001",
                    "test_case_id": "case_003",
                    "status": "fail",
                },
            },
        ]
        results = self.calculator.compute_sli_d(events)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.sli_id, "SLI-D")
        self.assertEqual(result.value, 2.0 / 3.0)  # 2 pass / 3 total
        self.assertEqual(result.numerator, 2.0)
        self.assertEqual(result.denominator, 3.0)

    def test_compute_sli_e_retrieval_compliance(self):
        """Test SLI-E: Retrieval Compliance."""
        events = [
            {
                "event_type": EventType.RETRIEVAL_EVAL.value,
                "payload": {
                    "retrieval_run_id": "run_001",
                    "corpus_id": "corpus_001",
                    "query_fingerprint": "a3f5e8b2c1d4f6a7e9b1c3d5f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5",
                    "top_k": 5,
                    "component": "backend",
                    "channel": "backend",
                    "relevance_compliant": True,
                    "timeliness_compliant": True,
                },
            },
            {
                "event_type": EventType.RETRIEVAL_EVAL.value,
                "payload": {
                    "retrieval_run_id": "run_002",
                    "corpus_id": "corpus_001",
                    "query_fingerprint": "b4g6f9c2d5e7a8f0b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6",
                    "top_k": 5,
                    "component": "backend",
                    "channel": "backend",
                    "relevance_compliant": True,
                    "timeliness_compliant": False,  # Not compliant
                },
            },
        ]
        results = self.calculator.compute_sli_e(events)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.sli_id, "SLI-E")
        self.assertEqual(result.value, 1.0 / 2.0)  # 1 compliant / 2 total
        self.assertEqual(result.numerator, 1.0)
        self.assertEqual(result.denominator, 2.0)

    def test_compute_sli_f_evaluation_quality(self):
        """Test SLI-F: Evaluation Quality Signal."""
        evaluation_events = [
            {
                "event_type": EventType.EVALUATION_RESULT.value,
                "payload": {
                    "evaluation_run_id": "run_001",
                    "eval_suite_id": "suite_001",
                    "method": "automated",
                    "component": "backend",
                    "channel": "backend",
                    "metrics": [
                        {"metric_name": "score", "metric_value": 0.85},
                        {"metric_name": "accuracy", "metric_value": 0.90},
                    ],
                },
            },
        ]
        user_flag_events = [
            {
                "event_type": EventType.USER_FLAG.value,
                "payload": {
                    "flag_type": "factual_incorrect",
                    "severity": "high",
                    "component": "backend",
                    "channel": "backend",
                    "ui_surface": "ide",
                },
            },
        ]
        results = self.calculator.compute_sli_f(evaluation_events, user_flag_events)
        self.assertGreater(len(results), 0)
        result = results[0]
        self.assertEqual(result.sli_id, "SLI-F")
        self.assertIn("score_distribution", result.metadata)
        self.assertIn("user_flag_rate", result.metadata)

    def test_compute_sli_g_false_positive_rate(self):
        """Test SLI-G: False Positive Rate."""
        events = [
            {
                "event_type": EventType.ALERT_NOISE_CONTROL.value,
                "payload": {
                    "alert_id": "alert_001",
                    "alert_fingerprint": "fp1",
                    "decision": "allow",
                    "window": "5m",
                    "component": "alerting",
                },
                "metadata": {
                    "validation_outcome": "false_positive",
                },
            },
            {
                "event_type": EventType.ALERT_NOISE_CONTROL.value,
                "payload": {
                    "alert_id": "alert_002",
                    "alert_fingerprint": "fp1",  # Same fingerprint to group together
                    "decision": "allow",
                    "window": "5m",
                    "component": "alerting",
                },
                "metadata": {
                    "validation_outcome": "true_positive",
                },
            },
        ]
        results = self.calculator.compute_sli_g(events)
        self.assertGreater(len(results), 0)
        result = results[0]
        self.assertEqual(result.sli_id, "SLI-G")
        self.assertEqual(result.value, 1.0 / 2.0)  # 1 false_positive / 2 total_positive
        self.assertEqual(result.numerator, 1.0)
        self.assertEqual(result.denominator, 2.0)

    def test_percentile_calculation(self):
        """Test percentile calculation helper."""
        data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        p50 = self.calculator._percentile(data, 50)
        p95 = self.calculator._percentile(data, 95)
        p99 = self.calculator._percentile(data, 99)

        # For 10 items, p50 is at index 5 (60), p95 at index 9 (100), p99 at index 9 (100)
        self.assertEqual(p50, 60.0)
        self.assertEqual(p95, 100.0)
        self.assertEqual(p99, 100.0)


if __name__ == "__main__":
    unittest.main()
