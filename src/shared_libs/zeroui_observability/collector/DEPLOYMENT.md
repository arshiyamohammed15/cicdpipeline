# ZeroUI Observability Layer - Collector Deployment Guide

## Overview

This document provides deployment instructions for the OpenTelemetry Collector with ZeroUI Observability Layer processors (Schema Guard and Privacy Guard).

## Prerequisites

- OpenTelemetry Collector (v0.90.0 or later)
- Python 3.11+ (for custom processors)
- Environment variables configured (see Configuration section)

## Local Development Setup

### 1. Install OpenTelemetry Collector

**Windows (PowerShell)**:
```powershell
# Download from https://github.com/open-telemetry/opentelemetry-collector/releases
# Extract to a directory, e.g., C:\otel-collector
$env:PATH += ";C:\otel-collector"
```

**Linux/macOS**:
```bash
# Using package manager or download from releases
```

### 2. Configure Environment Variables

Set required environment variables:

```powershell
# Windows PowerShell
$env:ZU_ROOT = "D:\ZeroUI"
$env:ZU_PLANE = "shared"
$env:ZU_REGION = "us-east-1"
$env:OTLP_RECEIVER_GRPC_ENDPOINT = "0.0.0.0:4317"
$env:OTLP_RECEIVER_HTTP_ENDPOINT = "0.0.0.0:4318"
$env:OTLP_EXPORTER_ENDPOINT = "http://localhost:4317"
$env:SCHEMA_GUARD_ENABLED = "true"
$env:PRIVACY_GUARD_ENABLED = "true"
```

### 3. Run Collector

```powershell
# Navigate to project root
cd D:\Projects\ZeroUI2.1

# Run collector with config
otelcol --config=src/shared_libs/zeroui_observability/collector/collector-config.yaml
```

## Plane-Specific Storage Routing

The collector routes telemetry to plane-specific storage paths based on the `ZU_PLANE` environment variable and resource attributes.

### IDE Plane (Laptop)

```powershell
$env:ZU_PLANE = "ide"
$env:ZU_ROOT = "D:\ZeroUI"
```

Storage path: `{ZU_ROOT}/ide/telemetry/(metrics|traces|logs)/dt={yyyy}-{mm}-{dd}/`

### Tenant Plane

```powershell
$env:ZU_PLANE = "tenant"
$env:ZU_TENANT_ID = "tenant-123"
$env:ZU_REGION = "us-east-1"
```

Storage path: `{ZU_ROOT}/tenant/{tenant_id}/{region}/telemetry/(metrics|traces|logs)/dt={yyyy}-{mm}-{dd}/`

### Product Plane

```powershell
$env:ZU_PLANE = "product"
$env:ZU_REGION = "us-east-1"
```

Storage path: `{ZU_ROOT}/product/{region}/telemetry/(metrics|traces|logs)/dt={yyyy}-{mm}-{dd}/`

### Shared Plane

```powershell
$env:ZU_PLANE = "shared"
$env:ZU_ORG_ID = "org-456"
$env:ZU_REGION = "us-east-1"
```

Storage path: `{ZU_ROOT}/shared/{org_id}/{region}/telemetry/(metrics|traces|logs)/dt={yyyy}-{mm}-{dd}/`

## Health Check Endpoints

The collector exposes health check endpoints:

- **Health**: `http://localhost:13133/`
- **Metrics**: `http://localhost:8888/metrics`
- **ZPages**: `http://localhost:55679/debug/tracez`

## Configuration Options

### Schema Guard Processor

- `SCHEMA_GUARD_ENABLED`: Enable/disable schema validation (default: `true`)
- `SCHEMA_DIR`: Path to schema directory (default: `src/shared_libs/zeroui_observability/contracts`)
- `SCHEMA_GUARD_REJECT_ON_INVALID`: Reject invalid events (default: `true`)
- `SCHEMA_GUARD_SAMPLE_INVALID`: Sample invalid events for debugging (default: `false`)
- `SCHEMA_GUARD_SAMPLE_RATE`: Sample rate for invalid events (default: `0.1`)

### Privacy Guard Processor

- `PRIVACY_GUARD_ENABLED`: Enable/disable privacy enforcement (default: `true`)
- `DENY_PATTERNS_FILE`: Path to deny patterns JSON file
- `PRIVACY_GUARD_REJECT_ON_VIOLATION`: Reject events with violations (default: `true`)
- `PRIVACY_GUARD_EMIT_AUDIT`: Emit privacy.audit.v1 events (default: `true`)
- `REDACTION_POLICY_VERSION`: Policy version (default: `v1.0`)

### Memory Limiter

- `MEMORY_LIMITER_CHECK_INTERVAL`: Check interval (default: `1s`)
- `MEMORY_LIMITER_LIMIT_MIB`: Memory limit in MiB (default: `512`)
- `MEMORY_LIMITER_SPIKE_LIMIT_MIB`: Spike limit in MiB (default: `128`)

### Batching

- `BATCH_TIMEOUT`: Batch timeout (default: `1s`)
- `BATCH_SIZE`: Batch size (default: `512`)
- `BATCH_MAX_SIZE`: Maximum batch size (default: `1024`)

## Kubernetes Deployment

See `deploy/k8s/` for Kubernetes deployment manifests. The collector can be deployed as:

- **DaemonSet**: One collector per node
- **Deployment**: Centralized collector service
- **Sidecar**: Collector alongside application pods

## Troubleshooting

### Collector Fails to Start

1. Check environment variables are set correctly
2. Verify collector config YAML is valid
3. Check collector logs for errors

### Events Not Appearing

1. Verify OTLP endpoints are accessible
2. Check schema guard is not rejecting events
3. Verify privacy guard is not blocking events
4. Check exporter endpoints are correct

### Performance Issues

1. Adjust `MEMORY_LIMITER_LIMIT_MIB` if memory constrained
2. Increase `BATCH_SIZE` for higher throughput
3. Disable `SCHEMA_GUARD_SAMPLE_INVALID` if not needed
4. Check collector metrics at `http://localhost:8888/metrics`

## References

- OpenTelemetry Collector: https://opentelemetry.io/docs/collector/
- ZeroUI Storage Rules: `storage-scripts/folder-business-rules.md`
- Phase 0 Contracts: `src/shared_libs/zeroui_observability/contracts/`
