# ZeroUI Observability Layer - Feature Flags

## Overview

Feature flags control observability telemetry emission across all tiers (VS Code Extension, Edge Agent, Cloud Services).

## Master Switch

### ZEROUI_OBSV_ENABLED

**Default**: `true`

**Description**: Master switch for all observability telemetry emission.

**Usage**:
```powershell
# Disable all observability
$env:ZEROUI_OBSV_ENABLED = "false"
```

```bash
# Linux/macOS
export ZEROUI_OBSV_ENABLED=false
```

## Event Type Flags

### ZEROUI_OBSV_EMIT_PERF_SAMPLES

**Default**: `true`

**Description**: Enable/disable `perf.sample.v1` event emission.

**Usage**:
```powershell
$env:ZEROUI_OBSV_EMIT_PERF_SAMPLES = "true"
```

### ZEROUI_OBSV_EMIT_ERRORS

**Default**: `true`

**Description**: Enable/disable `error.captured.v1` event emission.

**Usage**:
```powershell
$env:ZEROUI_OBSV_EMIT_ERRORS = "true"
```

## OTLP Configuration

### OTLP_EXPORTER_ENDPOINT

**Default**: `http://localhost:4317`

**Description**: OTLP exporter endpoint (gRPC or HTTP).

**Usage**:
```powershell
$env:OTLP_EXPORTER_ENDPOINT = "http://otel-collector:4317"
```

## Component Configuration

### COMPONENT_VERSION

**Default**: `unknown`

**Description**: Component version for telemetry metadata.

**Usage**:
```powershell
$env:COMPONENT_VERSION = "1.0.0"
```

## Tier-Specific Configuration

### VS Code Extension (Tier 1)

Feature flags are read from VS Code settings or environment variables.

**Settings Path**: `zeroui.observability.enabled`

### Edge Agent (Tier 2)

Feature flags are read from environment variables or configuration file.

### Cloud Services (Tier 3)

Feature flags are read from environment variables or configuration service.

## Rollout Strategy

1. **Phase 1.1**: Enable with `ZEROUI_OBSV_ENABLED=true` (default)
2. **Phase 1.2**: Monitor telemetry volume and adjust sampling if needed
3. **Phase 1.3**: Enable specific event types as needed
4. **Phase 1.4**: Disable if issues detected (rollback)

## References

- Phase 0 Contracts: `src/shared_libs/zeroui_observability/contracts/`
- Instrumentation: `src/shared_libs/zeroui_observability/instrumentation/`
