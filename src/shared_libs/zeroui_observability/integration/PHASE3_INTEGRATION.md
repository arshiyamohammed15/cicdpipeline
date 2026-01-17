# Phase 3 Integration Guide

## Overview

Phase 3 integration layer wires forecast and prevent-first services with existing observability phases (Phase 0, Phase 1, Phase 2).

## Architecture

```
Phase 0 (Contracts) → Phase 1 (SLI) → Phase 2 (Alerting) → Phase 3 (Forecast & Prevent-First)
                                                                    ↓
                                                              EPC-3, EPC-4, PM-7
```

## Usage

### Basic Forecast Computation

```python
from zeroui_observability.integration.phase3_integration import Phase3IntegrationService
from zeroui_observability.alerting import AlertConfigLoader

# Initialize integration service
integration = Phase3IntegrationService()

# Load alert configs
config_loader = AlertConfigLoader()
alert_configs = [config_loader.load_from_file("alert_config_a1.json")]

# Compute forecasts
forecasts = await integration.compute_forecasts_for_alert_configs(
    alert_configs=alert_configs,
    slo_objectives={"SLO-A": 0.99},
    sli_mappings={"SLO-A": "SLI-A"},
    window_data_by_slo={
        "SLO-A": {
            "short": {"error_count": 5, "total_count": 100},
            "mid": {"error_count": 10, "total_count": 200},
            "long": {"error_count": 20, "total_count": 400},
        }
    },
)
```

### Forecast and Prevent Workflow

```python
# Complete workflow: forecast → evaluate → trigger actions
result = await integration.forecast_and_prevent_workflow(
    alert_configs=alert_configs,
    slo_objectives={"SLO-A": 0.99},
    sli_mappings={"SLO-A": "SLI-A"},
    window_data_by_slo=window_data_by_slo,
    action_mappings={"SLO-A": "prevent-first-slo-a"},
    tenant_id="tenant-1",
    environment="production",
)

# Result contains forecasts and action results
forecasts = result["forecasts"]
action_results = result["action_results"]
```

## Integration Points

### Phase 0 (Contracts & Correlation)
- Event emission via `EventEmitter`
- Trace context propagation via `TraceContext`
- Event types: `FORECAST_SIGNAL`

### Phase 1 (Telemetry Backbone)
- SLI computation via `SLICalculator`
- SLI metrics for forecast inputs

### Phase 2 (Alerting & Noise Control)
- Burn-rate computation via `BurnRateAlertEngine`
- Alert configuration via `AlertConfig`

### EPC Services
- **EPC-3**: Policy evaluation for action authorization
- **EPC-4**: Ticket creation and alert routing
- **PM-7**: Receipt generation for audit trails

## Configuration

### Action Policies

Create action policy files in `config/prevent_first_actions/`:

```json
{
  "action_id": "prevent-first-slo-a",
  "action_type": "create_ticket",
  "enabled": false,
  "confidence_gate": {
    "enabled": true,
    "min_confidence": 0.7
  }
}
```

### Environment Variables

- `ZEROUI_OBSV_ENABLED`: Master switch (default: `true`)
- `ZEROUI_PREVENT_FIRST_ENABLED`: Enable prevent-first actions (default: `false`)
- `ZEROUI_PREVENT_FIRST_ACTIONS_PATH`: Path to action policy files

## Rollout Strategy

1. **Phase 3.1**: Enable forecast computation (read-only, no actions)
2. **Phase 3.2**: Enable prevent-first actions with confidence gates (disabled by default)
3. **Phase 3.3**: Enable actions per tenant/environment via feature flags
4. **Phase 3.4**: Full rollout after calibration

## Safety

- All actions disabled by default
- Confidence gates enforced
- Policy authorization required (if configured)
- Audit trails via PM-7 receipts
- Feature flags for gradual rollout
