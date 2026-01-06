# Tenant Cloud Local Bootstrap Guide

This guide explains how to run the Tenant Cloud plane stack (tenant services + dependencies) locally on your Windows laptop for testing tenant-side ingestion/adapters/evidence/telemetry flows.

## What This Script Does

The `tenant_cloud_bootstrap_local.ps1` script automates:

1. **Prerequisite Checks**: Verifies Git, Python 3.11+, Docker Desktop (if needed), Ollama (optional)
2. **Environment Setup**: Creates/updates `.env` with tenant database URLs and ZU_ROOT
3. **Folder Structure**: Creates ZU_ROOT tenant plane folder structure
4. **Python Environment**: Creates venv and installs dependencies
5. **Docker Dependencies**: Starts Tenant Postgres and Redis containers
6. **Database Schema**: Optionally applies schema pack and verifies equivalence
7. **Tenant Services**: Starts tenant-plane services via uvicorn
8. **Unit Tests**: Optionally runs tenant-plane unit tests (must pass)
9. **Ollama Models**: Optionally installs and pulls LLM models

The script is **idempotent** - safe to run multiple times.

## Quick Start Commands

### Setup + Start Dependencies

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/tenant_cloud_bootstrap_local.ps1 -Mode setup -StartDockerDeps
```

This will:
- Check prerequisites
- Create tenant folder structure
- Install Python dependencies
- Start Docker containers (Tenant Postgres + Redis)
- **Not** start tenant services (use `-Mode start` for that)

### Full Setup + Start + Schema + Tests

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/tenant_cloud_bootstrap_local.ps1 -Mode setup -StartDockerDeps -ApplyDbSchemaPack -RunUnitTests
```

### Start Services (after setup)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/tenant_cloud_bootstrap_local.ps1 -Mode start
```

This starts all discovered tenant services via uvicorn.

### Stop Services

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/tenant_cloud_bootstrap_local.ps1 -Mode stop
```

### Check Status

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/tenant_cloud_bootstrap_local.ps1 -Mode status
```

### Setup with Ollama + Small Models

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/tenant_cloud_bootstrap_local.ps1 -Mode setup -StartDockerDeps -SetupOllama -PullSmallModels
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-Mode` | Operation mode: `setup`, `start`, `stop`, `status`, `verify` | `setup` |
| `-AutoInstallPrereqs` | Auto-install missing prerequisites via winget | `false` |
| `-StartDockerDeps` | Start Tenant Postgres + Redis via docker compose | `false` |
| `-ApplyDbSchemaPack` | Apply schema pack + verify equivalence | `false` |
| `-RunUnitTests` | Run tenant-plane unit tests (must pass) | `false` |
| `-SetupOllama` | Ensure Ollama is installed | `false` |
| `-PullSmallModels` | Pull tinyllama, qwen2.5-coder:14b | `false` |
| `-PullBigModels` | Pull qwen2.5-coder:32b | `false` |
| `-ZuRoot` | Override ZU_ROOT path | Uses `.env` or `{repo}\.zu` |

## Ports Used

### Docker Containers
- **Tenant Postgres**: `localhost:5451` → container `5432`
- **Redis**: `localhost:6381` → container `6379` (uses 6381 to avoid collision with other local stacks)

### Backend Services
- **integration-adapters**: `8010` (`/health`)

To change ports, modify the `Discover-TenantServices` function in the script.

## Tenant Service Inventory

The script automatically discovers tenant services by scanning for `main.py` files in:

### Tenant Services (Discovered)
- `integration-adapters` - Integration Adapters Module (M10)
  - **Path**: `src/cloud_services/client-services/integration-adapters`
  - **Port**: `8010`
  - **Health Endpoint**: `/health`
  - **Webhook Endpoint**: `/v1/integrations/webhooks/{provider_id}/{connection_token}` (POST)
  - **Description**: Unified adapter layer for external system integrations (GitHub, GitLab, Jira, etc.) with webhook ingestion, polling, outbound actions, and SignalEnvelope normalization

### Service Startup Strategy

Services are started via **uvicorn** from the host (not Docker):
- Each service runs as a separate process
- Logs are written to `%USERPROFILE%\.zeroai\tenant\logs\<service>.log`
- Health checks are performed after startup

## Configuration

### Environment Variables

