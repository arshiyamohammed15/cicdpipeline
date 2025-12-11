## Environment Policies (to be filled per deployment)

These are deployment-time decisions that must be set explicitly. Defaults below are recommendations consistent with current code/tests; adjust per compliance and business rules.

### Retention / TTL (recommended defaults)
- Budget utilization and rate-limit usage: retain current + previous period; archive or purge older data (e.g., 60–90 days).
- SIN signals: short-lived (forwarded) or not persisted; DLQ entries: retain 30–90 days or per compliance.
- HRM telemetry/snapshots (if persisted): retain raw telemetry 30–90 days; keep rollups longer if needed.

### Encryption
- In transit: enforce TLS for all service/database/message bus connections.
- At rest: enable database/storage encryption; ensure DLQ payloads follow same policy.

### Isolation
- Enforce tenant_id scoping in queries and APIs; forbid cross-tenant DLQ access (already enforced in SIN stub).
- If regional/plane isolation is required, deploy per region/plane with separate data stores and disallow cross-region data movement.

### Backup / DR
- Define RPO/RTO per service; schedule logical backups for persistent stores (e.g., Postgres) and test restores.
- For DLQ stores backed by buckets/queues, ensure replication and retention align with DLQ TTL.

### Observability
- Metrics: latency p50/p95/p99 and error rates for budgeting/rate-limit and SIN endpoints; threshold/DLQ event counts.
- Logs: structured with tenant/resource identifiers; redact sensitive fields in payloads.
- Tracing: propagate context through ingress/egress paths for SIN and Validator.

### Performance / Scaling
- Budget/rate-limit hot paths: keep caches (as implemented); cap DB connections; consider Redis/fast store for rate-limit counters if persistence not required.
- Partition/segment data by tenant and/or time for large tables.

### Compliance / Privacy
- Classify payload fields (PII/PCI/etc.) where applicable (e.g., SIN payloads, DLQ). Apply minimization/redaction before storage; restrict access accordingly.
- Document data processing locations and lawful bases if required (GDPR/CCPA/etc.).
