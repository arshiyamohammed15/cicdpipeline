"""
OBS-13: Leading Indicator Detectors.

Detects leading indicators that may signal future SLO breaches:
- Latency p95 increases (SLI-B)
- Error capture coverage gaps (SLI-C)
- Bias signal spikes (from bias.scan.result.v1)
- User flag rate increases (from user.flag.v1)
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...contracts.event_types import EventType

logger = logging.getLogger(__name__)


@dataclass
class LeadingIndicator:
    """Leading indicator detection result."""

    indicator_type: str  # "latency_p95_increase", "error_coverage_gap", "bias_signal_spike", "user_flag_rate_increase"
    severity: str  # "low", "medium", "high"
    trend: str  # "increasing", "decreasing", "stable"
    value: float
    threshold: Optional[float] = None


class LeadingIndicatorDetector:
    """
    Detector for leading indicators of SLO breaches.

    Analyzes SLI time series and event streams to detect early warning signals.
    """

    def __init__(
        self,
        latency_threshold_p95_ms: Optional[float] = None,
        error_coverage_threshold: float = 0.95,  # 95% coverage required
        bias_confidence_threshold: float = 0.7,  # High confidence bias signals
        user_flag_rate_threshold: float = 0.05,  # 5% flag rate
    ):
        """
        Initialize leading indicator detector.

        Args:
            latency_threshold_p95_ms: Threshold for p95 latency (None = auto-detect from baseline)
            error_coverage_threshold: Minimum error capture coverage (0.0 to 1.0)
            bias_confidence_threshold: Minimum confidence for bias signal (0.0 to 1.0)
            user_flag_rate_threshold: Maximum acceptable user flag rate (0.0 to 1.0)
        """
        self.latency_threshold_p95_ms = latency_threshold_p95_ms
        self.error_coverage_threshold = error_coverage_threshold
        self.bias_confidence_threshold = bias_confidence_threshold
        self.user_flag_rate_threshold = user_flag_rate_threshold

    def detect_latency_p95_increase(
        self,
        sli_b_history: List[Dict[str, Any]],  # SLI-B time series
        baseline_p95_ms: Optional[float] = None,
    ) -> Optional[LeadingIndicator]:
        """
        Detect increasing latency p95 trend.

        Args:
            sli_b_history: SLI-B time series [{"timestamp": float, "p95": float}, ...]
            baseline_p95_ms: Baseline p95 latency (None = compute from history)

        Returns:
            LeadingIndicator if detected, None otherwise
        """
        if not sli_b_history or len(sli_b_history) < 2:
            return None

        # Sort by timestamp
        sorted_history = sorted(sli_b_history, key=lambda x: x.get("timestamp", 0.0))

        # Extract p95 values
        p95_values = [h.get("p95", 0.0) for h in sorted_history if "p95" in h]

        if len(p95_values) < 2:
            return None

        # Compute baseline if not provided
        if baseline_p95_ms is None:
            # Use median of first half as baseline
            mid_point = len(p95_values) // 2
            baseline_p95_ms = sorted(p95_values[:mid_point])[len(p95_values[:mid_point]) // 2] if mid_point > 0 else p95_values[0]

        # Use threshold if provided, otherwise use baseline * 1.2 (20% increase)
        threshold = self.latency_threshold_p95_ms or (baseline_p95_ms * 1.2)

        # Current p95
        current_p95 = p95_values[-1]

        # Compute trend (simple: compare recent vs older values)
        recent_values = p95_values[-3:] if len(p95_values) >= 3 else p95_values
        older_values = p95_values[:-3] if len(p95_values) >= 3 else p95_values[:1]

        recent_avg = sum(recent_values) / len(recent_values) if recent_values else 0.0
        older_avg = sum(older_values) / len(older_values) if older_values else 0.0

        # Determine trend
        if recent_avg > older_avg * 1.1:  # 10% increase
            trend = "increasing"
        elif recent_avg < older_avg * 0.9:  # 10% decrease
            trend = "decreasing"
        else:
            trend = "stable"

        # Determine severity
        if current_p95 > threshold * 1.5:  # 50% above threshold
            severity = "high"
        elif current_p95 > threshold * 1.2:  # 20% above threshold
            severity = "medium"
        elif current_p95 > threshold:
            severity = "low"
        else:
            # No indicator if below threshold
            return None

        return LeadingIndicator(
            indicator_type="latency_p95_increase",
            severity=severity,
            trend=trend,
            value=current_p95,
            threshold=threshold,
        )

    def detect_error_coverage_gap(
        self,
        sli_c_history: List[Dict[str, Any]],  # SLI-C time series
    ) -> Optional[LeadingIndicator]:
        """
        Detect error capture coverage gaps.

        Args:
            sli_c_history: SLI-C time series [{"timestamp": float, "value": float}, ...]
                          value is coverage ratio (0.0 to 1.0)

        Returns:
            LeadingIndicator if detected, None otherwise
        """
        if not sli_c_history:
            return None

        # Sort by timestamp
        sorted_history = sorted(sli_c_history, key=lambda x: x.get("timestamp", 0.0))

        # Extract coverage values
        coverage_values = [h.get("value", 1.0) for h in sorted_history if "value" in h]

        if not coverage_values:
            return None

        # Current coverage
        current_coverage = coverage_values[-1]

        # Check if below threshold
        if current_coverage >= self.error_coverage_threshold:
            return None

        # Compute trend
        if len(coverage_values) >= 2:
            recent_avg = sum(coverage_values[-3:]) / len(coverage_values[-3:]) if len(coverage_values) >= 3 else coverage_values[-1]
            older_avg = sum(coverage_values[:-3]) / len(coverage_values[:-3]) if len(coverage_values) >= 3 else coverage_values[0]

            if recent_avg < older_avg * 0.9:  # 10% decrease
                trend = "decreasing"  # Coverage is decreasing (bad)
            elif recent_avg > older_avg * 1.1:  # 10% increase
                trend = "increasing"  # Coverage is increasing (good)
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Determine severity
        gap = self.error_coverage_threshold - current_coverage
        if gap > 0.1:  # >10% gap
            severity = "high"
        elif gap > 0.05:  # >5% gap
            severity = "medium"
        else:
            severity = "low"

        return LeadingIndicator(
            indicator_type="error_coverage_gap",
            severity=severity,
            trend=trend,
            value=current_coverage,
            threshold=self.error_coverage_threshold,
        )

    def detect_bias_signal_spike(
        self,
        bias_events: List[Dict[str, Any]],  # bias.scan.result.v1 events
        window_seconds: float = 3600.0,  # 1 hour window
    ) -> Optional[LeadingIndicator]:
        """
        Detect bias signal spikes.

        Args:
            bias_events: List of bias.scan.result.v1 events
            window_seconds: Time window for spike detection

        Returns:
            LeadingIndicator if detected, None otherwise
        """
        if not bias_events:
            return None

        # Filter to recent events within window
        import time

        current_time = time.time()
        recent_events = [
            e for e in bias_events
            if e.get("event_time") and (current_time - e.get("event_time", 0)) <= window_seconds
        ]

        if not recent_events:
            return None

        # Count high-confidence bias detections
        high_confidence_count = 0
        for event in recent_events:
            if event.get("event_type") != EventType.BIAS_SCAN_RESULT.value:
                continue

            payload = event.get("payload", {})
            confidence = payload.get("confidence", 0.0)
            status = payload.get("status", "pass")

            if status == "fail" and confidence >= self.bias_confidence_threshold:
                high_confidence_count += 1

        # Compute spike rate
        spike_rate = high_confidence_count / window_seconds * 3600.0  # Per hour

        # Threshold: >2 high-confidence bias detections per hour
        threshold = 2.0

        if spike_rate <= threshold:
            return None

        # Determine severity
        if spike_rate > threshold * 3:  # >6 per hour
            severity = "high"
        elif spike_rate > threshold * 2:  # >4 per hour
            severity = "medium"
        else:
            severity = "low"

        return LeadingIndicator(
            indicator_type="bias_signal_spike",
            severity=severity,
            trend="increasing" if spike_rate > threshold else "stable",
            value=spike_rate,
            threshold=threshold,
        )

    def detect_user_flag_rate_increase(
        self,
        user_flag_events: List[Dict[str, Any]],  # user.flag.v1 events
        total_evaluation_events: int,
        window_seconds: float = 3600.0,  # 1 hour window
    ) -> Optional[LeadingIndicator]:
        """
        Detect user flag rate increases.

        Args:
            user_flag_events: List of user.flag.v1 events
            total_evaluation_events: Total number of evaluation events in same window
            window_seconds: Time window for rate computation

        Returns:
            LeadingIndicator if detected, None otherwise
        """
        if not user_flag_events or total_evaluation_events == 0:
            return None

        # Count flags in recent window
        import time

        current_time = time.time()
        recent_flags = [
            e for e in user_flag_events
            if e.get("event_time") and (current_time - e.get("event_time", 0)) <= window_seconds
        ]

        flag_count = len(recent_flags)
        flag_rate = flag_count / total_evaluation_events if total_evaluation_events > 0 else 0.0

        # Check if above threshold
        if flag_rate <= self.user_flag_rate_threshold:
            return None

        # Determine severity
        if flag_rate > self.user_flag_rate_threshold * 3:  # >15%
            severity = "high"
        elif flag_rate > self.user_flag_rate_threshold * 2:  # >10%
            severity = "medium"
        else:
            severity = "low"

        # Compute trend (compare to historical average if available)
        # For now, assume increasing if above threshold
        trend = "increasing"

        return LeadingIndicator(
            indicator_type="user_flag_rate_increase",
            severity=severity,
            trend=trend,
            value=flag_rate,
            threshold=self.user_flag_rate_threshold,
        )

    def detect_all(
        self,
        sli_b_history: Optional[List[Dict[str, Any]]] = None,
        sli_c_history: Optional[List[Dict[str, Any]]] = None,
        bias_events: Optional[List[Dict[str, Any]]] = None,
        user_flag_events: Optional[List[Dict[str, Any]]] = None,
        total_evaluation_events: int = 0,
    ) -> List[LeadingIndicator]:
        """
        Detect all leading indicators.

        Args:
            sli_b_history: SLI-B time series (latency)
            sli_c_history: SLI-C time series (error coverage)
            bias_events: Bias scan result events
            user_flag_events: User flag events
            total_evaluation_events: Total evaluation events for flag rate computation

        Returns:
            List of detected leading indicators
        """
        indicators = []

        # Latency p95 increase
        if sli_b_history:
            indicator = self.detect_latency_p95_increase(sli_b_history)
            if indicator:
                indicators.append(indicator)

        # Error coverage gap
        if sli_c_history:
            indicator = self.detect_error_coverage_gap(sli_c_history)
            if indicator:
                indicators.append(indicator)

        # Bias signal spike
        if bias_events:
            indicator = self.detect_bias_signal_spike(bias_events)
            if indicator:
                indicators.append(indicator)

        # User flag rate increase
        if user_flag_events:
            indicator = self.detect_user_flag_rate_increase(user_flag_events, total_evaluation_events)
            if indicator:
                indicators.append(indicator)

        return indicators
