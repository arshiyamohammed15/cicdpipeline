"""
Unit tests for ForecastCalculator.
"""

import pytest
from datetime import timedelta

from ..forecast_calculator import ForecastCalculator, BurnRateTrend


class TestForecastCalculator:
    """Test forecast calculator."""

    def test_compute_burn_rate_trend_increasing(self):
        """Test burn rate trend computation with increasing trend."""
        calculator = ForecastCalculator()
        
        # Create increasing burn rate history
        import time
        current_time = time.time()
        history = [
            {"timestamp": current_time - 600, "burn_rate": 0.5},
            {"timestamp": current_time - 300, "burn_rate": 0.7},
            {"timestamp": current_time, "burn_rate": 0.9},
        ]
        
        trend = calculator.compute_burn_rate_trend(history, "PT30M")
        
        assert trend.current_burn_rate == 0.9
        assert trend.trend_direction == "increasing"
        assert trend.trend_slope > 0

    def test_compute_burn_rate_trend_decreasing(self):
        """Test burn rate trend computation with decreasing trend."""
        calculator = ForecastCalculator()
        
        import time
        current_time = time.time()
        history = [
            {"timestamp": current_time - 600, "burn_rate": 0.9},
            {"timestamp": current_time - 300, "burn_rate": 0.7},
            {"timestamp": current_time, "burn_rate": 0.5},
        ]
        
        trend = calculator.compute_burn_rate_trend(history, "PT30M")
        
        assert trend.current_burn_rate == 0.5
        assert trend.trend_direction == "decreasing"
        assert trend.trend_slope < 0

    def test_compute_burn_rate_trend_stable(self):
        """Test burn rate trend computation with stable trend."""
        calculator = ForecastCalculator()
        
        import time
        current_time = time.time()
        history = [
            {"timestamp": current_time - 600, "burn_rate": 0.7},
            {"timestamp": current_time - 300, "burn_rate": 0.7},
            {"timestamp": current_time, "burn_rate": 0.7},
        ]
        
        trend = calculator.compute_burn_rate_trend(history, "PT30M")
        
        assert trend.current_burn_rate == 0.7
        assert trend.trend_direction == "stable"
        assert abs(trend.trend_slope) < 0.01

    def test_compute_time_to_breach_immediate(self):
        """Test time-to-breach when burn rate already exceeds threshold."""
        calculator = ForecastCalculator()
        
        trend = BurnRateTrend(
            current_burn_rate=1.5,  # Already above threshold
            trend_direction="increasing",
            trend_slope=0.1,
            window_used="PT30M",
        )
        
        time_to_breach = calculator.compute_time_to_breach(
            slo_objective=0.99,
            burn_rate_trend=trend,
            burn_rate_threshold=1.0,
        )
        
        assert time_to_breach == 0.0

    def test_compute_time_to_breach_increasing_trend(self):
        """Test time-to-breach with increasing trend."""
        calculator = ForecastCalculator(horizon_seconds=3600.0)
        
        trend = BurnRateTrend(
            current_burn_rate=0.5,
            trend_direction="increasing",
            trend_slope=0.001,  # Small positive slope
            window_used="PT30M",
        )
        
        time_to_breach = calculator.compute_time_to_breach(
            slo_objective=0.99,
            burn_rate_trend=trend,
            burn_rate_threshold=1.0,
        )
        
        # Should compute some positive time
        assert time_to_breach is None or time_to_breach > 0

    def test_compute_time_to_breach_decreasing_trend(self):
        """Test time-to-breach with decreasing trend (no breach expected)."""
        calculator = ForecastCalculator()
        
        trend = BurnRateTrend(
            current_burn_rate=0.5,
            trend_direction="decreasing",
            trend_slope=-0.1,
            window_used="PT30M",
        )
        
        time_to_breach = calculator.compute_time_to_breach(
            slo_objective=0.99,
            burn_rate_trend=trend,
            burn_rate_threshold=1.0,
        )
        
        # Should return None (no breach predicted)
        assert time_to_breach is None

    def test_compute_confidence(self):
        """Test confidence computation."""
        calculator = ForecastCalculator()
        
        trend = BurnRateTrend(
            current_burn_rate=0.7,
            trend_direction="increasing",
            trend_slope=0.1,
            window_used="PT30M",
        )
        
        # Low confidence with few data points
        confidence_low = calculator.compute_confidence(trend, data_points=2, min_data_points=3)
        assert confidence_low == 0.0
        
        # Higher confidence with more data points
        confidence_high = calculator.compute_confidence(trend, data_points=10, min_data_points=3)
        assert 0.0 < confidence_high <= 1.0

    def test_forecast(self):
        """Test full forecast computation."""
        calculator = ForecastCalculator(horizon_seconds=3600.0)
        
        import time
        current_time = time.time()
        history = [
            {"timestamp": current_time - 600, "burn_rate": 0.5},
            {"timestamp": current_time - 300, "burn_rate": 0.7},
            {"timestamp": current_time, "burn_rate": 0.9},
        ]
        
        result = calculator.forecast(
            forecast_id="test-forecast",
            slo_id="SLO-A",
            sli_id="SLI-A",
            slo_objective=0.99,
            burn_rate_history=history,
            window_duration="PT30M",
            component="test-component",
            channel="backend",
        )
        
        assert result.forecast_id == "test-forecast"
        assert result.slo_id == "SLO-A"
        assert result.sli_id == "SLI-A"
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0
        assert result.burn_rate_trend.current_burn_rate == 0.9
        assert result.burn_rate_trend.trend_direction == "increasing"
