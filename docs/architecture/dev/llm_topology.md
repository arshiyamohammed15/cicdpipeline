# LLM Topology Configuration

## Overview

ZeroUI supports two LLM topology modes to accommodate different deployment scenarios:

1. **LOCAL_SINGLE_PLANE**: All planes route to a single IDE plane LLM endpoint (local development)
2. **PER_PLANE**: Each plane has its own LLM endpoint (on-premises, integration, staging)

This configuration is environment-driven via environment variables. No hardcoded hostnames or ports are used in application code.

## Why Topology Override?

### Local Development Constraints

On a single laptop, running multiple Ollama instances (one per plane) is resource-intensive and often unnecessary. The LOCAL_SINGLE_PLANE mode allows:

- Single Ollama instance on the IDE plane
- Tenant, Product, and Shared planes forward requests to the IDE LLM endpoint
- Reduced memory and CPU usage
- Faster local development iteration

### On-Premises / Staging Requirements

In integration or staging environments, each plane should run its own LLM instance to:

- Enforce plane isolation (per ADR-LLM-001)
- Support independent scaling and monitoring
- Test per-plane failover scenarios
- Align with production architecture

## Configuration Model

### Environment Variables

The LLM topology is configured via the following environment variables:

#### Global Mode (Required)
- `LLM_TOPOLOGY_MODE`: One of:
  - `LOCAL_SINGLE_PLANE`: All planes use IDE LLM endpoint
  - `PER_PLANE`: Each plane has its own LLM endpoint

#### Canonical Endpoints (Required)
- `IDE_LLM_BASE_URL`: Base URL for IDE plane LLM service (e.g., `http://localhost:11434`)
- `TENANT_LLM_BASE_URL`: Base URL for Tenant plane LLM service
- `PRODUCT_LLM_BASE_URL`: Base URL for Product plane LLM service
- `SHARED_LLM_BASE_URL`: Base URL for Shared plane LLM service

#### Router Contract (Required)
- `LLM_ROUTER_BASE_PATH`: Base path for LLM router API (default: `/api/v1/llm`)
- `LLM_ROUTER_HEALTH_PATH`: Health check path (default: `/health`)

#### Local Mode Forwarding (Optional, for LOCAL_SINGLE_PLANE)
- `LLM_FORWARD_TO_IDE_PLANES`: Comma-separated list of planes that forward to IDE (e.g., `tenant,product,shared`)

### LOCAL_SINGLE_PLANE Rules

When `LLM_TOPOLOGY_MODE=LOCAL_SINGLE_PLANE`:
- `TENANT_LLM_BASE_URL` MUST equal `IDE_LLM_BASE_URL`
- `PRODUCT_LLM_BASE_URL` MUST equal `IDE_LLM_BASE_URL`
- `SHARED_LLM_BASE_URL` MUST equal `IDE_LLM_BASE_URL`
- `LLM_FORWARD_TO_IDE_PLANES` should be set to `tenant,product,shared`

### PER_PLANE Rules

When `LLM_TOPOLOGY_MODE=PER_PLANE`:
- Each `*_LLM_BASE_URL` can differ
- All four plane URLs must be set and non-empty
- `LLM_FORWARD_TO_IDE_PLANES` should be empty or omitted

## Usage

### Configuration Script

The `scripts/setup/configure_llm_topology.ps1` script provides an idempotent way to configure LLM topology.

#### Apply Local Mode

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/configure_llm_topology.ps1 -Mode local -Apply
```

This sets:
- `LLM_TOPOLOGY_MODE=LOCAL_SINGLE_PLANE`
- All plane URLs to `http://localhost:11434` (default)
- `LLM_FORWARD_TO_IDE_PLANES=tenant,product,shared`

#### Apply Per-Plane Mode

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/configure_llm_topology.ps1 `
  -Mode per-plane `
  -IdeLlmBaseUrl "http://ide-ollama:11434" `
  -TenantLlmBaseUrl "http://tenant-ollama:11434" `
  -ProductLlmBaseUrl "http://product-ollama:11434" `
  -SharedLlmBaseUrl "http://shared-ollama:11434" `
  -Apply
```

#### Verify Configuration

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/configure_llm_topology.ps1 -Mode verify
```

This validates:
- All required keys are present
- LOCAL_SINGLE_PLANE equality rules (if applicable)
- PER_PLANE non-empty rules (if applicable)
- Optional reachability check for IDE endpoint

