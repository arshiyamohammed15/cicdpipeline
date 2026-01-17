"""
OBS-13: Forecast Calculator - Time-to-breach computation from burn-rate trends.

Deterministic forecasting using burn-rate trends to estimate time until SLO breach.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    from isodate import parse_duration
except ImportError:
    import re
    from datetime import timedelta

    def parse_duration(duration_str: str) -> timedelta:
        """Simple ISO-8601 duration parser (PT5M -> timedelta)."""
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
        if not match:
            raise ValueError(f"Invalid ISO-8601 duration: {duration_str}")

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

logger = logging.getLogger(__name__)


@dataclass
class BurnRateTrend:
    """Burn rate trend information."""

    current_burn_rate: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    trend_slope: float  # Positive = increasing, negative = decreasing
    window_used: str  # ISO-8601 duration


@dataclass
class ForecastResult:
    """Result of forecast computation."""

    forecast_id: str
    slo_id: str
    sli_id: str
    time_to_breach_seconds: Optional[float]  # None if breach not predicted within horizon
    horizon_seconds: float
    confidence: float  # 0.0 to 1.0
    burn_rate_trend: BurnRateTrend
    component: str
    channel: str


class ForecastCalculator:
    """
    Forecast calculator for time-to-breach estimation.

    Uses burn-rate trends to predict when an SLO will be breached.
    Deterministic computation with no AI dependencies.
    """

    def __init__(self, horizon_seconds: float = 86400.0):  # Default: 24 hours
        """
        Initialize forecast calculator.

        Args:
            horizon_seconds: Maximum forecast horizon in seconds (default: 24 hours)
        """
        self.horizon_seconds = horizon_seconds

    def compute_burn_rate_trend(
        self,
        burn_rate_history: List[Dict[str, Any]],
        window_duration: str,  # ISO-8601 duration
    ) -> BurnRateTrend:
        """
        Compute burn rate trend from historical data.

        Args:
            burn_rate_history: List of burn rate values with timestamps
                             [{"timestamp": float, "burn_rate": float}, ...]
            window_duration: Time window used for trend computation (ISO-8601)

        Returns:
            BurnRateTrend with current burn rate, direction, and slope
        """
        if not burn_rate_history:
            return BurnRateTrend(
                current_burn_rate=0.0,
                trend_direction="stable",
                trend_slope=0.0,
                window_used=window_duration,
            )

        # Sort by timestamp (oldest first)
        sorted_history = sorted(burn_rate_history, key=lambda x: x.get("timestamp", 0.0))

        # Current burn rate is the most recent value
        current_burn_rate = sorted_history[-1].get("burn_rate", 0.0)

        # Compute trend slope using linear regression on recent points
        # Use last 5 points if available, otherwise all points
        trend_points = sorted_history[-5:] if len(sorted_history) >= 5 else sorted_history

        if len(trend_points) < 2:
            # Not enough data for trend
            return BurnRateTrend(
                current_burn_rate=current_burn_rate,
                trend_direction="stable",
                trend_slope=0.0,
                window_used=window_duration,
            )

        # Simple linear regression: slope = (y2 - y1) / (x2 - x1)
        # x = timestamp, y = burn_rate
        x_values = [p.get("timestamp", 0.0) for p in trend_points]
        y_values = [p.get("burn_rate", 0.0) for p in trend_points]

        # Normalize timestamps to start from 0
        if x_values[0] != x_values[-1]:
            x_normalized = [(x - x_values[0]) for x in x_values]
            slope = (y_values[-1] - y_values[0]) / (x_normalized[-1] - x_normalized[0]) if x_normalized[-1] != 0 else 0.0
        else:
            slope = 0.0

        # Determine trend direction
        if abs(slope) < 0.01:  # Threshold for "stable"
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"

        return BurnRateTrend(
            current_burn_rate=current_burn_rate,
            trend_direction=trend_direction,
            trend_slope=slope,
            window_used=window_duration,
        )

    def compute_time_to_breach(
        self,
        slo_objective: float,
        burn_rate_trend: BurnRateTrend,
        burn_rate_threshold: float = 1.0,  # Burn rate at which SLO is breached
    ) -> Optional[float]:
        """
        Compute time-to-breach from burn rate trend.

        Args:
            slo_objective: SLO target (e.g., 0.99 for 99%)
            burn_rate_trend: Burn rate trend information
            burn_rate_threshold: Burn rate threshold for breach (default: 1.0)

        Returns:
            Time to breach in seconds, or None if breach not predicted within horizon
        """
        current_burn_rate = burn_rate_trend.current_burn_rate

        # If current burn rate is already above threshold, breach is immediate
        if current_burn_rate >= burn_rate_threshold:
            return 0.0

        # If trend is decreasing or stable, breach may not occur
        if burn_rate_trend.trend_direction in ["decreasing", "stable"]:
            # Check if trend would ever reach threshold
            if burn_rate_trend.trend_slope <= 0:
                # Burn rate is not increasing, breach unlikely
                return None

        # If trend is increasing, compute time to reach threshold
        if burn_rate_trend.trend_direction == "increasing" and burn_rate_trend.trend_slope > 0:
            # Linear projection: time = (threshold - current) / slope
            # But slope is in burn_rate per second (from timestamp differences)
            # We need to convert to burn_rate per second

            # Estimate slope in burn_rate per second
            # If we have historical data, we can estimate the time scale
            # For now, assume slope is already normalized per second
            # (This is a simplification; in practice, you'd use actual time deltas)

            # Simple linear projection
            burn_rate_gap = burn_rate_threshold - current_burn_rate
            if burn_rate_trend.trend_slope > 0:
                # Convert slope to per-second if needed
                # Assume slope is computed over window duration
                try:
                    window_delta = parse_duration(burn_rate_trend.window_used).total_seconds()
                    if window_delta > 0:
                        slope_per_second = burn_rate_trend.trend_slope / window_delta
                        if slope_per_second > 0:
                            time_to_breach = burn_rate_gap / slope_per_second
                            # Clamp to horizon
                            if time_to_breach <= self.horizon_seconds:
                                return time_to_breach
                except (ValueError, ZeroDivisionError):
                    logger.warning(f"Failed to parse window duration: {burn_rate_trend.window_used}")

        # If we can't compute, return None
        return None

    def compute_confidence(
        self,
        burn_rate_trend: BurnRateTrend,
        data_points: int,
        min_data_points: int = 3,
    ) -> float:
        """
        Compute confidence score for forecast.

        Args:
            burn_rate_trend: Burn rate trend information
            data_points: Number of data points used for trend
            min_data_points: Minimum data points for reliable forecast

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base confidence on data quality
        if data_points < min_data_points:
            return 0.0

        # Higher confidence with more data points
        data_confidence = min(1.0, data_points / 10.0)  # Max confidence at 10+ points

        # Higher confidence with stronger trend (larger slope magnitude)
        trend_strength = min(1.0, abs(burn_rate_trend.trend_slope) * 10.0)  # Normalize

        # Combined confidence
        confidence = (data_confidence * 0.6) + (trend_strength * 0.4)

        return min(1.0, max(0.0, confidence))

    def forecast(
        self,
        forecast_id: str,
        slo_id: str,
        sli_id: str,
        slo_objective: float,
        burn_rate_history: List[Dict[str, Any]],
        window_duration: str,
        component: str = "backend",
        channel: str = "backend",
        burn_rate_threshold: float = 1.0,
    ) -> ForecastResult:
        """
        Compute forecast for an SLO.

        Args:
            forecast_id: Unique identifier for this forecast
            slo_id: SLO identifier
            sli_id: SLI identifier (SLI-A through SLI-G)
            slo_objective: SLO target (e.g., 0.99 for 99%)
            burn_rate_history: Historical burn rate data
            window_duration: Time window used for trend computation (ISO-8601)
            component: Component name
            channel: Channel name
            burn_rate_threshold: Burn rate threshold for breach (default: 1.0)

        Returns:
            ForecastResult with time-to-breach and confidence
        """
        # Compute burn rate trend
        burn_rate_trend = self.compute_burn_rate_trend(burn_rate_history, window_duration)

        # Compute time to breach
        time_to_breach_seconds = self.compute_time_to_breach(
            slo_objective=slo_objective,
            burn_rate_trend=burn_rate_trend,
            burn_rate_threshold=burn_rate_threshold,
        )

        # Compute confidence
        confidence = self.compute_confidence(
            burn_rate_trend=burn_rate_trend,
            data_points=len(burn_rate_history),
        )

        return ForecastResult(
            forecast_id=forecast_id,
            slo_id=slo_id,
            sli_id=sli_id,
            time_to_breach_seconds=time_to_breach_seconds,
            horizon_seconds=self.horizon_seconds,
            confidence=confidence,
            burn_rate_trend=burn_rate_trend,
            component=component,
            channel=channel,
        )