The script updates `.env` with:
- `ZU_ROOT` - Four-plane storage root
- `ZEROUI_TENANT_DB_URL` - Tenant plane database URL
- `REDIS_URL` - Redis connection URL
- `INTEGRATION_ADAPTERS_DATABASE_URL` - Integration adapters database URL (points to tenant DB)

### Docker Environment

Copy `infra/local/tenant_cloud.local.env.example` to `infra/local/tenant_cloud.local.env` to customize Docker container settings.

## Webhook / Ingestion Smoke

### Webhook Endpoint

The `integration-adapters` service exposes a webhook endpoint for receiving provider webhooks:

**Endpoint**: `POST /v1/integrations/webhooks/{provider_id}/{connection_token}`

**Example Request** (PowerShell):
```powershell
$webhookUrl = "http://localhost:8010/v1/integrations/webhooks/github/{connection_token}"
$headers = @{
    "Content-Type" = "application/json"
    "X-GitHub-Event" = "push"
    "X-GitHub-Delivery" = "12345"
}
$body = @{
    action = "opened"
    repository = @{
        name = "test-repo"
    }
} | ConvertTo-Json

Invoke-WebRequest -Uri $webhookUrl -Method POST -Headers $headers -Body $body
```

**Note**: The `connection_token` must be a valid webhook registration UUID. You need to create a connection and webhook registration first via the management APIs.

**Management APIs**:
- `POST /v1/integrations/connections` - Create connection
- `GET /v1/integrations/connections` - List connections
- `POST /v1/integrations/connections/{id}/verify` - Verify connection

See the [Integration Adapters README](../../../src/cloud_services/client-services/integration-adapters/README.md) for full API documentation.

## Troubleshooting

### Docker Desktop Not Running

If Docker commands fail:
1. Start Docker Desktop
2. Wait for it to fully start (whale icon in system tray)
3. Run the script again

### Port Already in Use

If a port is already in use:
1. Check what's using it: `netstat -ano | findstr :8010`
2. Stop the conflicting service
3. Or modify the port in the script's `Discover-TenantServices` function

### Python Launcher "py -3.11" Not Found

1. Install Python 3.11+ from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Or use `-AutoInstallPrereqs` to auto-install via winget

### Service Won't Start

1. Check service logs: `%USERPROFILE%\.zeroai\tenant\logs\<service>.log`
2. Verify Python venv is set up: `.\venv\Scripts\Activate.ps1`
3. Verify dependencies are installed: `pip list`
4. Check database connectivity: `docker ps` to see if containers are running

### Unit Tests Fail

1. Check the error output for specific test failures
2. Ensure all prerequisites are correctly installed
3. Ensure Docker containers are running (if tests require DB)
4. Try running tests manually:
   ```powershell
   .\venv\Scripts\Activate.ps1
   pytest -q tests/cloud_services/client_services/integration_adapters/ -v
   ```

### Schema Pack Scripts Not Found

If `scripts/db/apply_schema_pack.ps1` or `scripts/db/verify_schema_equivalence.ps1` don't exist:
- The script will print a warning and continue
- This is by design - schema pack application is optional
- You can apply schemas manually or create the scripts separately

### Services Start But Health Checks Fail

1. Wait a few seconds - services may need time to initialize
2. Check service logs for errors
3. Verify database connections are working
4. Check that required environment variables are set

## Next Steps

After successful bootstrap:

1. **Verify services are running**:
   ```powershell
   .\scripts\setup\tenant_cloud_bootstrap_local.ps1 -Mode status
   ```

2. **Test a service endpoint**:
   ```powershell
   curl http://localhost:8010/health
   ```

3. **Start testing tenant flows**:
   - Webhook ingestion
   - Integration connections
   - Event normalization
   - Check service logs in `%USERPROFILE%\.zeroai\tenant\logs\`

4. **Review service documentation**:
   - Check `src/cloud_services/client-services/integration-adapters/README.md`
   - Review API documentation (OpenAPI specs if available)

## See Also

- `docs/architecture/dev/quickstart_windows.md` - Full Windows quickstart guide
- `docs/architecture/database-runtime-mvp.md` - Database runtime documentation
- `storage-scripts/folder-business-rules.md` - Folder structure rules
- `AGENTS.md` - Agent guidance and rules

