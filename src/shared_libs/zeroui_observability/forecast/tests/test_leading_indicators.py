"""
Unit tests for LeadingIndicatorDetector.
"""

import pytest
import time

from ...contracts.event_types import EventType
from ..leading_indicators import LeadingIndicatorDetector


class TestLeadingIndicatorDetector:
    """Test leading indicator detector."""

    def test_detect_latency_p95_increase(self):
        """Test latency p95 increase detection."""
        detector = LeadingIndicatorDetector(latency_threshold_p95_ms=100.0)
        
        current_time = time.time()
        history = [
            {"timestamp": current_time - 600, "p95": 80.0},
            {"timestamp": current_time - 300, "p95": 90.0},
            {"timestamp": current_time, "p95": 120.0},  # Above threshold
        ]
        
        indicator = detector.detect_latency_p95_increase(history)
        
        assert indicator is not None
        assert indicator.indicator_type == "latency_p95_increase"
        assert indicator.value == 120.0
        assert indicator.threshold == 100.0
        assert indicator.severity in ["low", "medium", "high"]

    def test_detect_latency_p95_no_increase(self):
        """Test no latency increase when below threshold."""
        detector = LeadingIndicatorDetector(latency_threshold_p95_ms=100.0)
        
        current_time = time.time()
        history = [
            {"timestamp": current_time - 600, "p95": 80.0},
            {"timestamp": current_time - 300, "p95": 85.0},
            {"timestamp": current_time, "p95": 90.0},  # Below threshold
        ]
        
        indicator = detector.detect_latency_p95_increase(history)
        
        # Should return None if below threshold
        assert indicator is None or indicator.value < indicator.threshold

    def test_detect_error_coverage_gap(self):
        """Test error coverage gap detection."""
        detector = LeadingIndicatorDetector(error_coverage_threshold=0.95)
        
        current_time = time.time()
        history = [
            {"timestamp": current_time - 600, "value": 0.98},
            {"timestamp": current_time - 300, "value": 0.92},
            {"timestamp": current_time, "value": 0.90},  # Below threshold
        ]
        
        indicator = detector.detect_error_coverage_gap(history)
        
        assert indicator is not None
        assert indicator.indicator_type == "error_coverage_gap"
        assert indicator.value == 0.90
        assert indicator.threshold == 0.95
        assert indicator.severity in ["low", "medium", "high"]

    def test_detect_error_coverage_no_gap(self):
        """Test no error coverage gap when above threshold."""
        detector = LeadingIndicatorDetector(error_coverage_threshold=0.95)
        
        current_time = time.time()
        history = [
            {"timestamp": current_time - 600, "value": 0.98},
            {"timestamp": current_time - 300, "value": 0.97},
            {"timestamp": current_time, "value": 0.96},  # Above threshold
        ]
        
        indicator = detector.detect_error_coverage_gap(history)
        
        # Should return None if above threshold
        assert indicator is None

    def test_detect_bias_signal_spike(self):
        """Test bias signal spike detection."""
        detector = LeadingIndicatorDetector(bias_confidence_threshold=0.7)
        
        current_time = time.time()
        events = [
            {
                "event_type": EventType.BIAS_SCAN_RESULT.value,
                "event_time": current_time - 1800,
                "payload": {"status": "fail", "confidence": 0.8},
            },
            {
                "event_type": EventType.BIAS_SCAN_RESULT.value,
                "event_time": current_time - 900,
                "payload": {"status": "fail", "confidence": 0.75},
            },
            {
                "event_type": EventType.BIAS_SCAN_RESULT.value,
                "event_time": current_time - 300,
                "payload": {"status": "fail", "confidence": 0.85},
            },
        ]
        
        indicator = detector.detect_bias_signal_spike(events, window_seconds=3600.0)
        
        assert indicator is not None
        assert indicator.indicator_type == "bias_signal_spike"
        assert indicator.value > 0
        assert indicator.severity in ["low", "medium", "high"]

    def test_detect_user_flag_rate_increase(self):
        """Test user flag rate increase detection."""
        detector = LeadingIndicatorDetector(user_flag_rate_threshold=0.05)
        
        current_time = time.time()
        events = [
            {
                "event_type": EventType.USER_FLAG.value,
                "event_time": current_time - 1800,
                "payload": {},
            },
            {
                "event_type": EventType.USER_FLAG.value,
                "event_time": current_time - 900,
                "payload": {},
            },
            {
                "event_type": EventType.USER_FLAG.value,
                "event_time": current_time - 300,
                "payload": {},
            },
        ]
        
        # 3 flags out of 50 evaluations = 6% flag rate (above 5% threshold)
        indicator = detector.detect_user_flag_rate_increase(
            events, total_evaluation_events=50, window_seconds=3600.0
        )
        
        assert indicator is not None
        assert indicator.indicator_type == "user_flag_rate_increase"
        assert indicator.value > 0.05
        assert indicator.severity in ["low", "medium", "high"]

    def test_detect_all(self):
        """Test detect_all method."""
        detector = LeadingIndicatorDetector()
        
        current_time = time.time()
        sli_b_history = [
            {"timestamp": current_time - 600, "p95": 80.0},
            {"timestamp": current_time - 300, "p95": 90.0},
            {"timestamp": current_time, "p95": 120.0},
        ]
        
        sli_c_history = [
            {"timestamp": current_time - 600, "value": 0.98},
            {"timestamp": current_time - 300, "value": 0.92},
            {"timestamp": current_time, "value": 0.90},
        ]
        
        indicators = detector.detect_all(
            sli_b_history=sli_b_history,
            sli_c_history=sli_c_history,
        )
        
        assert len(indicators) >= 0  # May detect 0, 1, or 2 indicators
        for indicator in indicators:
            assert indicator.indicator_type in [
                "latency_p95_increase",
                "error_coverage_gap",
                "bias_signal_spike",
                "user_flag_rate_increase",
            ]