Exit codes:
- `0`: Configuration is valid
- `1`: Configuration has errors

#### Dry-Run (Preview Changes)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/configure_llm_topology.ps1 -Mode local -PrintDiff
```

Shows what would be changed without modifying files.

#### Write to Separate File

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/configure_llm_topology.ps1 `
  -Mode local `
  -OutEnvPath "infra/local/llm.env" `
  -DoNotTouchRepoEnv `
  -Apply
```

### Example Configuration Files

#### Local Development

See `infra/local/llm_topology.local.env.example`:

```env
LLM_TOPOLOGY_MODE=LOCAL_SINGLE_PLANE
IDE_LLM_BASE_URL=http://localhost:11434
TENANT_LLM_BASE_URL=http://localhost:11434
PRODUCT_LLM_BASE_URL=http://localhost:11434
SHARED_LLM_BASE_URL=http://localhost:11434
LLM_FORWARD_TO_IDE_PLANES=tenant,product,shared
LLM_ROUTER_BASE_PATH=/api/v1/llm
LLM_ROUTER_HEALTH_PATH=/health
```

#### On-Premises / Staging

See `infra/onprem/llm_topology.per_plane.env.example`:

```env
LLM_TOPOLOGY_MODE=PER_PLANE
IDE_LLM_BASE_URL=http://ide-ollama:11434
TENANT_LLM_BASE_URL=http://tenant-ollama:11434
PRODUCT_LLM_BASE_URL=http://product-ollama:11434
SHARED_LLM_BASE_URL=http://shared-ollama:11434
LLM_ROUTER_BASE_PATH=/api/v1/llm
LLM_ROUTER_HEALTH_PATH=/health
```

## Architecture Rules

### Functional Modules Must Use Router Contract

**CRITICAL**: Functional Modules must never call Ollama directly. All LLM interactions must go through the LLM Router contract:

- Use the LLM Gateway service (`LLMGatewayService`)
- Call via the router API endpoint (`/api/v1/llm/chat`, `/api/v1/llm/embedding`)
- The router resolves the correct endpoint based on `LLM_TOPOLOGY_MODE` and plane context

This is enforced by:
- CI guard: `scripts/ci/forbid_direct_ollama_in_fm.ps1`
- ADR-LLM-001: Per-plane LLM instances

### Endpoint Resolution

The LLM Gateway service resolves endpoints as follows:

1. Determine plane context (from request or configuration)
2. Read `LLM_TOPOLOGY_MODE` from environment
3. If `LOCAL_SINGLE_PLANE` and plane is in `LLM_FORWARD_TO_IDE_PLANES`:
   - Use `IDE_LLM_BASE_URL`
4. Otherwise:
   - Use `{PLANE}_LLM_BASE_URL` for the current plane

### Model Policy vs Topology

**Important**: This topology configuration only sets endpoint URLs. Model selection (which model to use for a task) remains in policy configuration and is handled by the `ModelRouter` component per LLM Strategy Directives.

## Related Documentation

- [LLM Strategy Directives](../llm_strategy_directives.md): Policy-driven routing, task classification, receipts
- [ADR-LLM-001: Per-Plane LLM Instances](../adr/ADR-LLM-001-per-plane-llm-instances.md): Architectural decision for plane isolation
- [Four Plane Architecture](../storage_fabric_four_plane.md): Overview of the four-plane deployment model

## Troubleshooting

### Verification Fails

If `-Mode verify` reports errors:

1. Check that all required environment variables are set
2. For `LOCAL_SINGLE_PLANE`, ensure all plane URLs equal `IDE_LLM_BASE_URL`
3. For `PER_PLANE`, ensure all plane URLs are non-empty and distinct
4. Check that `LLM_TOPOLOGY_MODE` is exactly `LOCAL_SINGLE_PLANE` or `PER_PLANE`

### Endpoint Unreachable

The verification script attempts a best-effort reachability check. If it reports "unreachable":

1. Ensure Ollama is running (for localhost endpoints)
2. Check network connectivity (for remote endpoints)
3. Verify firewall rules allow connections
4. Test manually: `curl http://localhost:11434/api/tags` (Ollama API)

### Configuration Not Applied

If changes don't take effect:

1. Ensure the `.env` file is loaded by your application
2. Check that the file path is correct (relative to repo root)
3. Restart services that read environment variables
4. Verify with `-Mode verify` that the configuration is correct

