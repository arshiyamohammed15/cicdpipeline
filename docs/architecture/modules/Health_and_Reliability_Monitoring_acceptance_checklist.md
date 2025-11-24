# Health & Reliability Monitoring Acceptance Checklist

| Item | Description | Status | Notes |
| --- | --- | --- | --- |
| FR Coverage | FR-1..FR-11 implemented and tested | ☐ | |
| Registry Seed | All P0 modules registered with SLO profiles | ☐ | |
| Telemetry Ingestion | Metrics/probes/heartbeats flowing via OTEL collector | ☐ | |
| Evaluation Engine | Health snapshots persisted with anti-flapping policies | ☐ | |
| Roll-Up Views | Tenant + plane APIs returning expected aggregation | ☐ | |
| Safe-to-Act | Endpoint integrated with EPC-8 & Edge Agent fallback | ☐ | |
| Events & Receipts | EPC-4 alerts and ERIS receipts emitted for transitions | ☐ | |
| Observability | `/metrics` exposed, dashboards updated, alerts defined | ☐ | |
| Tests | Unit, integration, load, resilience suites executed in CI | ☐ | Load/perf k6 harness failed (service not listening); see below |
| Resilience | Telemetry outage + service restart scenarios validated | ☑ | `python -m pytest tests/health_reliability_monitoring/resilience -q` (2025‑11‑24) |
| Load / Performance | k6 telemetry scenario targeting `/v1/health/telemetry` | ☐ | `.\\tools\\k6\\k6-v0.48.0-windows-amd64\\k6.exe run tests/health_reliability_monitoring/load/telemetry.js` failed: connection refused on `localhost:8095`; log: `c:\Users\pc\.cursor\projects\d-Projects-ZeroUI2-0\agent-tools\c8d24ef6-21ca-4ae6-83f6-c768e17d6d3c.txt` |

## Latest Harness Runs
- **k6 load test** – executed with 50 VUs for 60 s; 100 % of 17 852 requests failed because nothing was listening on `http://localhost:8095/v1/health/telemetry`. Start/port-forward a Health & Reliability Monitoring instance on that endpoint and re-run to capture latency/error-budget data.
- **Resilience suite** – `python -m pytest tests/health_reliability_monitoring/resilience -q` passed, confirming Safe-to-Act returns the configured degraded response when telemetry is stale.

