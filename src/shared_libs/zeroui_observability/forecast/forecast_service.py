"""
OBS-13: Forecast Service - Computes forecasts and emits forecast.signal.v1 events.

Service that computes forecasts for all configured SLOs and emits forecast events.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from ..contracts.event_types import EventType
from ..correlation.trace_context import TraceContext, get_or_create_trace_context
from ..instrumentation.python.instrumentation import EventEmitter
from ..sli.sli_calculator import SLICalculator
from ..alerting.alert_config import AlertConfig
from ..alerting.burn_rate_engine import BurnRateAlertEngine

from .forecast_calculator import ForecastCalculator
from .leading_indicators import LeadingIndicatorDetector

logger = logging.getLogger(__name__)


class ForecastService:
    """
    Forecast service for SLO breach prediction.

    Computes time-to-breach forecasts using burn-rate trends and leading indicators.
    Emits forecast.signal.v1 events for dashboard visualization.
    """

    def __init__(
        self,
        sli_calculator: Optional[SLICalculator] = None,
        event_emitter: Optional[EventEmitter] = None,
        horizon_seconds: float = 86400.0,  # 24 hours
    ):
        """
        Initialize forecast service.

        Args:
            sli_calculator: SLI calculator instance (Phase 1)
            event_emitter: Event emitter instance (Phase 0)
            horizon_seconds: Forecast horizon in seconds
        """
        self.sli_calculator = sli_calculator or SLICalculator()
        self.event_emitter = event_emitter
        self.forecast_calculator = ForecastCalculator(horizon_seconds=horizon_seconds)
        self.leading_indicator_detector = LeadingIndicatorDetector()

    async def compute_forecast(
        self,
        alert_config: AlertConfig,
        slo_objective: float,
        sli_id: str,
        window_data: Dict[str, Dict[str, int]],  # Window data from Phase 2
        sli_b_history: Optional[List[Dict[str, Any]]] = None,  # SLI-B time series
        sli_c_history: Optional[List[Dict[str, Any]]] = None,  # SLI-C time series
        bias_events: Optional[List[Dict[str, Any]]] = None,  # Bias events
        user_flag_events: Optional[List[Dict[str, Any]]] = None,  # User flag events
        total_evaluation_events: int = 0,
        component: str = "backend",
        channel: str = "backend",
        trace_ctx: Optional[TraceContext] = None,
    ) -> Dict[str, Any]:
        """
        Compute forecast for an SLO.

        Args:
            alert_config: Alert configuration (from Phase 2)
            slo_objective: SLO target (e.g., 0.99 for 99%)
            sli_id: SLI identifier (SLI-A through SLI-G)
            window_data: Window data from burn-rate engine
            sli_b_history: SLI-B time series (latency)
            sli_c_history: SLI-C time series (error coverage)
            bias_events: Bias scan result events
            user_flag_events: User flag events
            total_evaluation_events: Total evaluation events for flag rate
            component: Component name
            channel: Channel name
            trace_ctx: Optional trace context

        Returns:
            Forecast result dictionary
        """
        # Get or create trace context
        if trace_ctx is None:
            trace_ctx = get_or_create_trace_context()

        # Build burn rate history from window data
        burn_rate_history = self._build_burn_rate_history(
            window_data=window_data,
            slo_objective=slo_objective,
            alert_config=alert_config,
        )

        # Compute forecast
        forecast_id = f"fcst_{uuid.uuid4().hex[:16]}"
        forecast_result = self.forecast_calculator.forecast(
            forecast_id=forecast_id,
            slo_id=alert_config.slo_id,
            sli_id=sli_id,
            slo_objective=slo_objective,
            burn_rate_history=burn_rate_history,
            window_duration=alert_config.windows.long,  # Use long window for trend
            component=component,
            channel=channel,
        )

        # Detect leading indicators
        leading_indicators = self.leading_indicator_detector.detect_all(
            sli_b_history=sli_b_history,
            sli_c_history=sli_c_history,
            bias_events=bias_events,
            user_flag_events=user_flag_events,
            total_evaluation_events=total_evaluation_events,
        )

        # Build forecast payload
        forecast_payload = {
            "forecast_id": forecast_result.forecast_id,
            "slo_id": forecast_result.slo_id,
            "sli_id": forecast_result.sli_id,
            "time_to_breach_seconds": forecast_result.time_to_breach_seconds,
            "horizon_seconds": forecast_result.horizon_seconds,
            "confidence": forecast_result.confidence,
            "leading_indicators": [
                {
                    "indicator_type": ind.indicator_type,
                    "severity": ind.severity,
                    "trend": ind.trend,
                    "value": ind.value,
                    "threshold": ind.threshold,
                }
                for ind in leading_indicators
            ],
            "burn_rate_trend": {
                "current_burn_rate": forecast_result.burn_rate_trend.current_burn_rate,
                "trend_direction": forecast_result.burn_rate_trend.trend_direction,
                "trend_slope": forecast_result.burn_rate_trend.trend_slope,
                "window_used": forecast_result.burn_rate_trend.window_used,
            },
            "component": component,
            "channel": channel,
        }

        # Emit forecast event if emitter available
        if self.event_emitter:
            await self.event_emitter.emit_event(
                event_type=EventType.FORECAST_SIGNAL,
                payload=forecast_payload,
                severity="info",
                trace_ctx=trace_ctx,
            )

        return {
            "forecast_id": forecast_result.forecast_id,
            "slo_id": forecast_result.slo_id,
            "sli_id": forecast_result.sli_id,
            "time_to_breach_seconds": forecast_result.time_to_breach_seconds,
            "horizon_seconds": forecast_result.horizon_seconds,
            "confidence": forecast_result.confidence,
            "leading_indicators": leading_indicators,
            "burn_rate_trend": forecast_result.burn_rate_trend,
            "component": component,
            "channel": channel,
        }

    def _build_burn_rate_history(
        self,
        window_data: Dict[str, Dict[str, int]],
        slo_objective: float,
        alert_config: AlertConfig,
    ) -> List[Dict[str, Any]]:
        """
        Build burn rate history from window data.

        Args:
            window_data: Window data from burn-rate engine
            slo_objective: SLO target
            alert_config: Alert configuration

        Returns:
            List of burn rate history entries
        """
        import time

        history = []
        current_time = time.time()

        # Create burn-rate engine for computation
        engine = BurnRateAlertEngine(alert_config)

        # Compute burn rate for each window
        for window_name, data in window_data.items():
            error_count = data.get("error_count", 0)
            total_count = data.get("total_count", 0)

            if total_count > 0:
                error_rate, burn_rate = engine.compute_burn_rate(
                    error_count=error_count,
                    total_count=total_count,
                    slo_objective=slo_objective,
                )

                # Use timestamp offset based on window (older windows have older timestamps)
                # Short window = most recent, long window = oldest
                window_offsets = {"short": 0, "mid": -300, "long": -600}  # 5 min, 10 min offsets
                timestamp = current_time + window_offsets.get(window_name, 0)

                history.append({
                    "timestamp": timestamp,
                    "burn_rate": burn_rate,
                    "window_name": window_name,
                })

        # Sort by timestamp (oldest first)
        history.sort(key=lambda x: x.get("timestamp", 0.0))

        return history

    async def compute_forecasts_for_slos(
        self,
        alert_configs: List[AlertConfig],
        slo_objectives: Dict[str, float],  # slo_id -> objective
        sli_mappings: Dict[str, str],  # slo_id -> sli_id
        window_data_by_slo: Dict[str, Dict[str, Dict[str, int]]],  # slo_id -> window_data
        component: str = "backend",
        channel: str = "backend",
        trace_ctx: Optional[TraceContext] = None,
    ) -> List[Dict[str, Any]]:
        """
        Compute forecasts for multiple SLOs.

        Args:
            alert_configs: List of alert configurations
            slo_objectives: SLO objectives by SLO ID
            sli_mappings: SLI ID mappings by SLO ID
            window_data_by_slo: Window data by SLO ID
            component: Component name
            channel: Channel name
            trace_ctx: Optional trace context

        Returns:
            List of forecast results
        """
        forecasts = []

        for alert_config in alert_configs:
            slo_id = alert_config.slo_id
            slo_objective = slo_objectives.get(slo_id, 0.99)  # Default 99%
            sli_id = sli_mappings.get(slo_id, "SLI-A")  # Default SLI-A
            window_data = window_data_by_slo.get(slo_id, {})

            try:
                forecast = await self.compute_forecast(
                    alert_config=alert_config,
                    slo_objective=slo_objective,
                    sli_id=sli_id,
                    window_data=window_data,
                    component=component,
                    channel=channel,
                    trace_ctx=trace_ctx,
                )
                forecasts.append(forecast)
            except Exception as e:
                logger.error(f"Failed to compute forecast for SLO {slo_id}: {e}", exc_info=True)

        return forecasts
