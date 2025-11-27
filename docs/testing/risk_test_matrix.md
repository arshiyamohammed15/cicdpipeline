# ZeroUI Risk → Test Matrix

Living tracker that maps module risks to concrete test evidence, per the DG&P, Alerting, Budgeting/Rate-Limiting, and Deployment scope. Update status after every suite/run; do **not** treat this as static documentation.

## Data Governance & Privacy (M22)

| Risk | Required Evidence | Test Type | Harness Needs | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| Cross-tenant data leak via `/privacy/v1/export` or consent APIs | Multi-tenant negative tests proving Tenant A tokens can never read/export Tenant B data, including tampered payloads and parallel sessions | Integration + Security | Tenant fixture generator (A/B/attacker), IAM token issuer, data redaction diff tool | DG&P squad – owner TBD | Complete |
| Consent and privacy enforcement drift (Purpose limitation, data minimization) | Regression suite showing consent capture, purpose tagging, and enforcement receipts for create→classify→enforce workflows | Regression (unit + integration) | Synthetic dataset builder with consent states, ERIS receipt validator | DG&P squad – owner TBD | Partial (unit-only) |
| Classification latency exceeds 100 ms p95 | Perf harness report with p50/p95/p99 latency across PII/SPI workloads, compared to PRD budgets | Performance | Locust/k6 profile tied to Prometheus SLI collector | DG&P squad – owner TBD | Not started |
| Right-to-erasure fails under concurrent load | End-to-end test showing erase requests clear storage/lineage across shards while other tenants remain untouched | End-to-end + Chaos | Parallel tenant operations, storage simulator with audit hooks | DG&P squad – owner TBD | Complete |
| Missing ERIS receipts for compliance actions | Evidence pack containing ERIS receipts for consent, retention, rights workflows | Compliance-as-code | Receipt emitter mock + evidence bundler | DG&P squad – owner TBD | Complete |

## Alerting & Notification Service (EPC-4)

| Risk | Required Evidence | Test Type | Harness Needs | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| Deduplication/correlation regressions create alert storms | Golden-path regression comparing input burst vs. deduped incident count, enforced per PRD FR-3 | Integration | Alert stream replay tool, dedup baseline fixtures | Alerting SRE squad – owner TBD | Complete |
| Quiet hours/maintenance window suppression fails | Scenario tests proving scheduled suppressions prevent paging while still logging evidence | Integration + Policy | Time-travel harness, policy loader, channel spy | Alerting SRE squad – owner TBD | Complete |
| Routing/escalation mis-delivers alerts | Multi-channel tests verifying correct target (chat/email/webhook) and ERIS receipt for each severity | End-to-end | Channel stubs with delivery metrics, IAM persona generator | Alerting SRE squad – owner TBD | Partial (unit routing) |
| Alert fatigue controls drift (rate caps, noise budgets) | Metrics-driven tests that assert per-tenant alert volume stays within configured noise budget across rolling windows | Performance + Security | Load generator, metrics snapshot diff, policy ingestion | Alerting SRE squad – owner TBD | Complete |
| P1 paging latency exceeds SLO | Perf harness output tying ingestion→delivery latency to <30 s requirement under load | Performance | Synthetic PM-3/HRM feed, delivery stopwatch hooks | Alerting SRE squad – owner TBD | Complete |

## Budgeting, Rate-Limiting & Cost Observability (M35)

| Risk | Required Evidence | Test Type | Harness Needs | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| Budget enforcement bypass (soft limit incorrectly enforced) | Regression showing hard-stop vs soft-limit vs throttle behaviours for overlapping budgets | Integration | Budget matrix fixture, policy diff tool | FinOps squad – owner TBD | Complete |
| Rate limit counters drift causing tenant starvation | Stress test verifying token/leaky bucket accuracy over 10^6 ops without counter skew | Performance | High-throughput simulator, Redis/SQLite hook assertions | FinOps squad – owner TBD | Complete |
| Cost attribution misassigns tenants | Unit+integration tests asserting cost records always tag the correct tenant/project even during batch imports | Regression | Multi-tenant ledger fixtures, reconciliation checker | FinOps squad – owner TBD | Partial (unit) |
| Budget check latency >10 ms or rate-limit >5 ms | Perf harness capturing latency histograms for `/budgets/check` and `/rate-limits/check` APIs | Performance | Low-latency benchmark harness, Prometheus exporter | FinOps squad – owner TBD | Complete |
| Alerts/receipts missing for threshold breaches | Evidence pack containing ERIS receipts + alert payloads when budgets exceed thresholds | Compliance + Integration | ERIS client stub, alerting hook verifications | FinOps squad – owner TBD | Complete |

## Deployment & Infrastructure (EPC-8)

| Risk | Required Evidence | Test Type | Harness Needs | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| Environment parity drift (dev ≠ prod) | Automated parity report comparing config hashes/resource inventory across environments | Integration | Parity scanner, Terraform state diff | Deployment squad – owner TBD | Complete |
| Rollback preconditions not enforced | Scenario tests toggling failure signals to ensure rollbacks trigger before irreversible changes | Integration + Chaos | Deploy simulator with failure injection, state checkpointing | Deployment squad – owner TBD | Complete |
| Deployment scripts break IaC invariants | Unit tests over deployment orchestrator ensuring required steps (lint, plan, apply, verify) run in order | Unit | Harness to stub CI signals and filesystem snapshots | Deployment squad – owner TBD | Partial |
| Rollout introduces security misconfig (IAM, network) | Security tests validating policy-as-code rules run and block unsafe manifests | Security | Policy pack runner (e.g., OPA), fixture k8s manifests | Deployment squad – owner TBD | Complete |
| Missing evidence/logging for auditors | Evidence pack including deployment manifest, approvals, ERIS receipts for each rollout | Compliance | Evidence bundler tied to deployment scripts | Deployment squad – owner TBD | Complete |

