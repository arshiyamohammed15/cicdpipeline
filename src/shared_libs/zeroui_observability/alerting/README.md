# ZeroUI Observability Layer - Phase 2: Alerting & Noise Control

## Overview

This module implements **Phase 2 - Alerting & Noise Control** of the ZeroUI Observability Layer as defined in the Implementation Task Breakdown (OBS-10, OBS-11, OBS-12).

## Components

### OBS-10: Alert Config Contract + Loader

**File**: `alert_config.py`

Implements the `zero_ui.alert_config.v1` schema contract for alert configuration:
- JSON Schema validation
- Config loader with runtime reload support
- Default ticket-only config examples

**Usage**:
```python
from zeroui_observability.alerting import AlertConfigLoader

loader = AlertConfigLoader()
config = loader.load_from_file(Path("alert_config_a1_ticket_only.json"))
```

### OBS-11: Burn-rate Alert Engine (Multi-window) - Ticket Mode

**File**: `burn_rate_engine.py`

Implements multi-window burn-rate alerting per Google SRE Workbook:
- FAST alert: `burn_rate(short) > fast AND burn_rate(long) > fast_confirm`
- SLOW alert: `burn_rate(mid) > slow AND burn_rate(long) > slow_confirm`
- Min traffic gate
- Confidence gate (optional)

**Usage**:
```python
from zeroui_observability.alerting import BurnRateAlertEngine, AlertConfig

engine = BurnRateAlertEngine(config)
window_data = {
    "short": {"error_count": 20, "total_count": 100},
    "mid": {"error_count": 15, "total_count": 100},
    "long": {"error_count": 10, "total_count": 100},
}
result = engine.evaluate_alert(
    window_data=window_data,
    slo_objective=0.99,
)
```

### OBS-12: Noise Control (Dedup, Rate-limit, Suppression) + FPR SLI

**File**: `noise_control.py`

Implements alert noise control:
- Fingerprinting for deduplication
- Rate limiting per fingerprint
- Emits `alert.noise_control.v1` events
- FPR tracking for SLI-G computation

**Usage**:
```python
from zeroui_observability.alerting import NoiseControlProcessor

processor = NoiseControlProcessor(
    dedup_window_seconds=900,
    rate_limit_window_seconds=3600,
    max_alerts_per_window=5,
)

decision, noise_control_event = processor.process_alert(alert_event)
```

### Integration Layer

**File**: `integration.py`

Wires burn-rate engine with:
- EPC-4 (Alerting & Notification Service)
- EPC-5 (Health & Reliability Monitoring)
- SLI Calculator (for SLI-G FPR)

## Example Configurations

Example alert configs are in `examples/`:
- `alert_config_a1_ticket_only.json` - Decision Success SLO Burn (A1)
- `alert_config_a2_ticket_only.json` - Latency Regression (A2)
- `alert_config_a6_with_confidence.json` - Bias Signal Spike with confidence gate (A6)

## Testing

Tests are in `tests/`:
- `test_alert_config.py` - Alert config contract tests
- `test_burn_rate_engine.py` - Burn-rate engine tests
- `test_noise_control.py` - Noise control tests

Run tests:
```bash
python -m pytest src/shared_libs/zeroui_observability/alerting/tests/
```

## Dependencies

- `jsonschema` - Schema validation
- `isodate` - ISO-8601 duration parsing (fallback parser included)

## Acceptance Criteria

### OBS-10 ✅
- [x] Config schema validates
- [x] Invalid configs rejected
- [x] Valid configs load
- [x] Runtime reload supported
- [x] Default ticket-only config examples

### OBS-11 ✅
- [x] Alerts fire only when both windows breach
- [x] Low-traffic suppression works
- [x] No paging yet (ticket mode only)
- [x] Synthetic time-series tests

### OBS-12 ✅
- [x] Alert floods suppressed
- [x] Dedup works
- [x] Rate limiting works
- [x] Noise metrics visible via `alert.noise_control.v1` events
- [x] FPR tracking for SLI-G

## Integration with Phase 0 and Phase 1

### Phase 0 (Contracts & Correlation) ✅

**EventEmitter Integration**:
- `noise_control.py` uses `EventEmitter` to emit `alert.noise_control.v1` events
- Events are automatically wrapped in `zero_ui.obsv.event.v1` envelope
- Redaction is applied via Phase 0's `RedactionEnforcer`
- Events emitted asynchronously (non-blocking)

**TraceContext Integration**:
- `integration.py` uses `TraceContext` for end-to-end correlation
- All alert events include `trace_id` for correlation with source telemetry
- Trace IDs propagate through alert evaluation and routing

**EventType Integration**:
- Uses `EventType.ALERT_NOISE_CONTROL` enum for type safety

See `PHASE_INTEGRATION.md` for detailed integration documentation.

### Phase 1 (Telemetry Backbone) ✅

**SLI Calculator Integration**:
- `integration.py` uses `SLICalculator` to compute SLI-G (False Positive Rate)
- Formula: `false_positive / (false_positive + true_positive)`
- Returns `SLIResult` matching Phase 1's SLI computation format
- FPR feedback automatically triggers SLI-G recomputation

## Integration with Existing Services

### EPC-4 (Alerting & Notification Service)

The integration layer routes alerts to EPC-4 based on `routing.mode`:
- `ticket` - Creates tickets via EPC-4 API
- `page` - Pages on-call (disabled in ticket mode)

### EPC-5 (Health & Reliability Monitoring)

SLI data for burn-rate evaluation can be sourced from EPC-5's SLO tracking service.

## Next Steps (Phase 3)

- OBS-13: Forecast Signals (Time-to-breach, leading indicators)
- OBS-14: Prevent-First Actions (Safe-mode / Routing)
