# Health & Reliability Monitoring Load Test Plan

- Tooling: k6 (scripts referenced by `k6/*.js`)
- Scenarios:
  - **Telemetry Throughput (PT-1):** Push 5k metrics/sec via `/v1/health/telemetry` to verify evaluator keeps pace.
  - **API Latency (PT-2):** Exercise `/components/{id}/status` and `/check_safe_to_act` with 500 rps.
- Success Criteria:
  - Average evaluation latency < 250ms.
  - Safe-to-Act median latency < 150ms, P95 < 400ms.
- Run:
  ```
  k6 run tests/health_reliability_monitoring/load/telemetry.js
  ```

