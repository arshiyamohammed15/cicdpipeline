# ZeroUI Observability Layer

## Overview

The ZeroUI Observability Layer provides comprehensive observability, monitoring, and proactive SLO management for the ZeroUI Agentic AI System. It implements a phased approach to observability with deterministic-first design, auditable decisions, and minimal false positives.

## Architecture

The observability layer is organized into four phases:

### Phase 0: Contracts & Correlation ✅
- Event envelope schema (`zero_ui.obsv.event.v1`)
- 12 event type payload schemas (JSON Schema)
- Redaction/minimisation policy (allow/deny rules)
- Trace context propagation (W3C Trace Context)

**Location**: `src/shared_libs/zeroui_observability/contracts/`, `correlation/`, `privacy/`

### Phase 1: Telemetry Backbone ✅
- Collector pipeline (OTLP receiver → validate → enrich → export)
- SLI computation library (7 SLIs: SLI-A through SLI-G)
- Baseline dashboards (D1-D15)
- Storage adapters

**Location**: `src/shared_libs/zeroui_observability/collector/`, `sli/`, `dashboards/`

### Phase 2: Alerting & Noise Control ✅
- Alert config contract (`zero_ui.alert_config.v1`)
- Burn-rate alert engine (multi-window)
- Noise control (dedup, rate-limit, suppression)
- FPR SLI (SLI-G)

**Location**: `src/shared_libs/zeroui_observability/alerting/`

### Phase 3: Forecast & Prevent-First ✅
- Forecast signals (time-to-breach, leading indicators)
- Prevent-first actions (safe-mode, routing)
- Confidence gates
- Policy-driven authorization

**Location**: `src/shared_libs/zeroui_observability/forecast/`, `prevent_first/`

## Quick Start

### Basic Usage

```python
from zeroui_observability.integration.phase3_integration import Phase3IntegrationService
from zeroui_observability.alerting import AlertConfigLoader

# Initialize integration service
integration = Phase3IntegrationService()

# Load alert configs
config_loader = AlertConfigLoader()
alert_configs = [config_loader.load_from_file("alert_config_a1.json")]

# Compute forecasts and trigger prevent-first actions
result = await integration.forecast_and_prevent_workflow(
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
    action_mappings={"SLO-A": "prevent-first-slo-a"},
    tenant_id="tenant-1",
)
```

## Event Types

The observability layer defines 13 event types (12 required + 1 Phase 3):

1. `error.captured.v1` - Contextual error capture
2. `prompt.validation.result.v1` - Prompt validation results
3. `memory.access.v1` - Memory access logs
4. `memory.validation.v1` - Memory validation signals
5. `evaluation.result.v1` - Evaluation results
6. `user.flag.v1` - User feedback flags
7. `bias.scan.result.v1` - Bias detection results
8. `retrieval.eval.v1` - Retrieval evaluation
9. `failure.replay.bundle.v1` - Failure replay bundles
10. `perf.sample.v1` - Performance samples
11. `privacy.audit.v1` - Privacy audit events
12. `alert.noise_control.v1` - Alert noise control events
13. `forecast.signal.v1` - Forecast signals (Phase 3)

## SLIs and SLOs

The layer computes 7 SLIs:

- **SLI-A**: End-to-End Decision Success Rate
- **SLI-B**: End-to-End Latency (p50/p95/p99)
- **SLI-C**: Error Capture Coverage
- **SLI-D**: Prompt Validation Pass Rate
- **SLI-E**: Retrieval Compliance
- **SLI-F**: Evaluation Quality Signal
- **SLI-G**: False Positive Rate (FPR)

## Integration with Existing Services

### Platform Modules (PM)
- **PM-2** (CCCS): Runtime façade services (observability, receipts, redaction)
- **PM-7** (Evidence & Receipt Indexing): Receipt generation for audit trails

### Embedded Platform Capabilities (EPC)
- **EPC-3** (Configuration & Policy Management): Policy evaluation for prevent-first actions
- **EPC-4** (Alerting & Notification Service): Alert routing and ticket creation
- **EPC-5** (Health & Reliability Monitoring): SLO tracking and health monitoring

### Cross-Cutting Planes (CCP)
- **CCP-4** (Observability & Reliability Plane): Core observability infrastructure

## Configuration

### Environment Variables

- `ZEROUI_OBSV_ENABLED`: Master switch (default: `true`)
- `ZEROUI_PREVENT_FIRST_ENABLED`: Enable prevent-first actions (default: `false`)
- `OTLP_EXPORTER_ENDPOINT`: OTLP exporter endpoint (default: `http://localhost:4317`)
- `COMPONENT_VERSION`: Component version for telemetry

### Action Policies

Prevent-first actions are configured via JSON files in `config/prevent_first_actions/`:

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

## Testing

Run all tests:
```bash
pytest src/shared_libs/zeroui_observability/
```

Run Phase 3 tests:
```bash
pytest src/shared_libs/zeroui_observability/forecast/tests/
pytest src/shared_libs/zeroui_observability/prevent_first/tests/
```

## Documentation

- [Phase 0-2 Documentation](alerting/README.md)
- [Phase 3 Forecast Documentation](forecast/README.md)
- [Phase 3 Prevent-First Documentation](prevent_first/README.md)
- [Phase 3 Integration Guide](integration/PHASE3_INTEGRATION.md)

## References

- [ZeroUI Observability PRD v0.2](../../../docs/architecture/observability/ZeroUI_Observability_PRD_v0.2.md)
- [Implementation Task Breakdown](../../../docs/architecture/observability/ZeroUI_Observability_Implementation_Task_Breakdown_v0.1.md)
- [Architecture Document](../../../docs/architecture/observability/ZeroUI_Observability_Architecture_v0.1.md)

## EPC-12 (Contracts & Schema Registry) Integration

The observability layer integrates with EPC-12 to register all schemas:

- **Event envelope schema**: `zero_ui.obsv.event.v1`
- **12 event payload schemas**: All event type payload schemas

### Automatic Registration

Schemas can be automatically registered on module import:

```bash
export ZEROUI_OBSV_AUTO_REGISTER_SCHEMAS=true
export EPC12_SCHEMA_REGISTRY_URL=http://localhost:8000/registry/v1
```

### Manual Registration

```python
from zeroui_observability.integration import register_observability_schemas

# Register all schemas
results = register_observability_schemas(
    base_url="http://localhost:8000/registry/v1",
    enabled=True
)

print(f"Registered {results['succeeded']}/{results['total'] + 1} schemas")
```

### Registration Status

- **Envelope schema**: Registered as `zero_ui.obsv.event.v1` in namespace `zeroui.observability`
- **Payload schemas**: Registered with event type as name (e.g., `error.captured.v1`)
- **Compatibility mode**: `backward` (allows backward-compatible changes)

## Safety and Compliance

- **Deterministic-first**: All core computations are deterministic
- **Audit trails**: Every action generates receipt via PM-7
- **Confidence gates**: All prevent-first actions require confidence >= min_confidence
- **Policy-driven**: Actions require policy authorization (if configured)
- **Disabled by default**: All prevent-first actions disabled until explicitly enabled
- **Constitution compliance**: All code follows ZeroUI constitution rules
