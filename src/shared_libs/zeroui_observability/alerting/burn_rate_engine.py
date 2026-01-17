"""
OBS-11: Burn-rate Alert Engine (Multi-window) - Ticket Mode.

Evaluates burn rates over configured windows; generates alert events; routes to ticketing stub.
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    from isodate import parse_duration
except ImportError:
    # Fallback for ISO-8601 duration parsing
    import re
    
    def parse_duration(duration_str: str):
        """Simple ISO-8601 duration parser (PT5M -> timedelta)."""
        from datetime import timedelta
        
        # Match PT5M, PT30M, PT2H, etc.
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if not match:
            raise ValueError(f"Invalid ISO-8601 duration: {duration_str}")
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

from .alert_config import AlertConfig

logger = logging.getLogger(__name__)


@dataclass
class BurnRateResult:
    """Result of burn-rate evaluation for a time window."""

    window_name: str  # "short", "mid", "long"
    window_duration_seconds: float
    error_count: int
    total_count: int
    error_rate: float  # error_count / total_count
    burn_rate: float  # error_rate / allowed_error_rate
    allowed_error_rate: float  # from SLO objective
    breach: bool  # True if burn_rate exceeds threshold


@dataclass
class AlertEvaluationResult:
    """Result of alert evaluation."""

    alert_id: str
    should_fire: bool
    alert_type: Optional[str]  # "fast" | "slow" | None
    burn_rate_results: List[BurnRateResult]
    min_traffic_met: bool
    confidence_gate_passed: bool
    reason: Optional[str] = None


class BurnRateAlertEngine:
    """
    Multi-window burn-rate alert engine.
    
    Implements Google SRE Workbook multi-window burn-rate alerting:
    - FAST alert: burn_rate(short) > fast AND burn_rate(long) > fast_confirm
    - SLOW alert: burn_rate(mid) > slow AND burn_rate(long) > slow_confirm
    
    Alerts fire only when both windows breach; low-traffic suppression works.
    """

    def __init__(self, config: AlertConfig):
        """
        Initialize engine with alert config.
        
        Args:
            config: AlertConfig instance
        """
        self.config = config
        self._window_durations = self._parse_window_durations()

    def _parse_window_durations(self) -> Dict[str, float]:
        """Parse ISO-8601 durations to seconds."""
        durations = {}
        for window_name in ["short", "mid", "long"]:
            duration_str = getattr(self.config.windows, window_name)
            try:
                duration = parse_duration(duration_str)
                durations[window_name] = duration.total_seconds()
            except Exception as e:
                logger.error(f"Failed to parse window duration {window_name}={duration_str}: {e}")
                raise ValueError(f"Invalid window duration: {duration_str}") from e
        return durations

    def compute_burn_rate(
        self,
        error_count: int,
        total_count: int,
        slo_objective: float,
    ) -> tuple[float, float]:
        """
        Compute error rate and burn rate.
        
        Args:
            error_count: Number of errors in window
            total_count: Total events in window
            slo_objective: SLO target (e.g., 0.99 for 99%)
            
        Returns:
            Tuple of (error_rate, burn_rate)
        """
        if total_count == 0:
            return 0.0, 0.0

        error_rate = error_count / total_count
        error_budget = 1.0 - slo_objective
        if error_budget <= 0:
            logger.warning(f"Invalid error budget: {error_budget} (SLO objective: {slo_objective})")
            return error_rate, float("inf")

        allowed_error_rate = error_budget
        burn_rate = error_rate / allowed_error_rate if allowed_error_rate > 0 else float("inf")
        return error_rate, burn_rate

    def evaluate_window(
        self,
        window_name: str,
        error_count: int,
        total_count: int,
        threshold: float,
        slo_objective: float,
    ) -> BurnRateResult:
        """
        Evaluate burn rate for a single window.
        
        Args:
            window_name: "short", "mid", or "long"
            error_count: Number of errors in window
            total_count: Total events in window
            threshold: Burn-rate threshold to check against
            slo_objective: SLO target (e.g., 0.99 for 99%)
            
        Returns:
            BurnRateResult
        """
        error_rate, burn_rate = self.compute_burn_rate(error_count, total_count, slo_objective)
        breach = burn_rate > threshold

        return BurnRateResult(
            window_name=window_name,
            window_duration_seconds=self._window_durations[window_name],
            error_count=error_count,
            total_count=total_count,
            error_rate=error_rate,
            burn_rate=burn_rate,
            allowed_error_rate=1.0 - slo_objective,
            breach=breach,
        )

    def evaluate_alert(
        self,
        window_data: Dict[str, Dict[str, int]],
        slo_objective: float,
        confidence: Optional[float] = None,
    ) -> AlertEvaluationResult:
        """
        Evaluate alert condition using multi-window burn-rate logic.
        
        Args:
            window_data: Dict mapping window_name to {"error_count": int, "total_count": int}
                        Expected keys: "short", "mid", "long"
            slo_objective: SLO target (e.g., 0.99 for 99%)
            confidence: Optional confidence score (0.0 to 1.0) for confidence-gated alerts
            
        Returns:
            AlertEvaluationResult
        """
        # Check min traffic gate
        total_events = sum(data.get("total_count", 0) for data in window_data.values())
        min_traffic_met = total_events >= self.config.min_traffic.min_total_events

        if not min_traffic_met:
            return AlertEvaluationResult(
                alert_id=self.config.alert_id,
                should_fire=False,
                alert_type=None,
                burn_rate_results=[],
                min_traffic_met=False,
                confidence_gate_passed=True,
                reason=f"Min traffic not met: {total_events} < {self.config.min_traffic.min_total_events}",
            )

        # Check confidence gate if enabled
        confidence_gate_passed = True
        if self.config.confidence_gate and self.config.confidence_gate.enabled:
            min_confidence = self.config.confidence_gate.min_confidence or 0.0
            if confidence is None or confidence < min_confidence:
                confidence_gate_passed = False
                return AlertEvaluationResult(
                    alert_id=self.config.alert_id,
                    should_fire=False,
                    alert_type=None,
                    burn_rate_results=[],
                    min_traffic_met=True,
                    confidence_gate_passed=False,
                    reason=f"Confidence gate failed: {confidence} < {min_confidence}",
                )

        # Evaluate each window
        burn_rate_results = []
        for window_name in ["short", "mid", "long"]:
            if window_name not in window_data:
                logger.warning(f"Missing window data for {window_name}")
                continue

            data = window_data[window_name]
            error_count = data.get("error_count", 0)
            total_count = data.get("total_count", 0)

            # Determine threshold based on window
            if window_name == "short":
                threshold = self.config.burn_rate.fast
            elif window_name == "mid":
                threshold = self.config.burn_rate.slow
            else:  # long
                # Long window uses confirm thresholds
                threshold = max(
                    self.config.burn_rate.fast_confirm,
                    self.config.burn_rate.slow_confirm,
                )

            result = self.evaluate_window(
                window_name=window_name,
                error_count=error_count,
                total_count=total_count,
                threshold=threshold,
                slo_objective=slo_objective,
            )
            burn_rate_results.append(result)

        # Check FAST alert condition: short > fast AND long > fast_confirm
        short_result = next((r for r in burn_rate_results if r.window_name == "short"), None)
        long_result = next((r for r in burn_rate_results if r.window_name == "long"), None)

        fast_alert = False
        if short_result and long_result:
            fast_alert = (
                short_result.burn_rate > self.config.burn_rate.fast
                and long_result.burn_rate > self.config.burn_rate.fast_confirm
            )

        # Check SLOW alert condition: mid > slow AND long > slow_confirm
        mid_result = next((r for r in burn_rate_results if r.window_name == "mid"), None)
        slow_alert = False
        if mid_result and long_result:
            slow_alert = (
                mid_result.burn_rate > self.config.burn_rate.slow
                and long_result.burn_rate > self.config.burn_rate.slow_confirm
            )

        should_fire = fast_alert or slow_alert
        alert_type = None
        if fast_alert:
            alert_type = "fast"
        elif slow_alert:
            alert_type = "slow"

        reason = None
        if not should_fire:
            reason = "No burn-rate breach detected"
        elif fast_alert:
            reason = f"FAST burn: short={short_result.burn_rate:.2f} > {self.config.burn_rate.fast}, long={long_result.burn_rate:.2f} > {self.config.burn_rate.fast_confirm}"
        elif slow_alert:
            reason = f"SLOW burn: mid={mid_result.burn_rate:.2f} > {self.config.burn_rate.slow}, long={long_result.burn_rate:.2f} > {self.config.burn_rate.slow_confirm}"

        return AlertEvaluationResult(
            alert_id=self.config.alert_id,
            should_fire=should_fire,
            alert_type=alert_type,
            burn_rate_results=burn_rate_results,
            min_traffic_met=True,
            confidence_gate_passed=confidence_gate_passed,
            reason=reason,
        )

    def create_alert_event(
        self,
        evaluation_result: AlertEvaluationResult,
        slo_id: str,
        component: str,
        channel: str,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create alert event dictionary for routing.
        
        Args:
            evaluation_result: AlertEvaluationResult from evaluation
            slo_id: SLO ID
            component: Component identifier
            channel: Channel identifier
            trace_id: Optional trace ID for correlation
            
        Returns:
            Alert event dictionary
        """
        burn_rate_summary = {}
        for result in evaluation_result.burn_rate_results:
            burn_rate_summary[result.window_name] = {
                "burn_rate": result.burn_rate,
                "error_count": result.error_count,
                "total_count": result.total_count,
                "breach": result.breach,
            }

        alert_event = {
            "alert_id": evaluation_result.alert_id,
            "slo_id": slo_id,
            "alert_type": evaluation_result.alert_type,
            "severity": "critical" if evaluation_result.alert_type == "fast" else "warning",
            "component": component,
            "channel": channel,
            "trace_id": trace_id,
            "burn_rate_summary": burn_rate_summary,
            "min_traffic_met": evaluation_result.min_traffic_met,
            "confidence_gate_passed": evaluation_result.confidence_gate_passed,
            "reason": evaluation_result.reason,
            "routing_mode": self.config.routing.mode,
            "routing_target": self.config.routing.target,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return alert_event
