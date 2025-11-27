# DG&P Shared Harness & Test Suite Design

Designs the reusable harness layer plus DG&P-specific test suites so we can immediately implement regression/perf/security coverage that satisfies the PRD (M22) and the Risk → Test Matrix. This plan is executable as-is inside `src/cloud_services/shared-services/data-governance-privacy/tests/`.

## 1. Harness Objectives

1. **Multi-tenant fidelity**: Generate tenants (A, B, attacker) with configurable policies, consent states, and data assets.
2. **IAM scope simulation**: Issue signed tokens for roles (`data_engineer`, `tenant_admin`, `product_admin`, `cross_tenant_blocked`) with overridable scopes and expiry.
3. **Data fixture factory**: Seed classification payloads (PII, SPI, PHI), consent records, retention policies, and lineage graphs.
4. **SLO/perf rig**: Drive synthetic load aligned with PRD latency caps (100 ms classification, 20 ms consent, 50 ms privacy checks, 200 ms lineage).
5. **Evidence packs**: After each suite, emit `evidence/dgp/<timestamp>/` bundle containing pytest JUnit XML, anonymised logs, ERIS receipts, config snapshot, and metrics summary.
6. **Chaos toggles**: Simple switches to simulate IAM latency, ERIS outages, storage shard failures, or policy service timeouts.

## 2. Harness Layout (shared across modules)

Add a `tests/harness/` package reused by Alerting/Budgeting/Deployment later.

```
src/cloud_services/shared-services/data-governance-privacy/tests/
  harness/
    __init__.py
    tenants.py          # TenantFactory, AttackerProfile, isolation helpers
    tokens.py           # IAMTokenFactory, scope mutators, invalid token helpers
    fixtures.py         # ClassificationPayloadFactory, ConsentStateFactory
    receipts.py         # ERISReceiptSpy, evidence bundler hooks
    chaos.py            # Context managers to flip dependency availability flags
    perf_runner.py      # Async driver for locust/k6-style workloads, Prom metrics sink
    evidence.py         # EvidencePackBuilder (zipper + metadata manifest)
    asserts.py          # Custom assertions (tenant isolation, latency budgets, receipt schemas)
```

Key principles:

- Harness utilities should be importable from other modules (`tests.shared_harness` namespace) to avoid duplication.
- Each helper logs structured metadata (tenant, policy, request_id) for easy redaction before evidence packing.
- Chaos toggles wrap async context managers so tests can do `with chaos.eris_outage(): ...`.

## 3. DG&P Suite Structure & Naming

```
tests/
  unit/
    test_classification_engine.py
    test_consent_service.py
    test_privacy_enforcement.py
    test_retention_scheduler.py
  integration/
    test_multistep_consent_flow.py
    test_export_and_redaction.py
    test_retention_policy_execution.py
    test_lineage_trace_accuracy.py
  security/
    test_cross_tenant_export_blocked.py
    test_scope_escalation_denied.py
    test_data_minimization_enforced.py
  performance/
    test_classification_latency_budget.py
    test_consent_latency_budget.py
    test_privacy_gate_throughput.py
  end_to_end/
    test_right_to_erasure_workflow.py
    test_access_request_to_receipt.py
  compliance/
    test_eris_receipts_complete.py
    test_audit_evidence_pack_generated.py
  chaos/
    test_eris_outage_degrades_gracefully.py
    test_policy_service_timeout_fallback.py
```

### Naming conventions

- Use `dgp_` prefix for pytest markers, e.g., `@pytest.mark.dgp_performance`.
- Each test module exports a `SCENARIO_ID` referencing the PRD requirement (e.g., `FR-1-classification`, `FR-4-consent`).
- Fixtures live in `tests/conftest.py` but should delegate heavy lifting to `harness/` helpers.

## 4. Suite Details & Acceptance Criteria

