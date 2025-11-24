# Health & Reliability Monitoring Rollout Runbook

## Prerequisites
- Health & Reliability Monitoring container image published to `ghcr.io/zeroui/health-reliability-monitoring`.
- EPC-3 (Configuration & Policy), EPC-4 (Alerting), EPC-8 (Deployment), PM-7 (ERIS) reachable in target environment.
- OTLP collector deployed (`deploy/otel/health_reliability_monitoring-collector.yaml`).
- Database schema applied via `db/migrations/health_reliability_monitoring/001_initial.sql` (or follow `docs/architecture/modules/Health_and_Reliability_Monitoring_migration.md` for manual renames).

## Deployment Steps
1. **Config Review**
   - Confirm `HEALTH_RELIABILITY_MONITORING_DATABASE_URL`, `EPC3_BASE_URL`, OTLP endpoint, and safe-to-act defaults in the deployment manifest.
2. **Apply Manifests**
   ```bash
   kubectl apply -f deploy/k8s/health_reliability_monitoring-deployment.yaml
   ```
3. **Smoke Tests**
   - `kubectl port-forward deploy/health-reliability-monitoring 8095:8095`
   - `curl http://localhost:8095/healthz`
   - Register a synthetic component and ingest telemetry via `/v1/health/telemetry`.
4. **Integration Verification**
   - Check alerts flowing to EPC-4 topic.
   - Confirm ERIS receipts for sample state transitions.
   - Exercise Safe-to-Act API through EPC-8 gate.
5. **Observability**
   - Ensure module metrics appear in Prometheus (`/metrics` endpoint scrape).
   - Verify OTEL collector receiving telemetry from Edge Agents.

## Rollback
1. `kubectl rollout undo deploy/health-reliability-monitoring`
2. Disable Safe-to-Act consumers (EPC-8) if the module remains unavailable.
3. Notify stakeholders via incident channel referencing Health & Reliability Monitoring rollback.

## Acceptance Checklist
- All steps in `docs/architecture/modules/Health_and_Reliability_Monitoring_acceptance_checklist.md` verified.
- Unit + integration tests (`python -m pytest tests/health_reliability_monitoring`) passing in CI.
- Dashboards updated with module metrics.

