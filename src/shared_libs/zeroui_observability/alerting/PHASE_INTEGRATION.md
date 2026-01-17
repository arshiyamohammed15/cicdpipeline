# Phase 2 Integration with Phase 0 and Phase 1

## Overview

Phase 2 (Alerting & Noise Control) is now fully integrated with Phase 0 (Contracts & Correlation) and Phase 1 (Telemetry Backbone).

## Phase 0 Integration

### Event Emission

**Component**: `noise_control.py`

- Uses `EventEmitter` from Phase 0 to emit `alert.noise_control.v1` events
- Events are wrapped in the `zero_ui.obsv.event.v1` envelope automatically
- Redaction is applied via Phase 0's `RedactionEnforcer`
- Events are emitted asynchronously (non-blocking)

**Example**:
```python
from zeroui_observability.alerting import NoiseControlProcessor
from zeroui_observability.instrumentation.python.instrumentation import EventEmitter

# EventEmitter is automatically created if not provided
processor = NoiseControlProcessor()

# process_alert() now emits alert.noise_control.v1 events via EventEmitter
decision, payload = await processor.process_alert(alert_event, trace_ctx=trace_ctx)
```

### Trace Context

**Component**: `integration.py`

- Uses `TraceContext` from Phase 0 for end-to-end correlation
- Trace IDs are propagated through alert evaluation and routing
- All alert events include `trace_id` for correlation

**Example**:
```python
from zeroui_observability.correlation.trace_context import get_or_create_trace_context
from zeroui_observability.alerting import ObservabilityAlertingService

trace_ctx = get_or_create_trace_context()
result = await service.evaluate_and_route_alert(
    alert_id="A1",
    window_data={...},
    slo_objective=0.99,
    component="test-component",
    channel="backend",
    trace_ctx=trace_ctx,  # Phase 0 integration
)
```

### Event Types

**Component**: `noise_control.py`

- Uses `EventType.ALERT_NOISE_CONTROL` enum from Phase 0
- Ensures type safety and consistency with other event types

## Phase 1 Integration

### SLI Calculator

**Component**: `integration.py`

- Uses `SLICalculator` from Phase 1 for SLI-G (False Positive Rate) computation
- Computes FPR from false positive feedback: `false_positive / (false_positive + true_positive)`
- Returns `SLIResult` matching Phase 1's SLI computation format

**Example**:
```python
from zeroui_observability.sli.sli_calculator import SLICalculator
from zeroui_observability.alerting import ObservabilityAlertingService

sli_calculator = SLICalculator()
service = ObservabilityAlertingService(
    config_loader=loader,
    noise_control=processor,
    sli_calculator=sli_calculator,  # Phase 1 integration
)

# Record false positive feedback
sli_result = service.record_false_positive_feedback(
    alert_id="A1",
    fingerprint=fingerprint,
    is_false_positive=True,
    detector_type="burn-rate-alert",
)

# Returns SLIResult for SLI-G
if sli_result:
    print(f"FPR: {sli_result.value:.4f}")
```

## Integration Points Summary

| Phase | Component | Integration Point | Purpose |
|-------|-----------|------------------|---------|
| Phase 0 | EventEmitter | `noise_control.py` | Emit `alert.noise_control.v1` events with proper envelope |
| Phase 0 | TraceContext | `integration.py` | End-to-end correlation via trace IDs |
| Phase 0 | EventType | `noise_control.py` | Type-safe event type enum |
| Phase 1 | SLICalculator | `integration.py` | Compute SLI-G (False Positive Rate) |

## Backward Compatibility

All integrations are optional with graceful fallbacks:

- If Phase 0 is not available, events are not emitted but processing continues
- If Phase 1 is not available, SLI-G computation is skipped but feedback is still recorded
- Trace context fallback creates minimal trace IDs if Phase 0 is unavailable

## Testing Integration

To test Phase 2 with Phase 0 and Phase 1:

```python
import asyncio
from zeroui_observability.alerting import (
    AlertConfigLoader,
    NoiseControlProcessor,
    ObservabilityAlertingService,
)
from zeroui_observability.correlation.trace_context import get_or_create_trace_context
from zeroui_observability.sli.sli_calculator import SLICalculator

async def test_integration():
    # Phase 0: Trace context
    trace_ctx = get_or_create_trace_context()
    
    # Phase 1: SLI Calculator
    sli_calculator = SLICalculator()
    
    # Phase 2: Alerting
    loader = AlertConfigLoader()
    config = loader.load_from_file(Path("alert_config_a1_ticket_only.json"))
    
    processor = NoiseControlProcessor()  # Uses EventEmitter from Phase 0
    
    service = ObservabilityAlertingService(
        config_loader=loader,
        noise_control=processor,
        sli_calculator=sli_calculator,  # Phase 1 integration
    )
    
    # Evaluate alert (emits alert.noise_control.v1 via Phase 0)
    result = await service.evaluate_and_route_alert(
        alert_id="A1",
        window_data={
            "short": {"error_count": 20, "total_count": 100},
            "mid": {"error_count": 15, "total_count": 100},
            "long": {"error_count": 10, "total_count": 100},
        },
        slo_objective=0.99,
        component="test-component",
        channel="backend",
        trace_ctx=trace_ctx,  # Phase 0 integration
    )
    
    print(f"Alert evaluated: {result['should_fire']}")
    print(f"Trace ID: {result['trace_id']}")  # From Phase 0

asyncio.run(test_integration())
```

## Benefits

1. **Unified Event Model**: All events use Phase 0's envelope schema
2. **End-to-End Correlation**: Trace IDs link alerts to source telemetry
3. **SLI Computation**: FPR tracking via Phase 1's SLI Calculator
4. **Consistent Instrumentation**: Uses same EventEmitter as other observability events
5. **Privacy Compliance**: Redaction applied via Phase 0's RedactionEnforcer
