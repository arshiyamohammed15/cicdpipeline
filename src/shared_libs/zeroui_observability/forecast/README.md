# ZeroUI Observability Layer - Phase 3: Forecast Signals

## Overview

This module implements **OBS-13: Forecast Signals (Time-to-breach, leading indicators)** for the ZeroUI Observability Layer. It provides deterministic forecasting of SLO breaches using burn-rate trends and leading indicator detection.

## Components

### ForecastCalculator

Computes time-to-breach estimates from burn-rate trends using deterministic linear projection.

**Key Features**:
- Burn rate trend computation from historical data
- Time-to-breach estimation using linear projection
- Confidence scoring based on data quality and trend strength
- Horizon-based forecasting (default: 24 hours)

**Usage**:
```python
from zeroui_observability.forecast import ForecastCalculator

calculator = ForecastCalculator(horizon_seconds=86400.0)  # 24 hours

# Build burn rate history
history = [
    {"timestamp": current_time - 600, "burn_rate": 0.5},
    {"timestamp": current_time - 300, "burn_rate": 0.7},
    {"timestamp": current_time, "burn_rate": 0.9},
]

# Compute forecast
result = calculator.forecast(
    forecast_id="fcst-123",
    slo_id="SLO-A",
    sli_id="SLI-A",
    slo_objective=0.99,
    burn_rate_history=history,
    window_duration="PT30M",
)
```

### LeadingIndicatorDetector

Detects leading indicators that may signal future SLO breaches:
- **Latency p95 increases** (SLI-B): Detects increasing latency trends
- **Error coverage gaps** (SLI-C): Detects declining error capture coverage
- **Bias signal spikes**: Detects high-confidence bias detections
- **User flag rate increases**: Detects rising user flag rates

**Usage**:
```python
from zeroui_observability.forecast import LeadingIndicatorDetector

detector = LeadingIndicatorDetector(
    latency_threshold_p95_ms=100.0,
    error_coverage_threshold=0.95,
    bias_confidence_threshold=0.7,
    user_flag_rate_threshold=0.05,
)

indicators = detector.detect_all(
    sli_b_history=sli_b_history,
    sli_c_history=sli_c_history,
    bias_events=bias_events,
    user_flag_events=user_flag_events,
    total_evaluation_events=100,
)
```

### ForecastService

Service that computes forecasts for configured SLOs and emits `forecast.signal.v1` events.

**Usage**:
```python
from zeroui_observability.forecast import ForecastService
from zeroui_observability.alerting import AlertConfig

service = ForecastService()

forecast = await service.compute_forecast(
    alert_config=alert_config,
    slo_objective=0.99,
    sli_id="SLI-A",
    window_data=window_data,
    component="backend",
    channel="backend",
)
```

## Event Schema

Forecast events use the `forecast.signal.v1` schema with the following payload:

- `forecast_id`: Unique identifier
- `slo_id`: SLO identifier
- `sli_id`: SLI identifier (SLI-A through SLI-G)
- `time_to_breach_seconds`: Estimated time until breach (null if not predicted)
- `horizon_seconds`: Forecast horizon
- `confidence`: Confidence score (0.0 to 1.0)
- `leading_indicators`: List of detected leading indicators
- `burn_rate_trend`: Burn rate trend information

## Integration

### Phase 0 Integration
- Uses `EventEmitter` to emit `forecast.signal.v1` events
- Uses `TraceContext` for end-to-end correlation

### Phase 1 Integration
- Uses `SLICalculator` for SLI time series computation
- Queries SLI metrics for forecast inputs

### Phase 2 Integration
- Uses `BurnRateAlertEngine` for burn-rate computation
- Uses `AlertConfig` for SLO configuration

## Testing

Run tests with:
```bash
pytest src/shared_libs/zeroui_observability/forecast/tests/
```

## References

- [ZeroUI Observability PRD v0.2](docs/architecture/observability/ZeroUI_Observability_PRD_v0.2.md)
- [Implementation Task Breakdown](docs/architecture/observability/ZeroUI_Observability_Implementation_Task_Breakdown_v0.1.md)
