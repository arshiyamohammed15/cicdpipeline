"""
Unit tests for ForecastService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from ...alerting.alert_config import AlertConfig, WindowConfig, BurnRateConfig, MinTrafficConfig, RoutingConfig
from ..forecast_service import ForecastService


class TestForecastService:
    """Test forecast service."""

    @pytest.fixture
    def alert_config(self):
        """Create test alert config."""
        return AlertConfig(
            alert_id="A1",
            slo_id="SLO-A",
            objective="99% success rate",
            windows=WindowConfig(short="PT5M", mid="PT30M", long="PT2H"),
            burn_rate=BurnRateConfig(fast=6.0, fast_confirm=1.0, slow=1.0, slow_confirm=0.5),
            min_traffic=MinTrafficConfig(min_total_events=10),
            routing=RoutingConfig(mode="ticket", target="team-oncall"),
        )

    @pytest.fixture
    def event_emitter(self):
        """Create mock event emitter."""
        emitter = AsyncMock()
        emitter.emit_event = AsyncMock(return_value=True)
        return emitter

    @pytest.mark.asyncio
    async def test_compute_forecast(self, alert_config, event_emitter):
        """Test forecast computation."""
        service = ForecastService(event_emitter=event_emitter)
        
        window_data = {
            "short": {"error_count": 5, "total_count": 100},
            "mid": {"error_count": 10, "total_count": 200},
            "long": {"error_count": 20, "total_count": 400},
        }
        
        result = await service.compute_forecast(
            alert_config=alert_config,
            slo_objective=0.99,
            sli_id="SLI-A",
            window_data=window_data,
            component="test-component",
            channel="backend",
        )
        
        assert "forecast_id" in result
        assert result["slo_id"] == "SLO-A"
        assert result["sli_id"] == "SLI-A"
        assert "confidence" in result
        assert "burn_rate_trend" in result
        assert "leading_indicators" in result
        
        # Verify event was emitted
        event_emitter.emit_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_compute_forecasts_for_slos(self, alert_config, event_emitter):
        """Test computing forecasts for multiple SLOs."""
        service = ForecastService(event_emitter=event_emitter)
        
        alert_configs = [alert_config]
        slo_objectives = {"SLO-A": 0.99}
        sli_mappings = {"SLO-A": "SLI-A"}
        window_data_by_slo = {
            "SLO-A": {
                "short": {"error_count": 5, "total_count": 100},
                "mid": {"error_count": 10, "total_count": 200},
                "long": {"error_count": 20, "total_count": 400},
            }
        }
        
        results = await service.compute_forecasts_for_slos(
            alert_configs=alert_configs,
            slo_objectives=slo_objectives,
            sli_mappings=sli_mappings,
            window_data_by_slo=window_data_by_slo,
        )
        
        assert len(results) == 1
        assert results[0]["slo_id"] == "SLO-A"
