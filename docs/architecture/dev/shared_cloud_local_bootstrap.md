# Shared Cloud Local Bootstrap

## Overview

The `shared_cloud_bootstrap_local.ps1` script bootstraps and manages the **Shared Cloud plane** stack on a local laptop/workstation. This enables engineers to run shared-plane capabilities locally, including:

- **PKI/Trust services**: Key Management Service (KMS), Trust as a Capability
- **Registry services**: Contracts & Schema Registry
- **Identity & Access**: Identity Access Management (IAM)
- **Notifications**: Alerting & Notification Service
- **Observability**: Health & Reliability Monitoring, Evidence Receipt Indexing
- **Governance**: Configuration & Policy Management, Data Governance & Privacy
- **Cost Control**: Budgeting, Rate-Limiting & Cost Observability
- **LLM Runtime**: Ollama AI Agent (plane-local)

The script manages:
- Shared PostgreSQL database (port 5455)
- Redis Streams (port 6382)
- All shared-plane FastAPI services
- Optional Ollama setup and model pulling
- Database schema pack application
- Unit test execution

## Quick Start

### One-Command Setup

```powershell
# Full setup with Docker deps, schema, and tests
powershell -ExecutionPolicy Bypass -File scripts/setup/shared_cloud_bootstrap_local.ps1 `
  -Mode setup `
  -StartDockerDeps `
  -ApplyDbSchemaPack `
  -RunUnitTests

# Setup with Ollama and small models
powershell -ExecutionPolicy Bypass -File scripts/setup/shared_cloud_bootstrap_local.ps1 `
  -Mode setup `
  -StartDockerDeps `
  -SetupOllama `
  -PullSmallModels

# Start services (after initial setup)
powershell -ExecutionPolicy Bypass -File scripts/setup/shared_cloud_bootstrap_local.ps1 `
  -Mode start

# Stop services
powershell -ExecutionPolicy Bypass -File scripts/setup/shared_cloud_bootstrap_local.ps1 `
  -Mode stop

# Check status
powershell -ExecutionPolicy Bypass -File scripts/setup/shared_cloud_bootstrap_local.ps1 `
  -Mode status
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `Mode` | Operation mode: `setup`, `start`, `stop`, `status`, `verify` | `setup` |
| `AutoInstallPrereqs` | Auto-install missing prerequisites via winget | `false` |
| `StartDockerDeps` | Start Shared Postgres + Redis via docker compose | `false` |
| `ApplyDbSchemaPack` | Apply schema pack + verify equivalence | `false` |
| `RunUnitTests` | Run shared-plane unit tests (FAIL if any fail) | `false` |
| `SetupOllama` | Ensure Ollama is installed | `false` |
| `PullSmallModels` | Pull tinyllama, qwen2.5-coder:14b | `false` |
| `PullBigModels` | Pull qwen2.5-coder:32b | `false` |
| `ZuRoot` | Override ZU_ROOT path | Auto-detected from `.env` or `{repo}\.zu` |

## Modes

### `setup`
Initial setup mode:
- Checks prerequisites (Git, Python 3.11, Docker if `-StartDockerDeps`, Ollama if `-SetupOllama`)
- Creates/updates `.env` file with `ZU_ROOT` and database URLs
- Creates shared plane folder structure under `ZU_ROOT/shared/`
- Creates Python virtual environment if missing
- Installs Python dependencies (`requirements.txt`, `pip install -e .`)
- Optionally starts Docker dependencies (`-StartDockerDeps`)
- Optionally applies DB schema pack (`-ApplyDbSchemaPack`)
- Optionally runs unit tests (`-RunUnitTests`)
- Optionally sets up Ollama and pulls models (`-SetupOllama`, `-PullSmallModels`, `-PullBigModels`)