### 4.1 Unit Suite
- **`test_classification_engine.py`**: Validate taxonomy mapping (PII/SPI/PHI) and ensure overrides/statistical detection behave as in PRD Section “classification_engine”.
- **`test_consent_service.py`**: Validate capture/update/revocation flows, ensuring purpose limitation tags persist.
- **`test_privacy_enforcement.py`**: Confirm purpose & minimization policies block disallowed requests and write structured violations.
- **`test_retention_scheduler.py`**: Verify retention policies schedule deletion correctly across monthly/quarterly/custom windows.

Acceptance: 100 % branch coverage on core services, deterministic snapshots for review.

### 4.2 Integration Suite
- **Multistep consent flow**: Create data asset → classify → enforce consent gates → emit ERIS receipt. Assert receipts and DB rows align.
- **Export & redaction**: Request export as Tenant A and confirm redacted copy matches policy, while Tenant B is denied with 403 + ERIS violation.
- **Retention execution**: Simulate time advance to trigger deletion; ensure audit logs contain before/after lineage.
- **Lineage trace**: Validate trace completion ≤200 ms with correct provenance nodes.

### 4.3 Security Suite
- **Cross-tenant export blocked**: Use attacker token to attempt cross-tenant export; expect denial + evidence.
- **Scope escalation denied**: Attempt to escalate scopes within token payload; verify signature validation and audit log.
- **Data minimization**: Attempt to request full payload when policy allows only masked fields; ensure response trimmed and violation logged.

### 4.4 Performance Suite
- Use `perf_runner.py` to fire 5k requests per minute, capturing histograms.
- Enforce PRD budgets: classification ≤100 ms p95, consent ≤20 ms, privacy ≤50 ms, lineage ≤200 ms. Test fails if histograms breach threshold and attaches Prom snapshot to evidence pack.

### 4.5 End-to-End Suite
- **Right to erasure**: Create asset, propagate to storage mock, submit GDPR delete, verify:
  - Data removed from storage shards.
  - Downstream caches invalidated.
  - ERIS receipt + log emitted.
- **Access request**: Submit SAR (subject access request) and ensure timeline from submission to receipt is recorded with steps per PRD.

### 4.6 Compliance Suite
- Validate ERIS receipts exist for every action executed in preceding tests.
- Confirm `evidence.py` zipped bundle contains manifest, hashed artefacts, and is stored under `artifacts/dgp/`.

### 4.7 Chaos Suite
- **ERIS outage**: Simulate ERIS downtime; ensure module queues receipts, surfaces degraded mode, and keeps audit trail.
- **Policy service timeout**: Force policy lookup to timeout; confirm module falls back to cached policy with alert raised.

## 5. Execution Workflow

1. `python -m pytest src/cloud_services/shared-services/data-governance-privacy/tests -m "dgp_regression"` – run regression + security suites on each PR.
2. `python -m pytest ... -m "dgp_performance" --perf-config tests/harness/perf_config.yaml` – nightly perf job.
3. `python -m pytest ... -m "dgp_compliance" --evidence-out artifacts/dgp/<timestamp>` – weekly compliance evidence run.
4. CI job uploads evidence packs to artefact storage + ERIS receipts to registry.

## 6. Shared Harness Roadmap

| Step | Description | Output |
| --- | --- | --- |
| H1 | Implement `HarnessTenantFactory` + IAM token helpers | `tenants.py`, `tokens.py` |
| H2 | Build fixture factories for classification/consent/retention | `fixtures.py` |
| H3 | Wire perf runner + Prom collector stub | `perf_runner.py` |
| H4 | Add evidence pack builder (zip + manifest) | `evidence.py` |
| H5 | Add chaos toggles (ERIS, IAM, storage) | `chaos.py` |
| H6 | Promote harness to reusable namespace for Alerting/Budgeting/Deployment | `tests/shared_harness/__init__.py` |

Once H1–H4 are done, DG&P suites can be implemented; H5–H6 support cross-module adoption.

## 7. Definition of Done Update

- No DG&P story closes until:
  - Relevant suite(s) updated.
  - Evidence pack archived.
  - Risk → Test Matrix row marked “Complete”.
- Releases block on `dgp_regression`, `dgp_security`, `dgp_performance` markers being green.

This document is now the authoritative blueprint for coding the harness and DG&P suites.

