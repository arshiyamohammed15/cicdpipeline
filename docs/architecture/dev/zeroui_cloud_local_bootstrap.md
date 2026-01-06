# ZeroUI Cloud Local Bootstrap Guide

This guide explains how to run the ZeroUI Cloud plane stack (Product services + Shared dependencies) locally on your Windows laptop for Functional Module development.

## What This Script Does

The `zeroui_cloud_bootstrap_local.ps1` script automates:

1. **Prerequisite Checks**: Verifies Git, Python 3.11+, Docker Desktop (if needed), Ollama (optional)
2. **Environment Setup**: Creates/updates `.env` with database URLs and ZU_ROOT
3. **Folder Structure**: Creates ZU_ROOT folder structure using existing tooling
4. **Python Environment**: Creates venv and installs dependencies
5. **Docker Dependencies**: Starts Postgres (Product + Shared) and Redis containers
6. **Database Schema**: Optionally applies schema pack and verifies equivalence
7. **Backend Services**: Starts Product and Shared plane services via uvicorn
8. **Unit Tests**: Optionally runs backend unit tests (must pass)
9. **Ollama Models**: Optionally installs and pulls LLM models

The script is **idempotent** - safe to run multiple times.

## Quick Start Commands

### Setup + Start Dependencies

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/zeroui_cloud_bootstrap_local.ps1 -Mode setup -StartDockerDeps
```

This will:
- Check prerequisites
- Create folder structure
- Install Python dependencies
- Start Docker containers (Postgres + Redis)
- **Not** start backend services (use `-Mode start` for that)

### Full Setup + Start + Schema + Tests

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/zeroui_cloud_bootstrap_local.ps1 -Mode setup -StartDockerDeps -ApplyDbSchemaPack -RunUnitTests
```

### Start Services (after setup)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/zeroui_cloud_bootstrap_local.ps1 -Mode start
```

This starts all discovered backend services via uvicorn.

### Stop Services

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/zeroui_cloud_bootstrap_local.ps1 -Mode stop
```

### Check Status

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/zeroui_cloud_bootstrap_local.ps1 -Mode status
```

### Setup with Ollama + Small Models

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/zeroui_cloud_bootstrap_local.ps1 -Mode setup -StartDockerDeps -SetupOllama -PullSmallModels
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-Mode` | Operation mode: `setup`, `start`, `stop`, `status`, `verify` | `setup` |
| `-AutoInstallPrereqs` | Auto-install missing prerequisites via winget | `false` |
| `-StartDockerDeps` | Start Postgres + Redis via docker compose | `false` |
| `-ApplyDbSchemaPack` | Apply schema pack + verify equivalence | `false` |
| `-RunUnitTests` | Run backend unit tests (must pass) | `false` |
| `-SetupOllama` | Ensure Ollama is installed | `false` |
| `-PullSmallModels` | Pull tinyllama, qwen2.5-coder:14b, llama3.1:8b | `false` |
| `-PullBigModels` | Pull qwen2.5-coder:32b | `false` |
| `-ZuRoot` | Override ZU_ROOT path | Uses `.env` or `{repo}\.zu` |

## Ports Used

### Docker Containers
- **Product Postgres**: `localhost:5444` → container `5432`
- **Shared Postgres**: `localhost:5445` → container `5432`
- **Redis**: `localhost:6379` → container `6379`

### Backend Services
- **identity-access-management**: `8001` (`/health`)
- **contracts-schema-registry**: `8000` (`/health`)
- **alerting-notification-service**: `8002` (`/healthz`)
- **evidence-receipt-indexing-service**: `8007` (`/health`)
- **llm_gateway**: `8006` (`/health`)
- **detection-engine-core**: `8003` (`/health`)
- **signal-ingestion-normalization**: `8004` (`/health`)
- **mmm_engine**: `8005` (`/health`)
- **user_behaviour_intelligence**: `8009` (`/health`)

To change ports, modify the `Discover-Services` function in the script.

## Service Inventory

The script automatically discovers services by scanning for `main.py` files in:

### Product Services (ZeroUI Cloud Plane)
- `mmm_engine` - Mirror-Mentor-Multiplier decision engine
- `signal-ingestion-normalization` - Signal ingestion and normalization
- `detection-engine-core` - Detection engine core
- `user_behaviour_intelligence` - User behaviour intelligence

### Shared Services (Dependencies)
- `identity-access-management` - IAM service (M21)
- `contracts-schema-registry` - Schema registry (EPC-12)
- `alerting-notification-service` - Alerting service (EPC-4)
- `evidence-receipt-indexing-service` - ERIS service (PM-7)
- `llm_gateway` - LLM Gateway & Safety Enforcement

### Service Startup Strategy

Services are started via **uvicorn** from the host (not Docker):
- Each service runs as a separate process
- Logs are written to `%USERPROFILE%\.zeroai\cloud\logs\<service>.log`
- Services are started in dependency order (Shared services first, then Product services)
- Health checks are performed after startup

## Configuration

### Environment Variables

The script updates `.env` with:
- `ZU_ROOT` - Four-plane storage root
- `ZEROUI_PRODUCT_DB_URL` - Product plane database URL
- `ZEROUI_SHARED_DB_URL` - Shared plane database URL
- `REDIS_URL` - Redis connection URL

### Docker Environment

Copy `infra/local/zeroui_cloud.local.env.example` to `infra/local/zeroui_cloud.local.env` to customize Docker container settings.

## Troubleshooting

### Docker Desktop Not Running

If Docker commands fail:
1. Start Docker Desktop
2. Wait for it to fully start (whale icon in system tray)
3. Run the script again

### Port Already in Use

If a port is already in use:
1. Check what's using it: `netstat -ano | findstr :8001`
2. Stop the conflicting service
3. Or modify the port in the script's `Discover-Services` function

### Python Launcher "py -3.11" Not Found

1. Install Python 3.11+ from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Or use `-AutoInstallPrereqs` to auto-install via winget

### Service Won't Start

1. Check service logs: `%USERPROFILE%\.zeroai\cloud\logs\<service>.log`
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
   pytest -q tests/cloud_services/ tests/product_services/ -v
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
   .\scripts\setup\zeroui_cloud_bootstrap_local.ps1 -Mode status
   ```

2. **Test a service endpoint**:
   ```powershell
   curl http://localhost:8001/health
   ```

3. **Start developing Functional Modules**:
   - Services are ready to accept requests
   - Use the service URLs from the status output
   - Check service logs in `%USERPROFILE%\.zeroai\cloud\logs\`

4. **Review service documentation**:
   - Check individual service README files in `src/cloud_services/`
   - Review API documentation (OpenAPI specs if available)

## See Also

- `docs/architecture/dev/quickstart_windows.md` - Full Windows quickstart guide
- `docs/architecture/database-runtime-mvp.md` - Database runtime documentation
- `storage-scripts/folder-business-rules.md` - Folder structure rules
- `AGENTS.md` - Agent guidance and rules

