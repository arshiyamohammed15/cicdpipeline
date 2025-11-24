# Health & Reliability Monitoring Migration Guide

The EPC-5 to Health & Reliability Monitoring rename changed database objects, environment variables, scopes, and repository paths. Follow these steps before rolling out the renamed service:

## 1. Database Schema

Existing deployments that used the old `epc5_*` tables must either:

1. **Run the new migration** `db/migrations/health_reliability_monitoring/001_initial.sql` against the target database (preferred).  
2. **Or manually rename** the tables and indexes:
   - `epc5_components` → `health_reliability_monitoring_components`
   - `epc5_component_dependencies` → `health_reliability_monitoring_component_dependencies`
   - `epc5_health_snapshots` → `health_reliability_monitoring_health_snapshots`
   - `epc5_slo_status` → `health_reliability_monitoring_slo_status`
   - Update any `idx_epc5_*` indexes to the new `idx_health_reliability_monitoring_*` names.

## 2. Environment Variables & Secrets

Replace all legacy `EPC5_*` variables with the new `HEALTH_RELIABILITY_MONITORING_*` equivalents (see service README). Update CI pipelines, Kubernetes secrets, Helm charts, and any automation that injects these values.

## 3. IAM Scopes

Tokens and policy bindings must grant `health_reliability_monitoring.read` / `health_reliability_monitoring.write` (plus `.cross_tenant` / `.admin` where applicable). Regenerate service tokens for agents or components that previously used `epc5.*` scopes.

## 4. Kubernetes & OTEL Manifests

Ensure the renamed manifests under `deploy/k8s/health_reliability_monitoring-deployment.yaml` and `deploy/otel/health_reliability_monitoring-collector.yaml` are applied. Images now live at `ghcr.io/zeroui/health-reliability-monitoring`.

## 5. Source Control Hygiene

Stage and commit all renamed directories/files (`.github`, `contracts/health/...`, `db/migrations/health_reliability_monitoring/...`, `deploy/...`, `docs/runbooks/...`, `tests/health_reliability_monitoring/...`, etc.) so downstream consumers pull the new structure.

