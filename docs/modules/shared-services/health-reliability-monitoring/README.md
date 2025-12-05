# Health & Reliability Monitoring Service

## Overview

This service implements the Health & Reliability Monitoring capability defined in
`docs/architecture/modules/Health_and_Reliability_Monitoring_PRD_Updated.md`. It consolidates telemetry
from ZeroUI components, evaluates health states, provides Safe-to-Act gating APIs, emits audit-grade
receipts, and integrates with Alerting (EPC-4), Deployment (EPC-8), ERIS (PM-7), and other dependent modules.

## Key Responsibilities

- Monitored component registry with dependency graph & SLO metadata
- Telemetry ingestion pipeline (metrics, probes, heartbeats) using OpenTelemetry conventions
- Policy-driven health evaluation, anti-flapping, roll-ups (component → plane → tenant)
- SLO & error budget tracking with burn-rate metrics
- Health APIs and Safe-to-Act decisions for agents, gates, and humans
- Event exports to EPC-4 and ERIS receipts for auditability
- Full self-observability and resilience controls (graceful UNKNOWN/degraded behavior)

## Service Layout

```
health-reliability-monitoring/
├── config.py                # Settings management (env vars, defaults)
├── main.py                  # FastAPI entrypoint with routers and middlewares
├── models.py                # Pydantic schemas exposed via FastAPI
├── dependencies.py          # IAM, policy, ERIS, EPC-4, EPC-8 client abstractions
├── routes/                  # HTTP API routers (registry, health, safe-to-act, admin)
├── services/                # Business logic (registry, telemetry, evaluator, SLO, events, audit)
├── database/                # SQLAlchemy models, sessions, migrations
├── telemetry/               # OTel collector bootstrap helpers
├── tests/                   # Unit/integration/perf/security/resilience suites (phased in)
└── requirements.txt         # Service dependencies
```

## Running Locally

1. Create virtual environment and install dependencies:
   ```
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Set environment variables (see `config.py` for defaults).
3. Apply migrations (`alembic upgrade head`) to provision the registry schema.
4. Launch the API:
   ```
   uvicorn health_reliability_monitoring.main:app --reload --port 8095
   ```

## Environment Variables & Scopes

| Purpose | Env Var / Scope | Notes |
| --- | --- | --- |
| Service metadata | `HEALTH_RELIABILITY_MONITORING_VERSION`, `HEALTH_RELIABILITY_MONITORING_HTTP_PORT` | Replace any legacy `EPC5_*` vars in manifests/CI |
| Database config | `HEALTH_RELIABILITY_MONITORING_DATABASE_URL`, `HEALTH_RELIABILITY_MONITORING_DB_*` | Default file is `health_reliability_monitoring.db` |
| Telemetry ingest | `HEALTH_RELIABILITY_MONITORING_INGEST_*`, `HEALTH_RELIABILITY_MONITORING_LABEL_CARDINALITY_LIMIT` | Mirrors renamed OTEL collector configuration |
| Safe-to-Act | `HEALTH_RELIABILITY_MONITORING_SAFE_*` | Controls stale telemetry fallbacks |
| OAuth scopes | `health_reliability_monitoring.read`, `health_reliability_monitoring.write`, `health_reliability_monitoring.cross_tenant`, `health_reliability_monitoring.admin` | Update IAM grants and edge tokens accordingly |

## Status

- ✅ PRD alignment and validation report updates
- ✅ Service scaffolding, contracts, and baseline interfaces
- ⏳ Registry, telemetry, evaluator, APIs, testing, and deployment tasks (tracked via repo to-dos)

## Upgrade Checklist

- Ensure all deployments, CI jobs, and secret stores reference the new `HEALTH_RELIABILITY_MONITORING_*` env vars and scopes.
- Apply the schema migration in `db/migrations/health_reliability_monitoring/001_initial.sql` (or run the manual table rename steps in `docs/architecture/modules/Health_and_Reliability_Monitoring_migration.md`) before rolling out to an environment with existing data.
- When committing, include the renamed directories/files (`.github`, `contracts/health/…`, `db/migrations/health_reliability_monitoring/…`, `deploy/…`, `docs/runbooks/…`, `tests/health_reliability_monitoring/…`, etc.) so downstream automation picks up the new structure.

