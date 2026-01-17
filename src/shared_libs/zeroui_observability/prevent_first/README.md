# ZeroUI Observability Layer - Phase 3: Prevent-First Actions

## Overview

This module implements **OBS-14: Prevent-First Actions (Safe-mode / Routing)** for the ZeroUI Observability Layer. It provides confidence-gated prevent-first actions for proactive SLO management.

## Components

### ActionPolicy

Policy-driven action authorization via EPC-3 (Configuration & Policy Management).

**Key Features**:
- Confidence gate enforcement
- Policy evaluation via EPC-3
- Tenant/environment filtering
- Permission-based authorization

**Usage**:
```python
from zeroui_observability.prevent_first import ActionPolicy, ActionPolicyConfig

policy = ActionPolicy()

action_config = ActionPolicyConfig(
    action_id="prevent-first-slo-a",
    action_type="create_ticket",
    enabled=True,
    confidence_gate={"enabled": True, "min_confidence": 0.7},
    permissions={"require_policy_approval": True},
)

authorization = await policy.evaluate_action_authorization(
    action_policy=action_config,
    context={"forecast_data": forecast},
    tenant_id="tenant-1",
)
```

### ActionExecutor

Executes prevent-first actions with confidence gates and policy authorization.

**Supported Actions**:
- `create_ticket`: Create ticket via EPC-4
- `request_human_validation`: Request HITL validation
- `reduce_autonomy_level`: Reduce system autonomy level
- `gate_mode_change`: Gate mode changes

**Usage**:
```python
from zeroui_observability.prevent_first import ActionExecutor

executor = ActionExecutor(
    epc4_client=epc4_client,
    receipt_service=receipt_service,
    action_policy=action_policy,
)

result = await executor.execute_action(
    action_policy=action_config,
    action_type="create_ticket",
    forecast_data={"confidence": 0.8, "time_to_breach_seconds": 3600},
    context={},
    trace_ctx=trace_ctx,
    tenant_id="tenant-1",
)
```

### PreventFirstService

Service that evaluates forecasts and triggers prevent-first actions.

**Key Features**:
- Forecast evaluation
- Confidence gate enforcement
- Action policy loading and management
- Batch forecast evaluation

**Usage**:
```python
from zeroui_observability.prevent_first import PreventFirstService

service = PreventFirstService(
    action_executor=action_executor,
    action_policy=action_policy,
    action_policies_path=Path("config/prevent_first_actions.json"),
)

result = await service.evaluate_and_trigger(
    forecast_data={"confidence": 0.8, "slo_id": "SLO-A"},
    action_id="prevent-first-slo-a",
    tenant_id="tenant-1",
)
```

## Action Policy Configuration

Action policies are configured via JSON files following the `action_policy_schema.json` schema:

```json
{
  "action_id": "prevent-first-slo-a",
  "action_type": "create_ticket",
  "enabled": true,
  "confidence_gate": {
    "enabled": true,
    "min_confidence": 0.7
  },
  "permissions": {
    "tenant_ids": ["tenant-1", "tenant-2"],
    "require_policy_approval": true
  },
  "escalation_path": {
    "target": "team-oncall",
    "channels": ["ticket"],
    "priority": "high"
  },
  "action_parameters": {
    "ticket_title_template": "Prevent-First: SLO-A Breach Forecast",
    "ticket_description_template": "Forecast indicates potential breach in {time_to_breach_seconds}s"
  }
}
```

## Integration

### EPC-3 (Configuration & Policy Management)
- Policy evaluation for action authorization
- Module ID: `zeroui_observability_prevent_first`

### EPC-4 (Alerting & Notification Service)
- Ticket creation via `/v1/alerts` endpoint
- Alert routing and escalation

### PM-7 (Evidence & Receipt Indexing Service)
- Receipt generation for audit trails
- Every action emits receipt with `receipt_id` and `trace_id`

## Safety Features

- **Disabled by default**: All actions are disabled until explicitly enabled
- **Confidence gates**: Actions only execute when confidence >= min_confidence
- **Policy authorization**: Actions require policy approval (if configured)
- **Audit trails**: Every action generates receipt via PM-7

## Testing

Run tests with:
```bash
pytest src/shared_libs/zeroui_observability/prevent_first/tests/
```

## References

- [ZeroUI Observability PRD v0.2](docs/architecture/observability/ZeroUI_Observability_PRD_v0.2.md)
- [Implementation Task Breakdown](docs/architecture/observability/ZeroUI_Observability_Implementation_Task_Breakdown_v0.1.md)