### `start`
Starts all discovered shared services:
- Starts Docker dependencies if `-StartDockerDeps` is set
- Starts each shared service via `uvicorn` from the host Python environment
- Waits for health checks
- Services run in background with logs in `%USERPROFILE%\.zeroai\shared\logs\`

### `stop`
Stops all running services:
- Stops Docker containers
- Kills service processes by PID and port

### `status`
Shows current status:
- Docker container status
- Service process status and health endpoints

### `verify`
Verification-only mode:
- Checks prerequisites
- Verifies folder structure exists
- Does not start services or run tests

## Ports Used

| Service | Port | Description |
|--------|------|-------------|
| Shared Postgres | 5455 | PostgreSQL database for shared plane |
| Redis | 6382 | Redis Streams event bus |
| Key Management Service | 8020 | KMS API |
| Contracts & Schema Registry | 8021 | Registry API |
| Identity Access Management | 8022 | IAM API |
| Alerting & Notification | 8023 | Notification API |
| Budgeting & Rate Limiting | 8024 | Budget API |
| Configuration & Policy | 8025 | Policy API |
| Data Governance & Privacy | 8026 | DG&P API |
| Evidence Receipt Indexing | 8027 | ERIS API |
| Health & Reliability | 8028 | HRM API |
| Ollama AI Agent | 8029 | LLM API |
| Trust as a Capability | 8030 | Trust API |

**Note**: Ports are chosen to avoid conflicts with Tenant Cloud (6381, 5451) and ZeroUI Cloud (6379, 5444, 5445) stacks.

## Shared Service Inventory

The script discovers shared services by scanning `src/cloud_services/shared-services/**/main.py`. The following services are currently supported:

| Service | Path | Health Endpoint | Description |
|---------|------|-----------------|-------------|
| **key-management-service** | `shared-services/key-management-service` | `/health` | Cryptographic foundation, trust anchors, key rotation |
| **contracts-schema-registry** | `shared-services/contracts-schema-registry` | `/health` | Schema management, validation, contract enforcement |
| **identity-access-management** | `shared-services/identity-access-management` | `/health` | Identity verification, access decisions, JIT elevation |
| **alerting-notification-service** | `shared-services/alerting-notification-service` | `/healthz` | Alert routing, notification delivery, escalation |
| **budgeting-rate-limiting-cost-observability** | `shared-services/budgeting-rate-limiting-cost-observability` | `/health` | Resource budgeting, rate limiting, cost transparency |
| **configuration-policy-management** | `shared-services/configuration-policy-management` | `/health` | Policy lifecycle, configuration enforcement |
| **data-governance-privacy** | `shared-services/data-governance-privacy` | `/health` | Data classification, consent, retention, lineage |
| **evidence-receipt-indexing-service** | `shared-services/evidence-receipt-indexing-service` | `/health` | Receipt indexing, audit trail, evidence storage |
| **health-reliability-monitoring** | `shared-services/health-reliability-monitoring` | `/health` | Component health, SLO tracking, telemetry evaluation |
| **ollama-ai-agent** | `shared-services/ollama-ai-agent` | `/health` | Plane-local LLM runtime, prompt processing |
| **trust-as-capability** | `shared-services/trust-as-capability` | `/health` | Trust evaluation, workspace trust assessment |

### Service Startup Order

Services are started in dependency order:
1. Infrastructure: `key-management-service`, `identity-access-management`
2. Registry: `contracts-schema-registry`
3. Policy: `configuration-policy-management`
4. Budgeting: `budgeting-rate-limiting-cost-observability`
5. Governance: `data-governance-privacy`
6. Evidence: `evidence-receipt-indexing-service`
7. Notifications: `alerting-notification-service`
8. Monitoring: `health-reliability-monitoring`
9. LLM: `ollama-ai-agent`
10. Trust: `trust-as-capability`

## Evaluation Harness

**Status**: MISSING

The repository does not contain a standalone evaluation harness service. The following evaluation-related components exist:

- **Test Harness Utilities**: `tests/shared_harness/` provides reusable test fixtures and performance runners for unit/integration tests
- **Health Evaluation Service**: Part of `health-reliability-monitoring`, evaluates telemetry into health snapshots
- **Policy Evaluation Engine**: Part of `configuration-policy-management`, evaluates policy rules

The folder structure under `ZU_ROOT/shared/eval/(harness|results|cache)/` is prepared for evaluation harness storage, but no service implementation exists at this time.

To run evaluation workloads:
1. Use the test harness utilities in `tests/shared_harness/` for programmatic evaluation
2. Use `health-reliability-monitoring` for health evaluation
3. Use `configuration-policy-management` for policy evaluation

## Environment Variables

The script writes the following to `{repo-root}/.env` (only if missing):

```ini
ZU_ROOT={resolved-path}
ZEROUI_SHARED_DB_URL=postgresql://zeroui:zeroui_dev_only@localhost:5455/zeroui_shared
REDIS_URL=redis://localhost:6382
```

**Note**: The script never overwrites existing values. To change these, edit `.env` manually.

## Folder Structure

The script ensures the following folder structure under `ZU_ROOT/shared/`:

```
shared/
├── pki/              # PKI files (trust-anchors, certificates, CRL)
├── registry/          # Artifact/model/provider registry
├── telemetry/         # Metrics, traces, logs
├── siem/              # SIEM detections and events
├── governance/        # Controls, attestations, SBOM, supply-chain
├── notifications/     # Notification queues and events
├── evaluation/        # Evaluation harness storage (harness/results/cache)
├── bi-lake/          # Business intelligence data lake
└── queue/             # Message queues
```

If `storage-scripts/tools/create-folder-structure-development.ps1` exists, it is called to create the full structure. Otherwise, only the top-level folders are created.

## Troubleshooting

### Docker Desktop Not Running

**Error**: `docker: command not found` or `Cannot connect to the Docker daemon`

**Solution**:
1. Start Docker Desktop
2. Wait for Docker to be ready (check system tray icon)
3. Verify: `docker ps`

### Port Already in Use

**Error**: `Port 5455 is already in use` or similar

**Solution**:
1. Check what's using the port: `netstat -ano | findstr :5455`
2. Stop the conflicting service or change the port in `infra/local/shared_cloud.local.env`
3. Update the compose file port mapping if needed

### Python 3.11 Not Found

**Error**: `Python 3.11+ is required`

**Solution**:
1. Install Python 3.11: `winget install Python.Python.3.11`
2. Or use `-AutoInstallPrereqs` flag
3. Verify: `py -3.11 -V`

### Service Health Check Fails

**Error**: Service starts but health endpoint returns 500 or timeout

**Solution**:
1. Check service logs: `%USERPROFILE%\.zeroai\shared\logs\{service}.log`
2. Verify database is running: `docker ps --filter name=zeroui-shared-pg`
3. Check database connection: `docker exec -it zeroui-shared-pg psql -U zeroui -d zeroui_shared -c "SELECT 1;"`
4. Verify environment variables in `.env` are correct

### Schema Pack Apply Fails

**Error**: `Schema pack apply failed`

**Solution**:
1. Ensure Docker containers are running: `docker ps`
2. Check database is accessible: `docker exec -it zeroui-shared-pg psql -U zeroui -d zeroui_shared`
3. Review schema pack script: `scripts/db/apply_schema_pack.ps1`
4. Check for migration errors in script output

### Unit Tests Fail

**Error**: `Shared unit tests failed`

**Solution**:
1. Review test output for specific failures
2. Ensure all dependencies are installed: `venv\Scripts\python -m pip install -r requirements.txt`
3. Check test database configuration
4. Run tests individually: `venv\Scripts\python -m pytest tests/cloud_services/shared_services/{service}/ -v`

### Ollama Model Pull Fails

**Error**: `Failed to pull {model}`

**Solution**:
1. Ensure Ollama is running: `ollama list`
2. Check internet connection
3. Verify model name is correct (check Ollama documentation)
4. Try pulling manually: `ollama pull tinyllama:latest`

## Next Steps

After successful bootstrap:

1. **Verify Services**: Run `-Mode status` to confirm all services are running
2. **Test Health Endpoints**: Use `Invoke-WebRequest http://localhost:8020/health` to test each service
3. **Check Logs**: Monitor `%USERPROFILE%\.zeroai\shared\logs\` for service activity
4. **Run Integration Tests**: Execute shared-service integration tests
5. **Configure Services**: Update service configurations as needed for your development workflow

## Related Documentation

- [ZeroUI Bootstrap](bootstrap_one_command.md) - Initial repo setup
- [ZeroUI Cloud Bootstrap](zeroui_cloud_local_bootstrap.md) - Product/Shared plane bootstrap
- [Tenant Cloud Bootstrap](tenant_cloud_local_bootstrap.md) - Tenant plane bootstrap
- [Quick Start Guide](quickstart_windows.md) - Windows development setup

