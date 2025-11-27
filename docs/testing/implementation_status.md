# Test Suite Implementation Status

## ✅ Completed

### Infrastructure
- ✅ Shared harness package (`tests/shared_harness/`) with core utilities
- ✅ Module-specific fixtures (Alerting, Budgeting, Deployment)
- ✅ Pytest markers registered in `pyproject.toml`
- ✅ Evidence pack generation plugin (`tests/pytest_evidence_plugin.py`)
- ✅ CI/CD integration (Jenkinsfile updated with mandatory test stage)
- ✅ Documentation (`docs/testing/ci_integration_guide.md`)

### Data Governance & Privacy (M22)
- ✅ Unit tests marked with `dgp_regression`
- ✅ Security tests marked with `dgp_security`
- ✅ Performance tests marked with `dgp_performance`
- ✅ Compliance tests marked with `dgp_compliance`
- ✅ Integration tests marked with `dgp_regression`
- ⚠️ **Gap**: Some Risk→Test Matrix items still "Not started" (see below)

## ⏳ Remaining Work

### 1. Add Markers to Existing Test Suites

**Alerting & Notification Service (EPC-4)**
- [ ] Add `@pytest.mark.alerting_regression` to regression tests
- [ ] Add `@pytest.mark.alerting_security` to security tests
- [ ] Add `@pytest.mark.alerting_performance` to performance tests
- [ ] Files to update: `test_*_comprehensive.py`, `test_security_*.py`, `test_performance_*.py`

**Budgeting, Rate-Limiting & Cost Observability (M35)**
- [ ] Add `@pytest.mark.budgeting_regression` to regression tests
- [ ] Add `@pytest.mark.budgeting_security` to security tests
- [ ] Add `@pytest.mark.budgeting_performance` to performance tests
- [ ] Files to update: `test_budget_service.py`, `test_rate_limit_service.py`, `test_cost_service.py`

**Deployment & Infrastructure (EPC-8)**
- [ ] Add `@pytest.mark.deployment_regression` to regression tests
- [ ] Add `@pytest.mark.deployment_security` to security tests
- [ ] Files to update: `test_deployment_*.py`

### 2. Implement Missing Risk→Test Matrix Test Suites

#### Data Governance & Privacy (M22)
- [ ] **Cross-tenant export denial test** (`test_cross_tenant_export_blocked.py`)
  - Multi-tenant negative tests with tampered payloads
  - Status: "Not started"
  
- [ ] **Right-to-erasure E2E test** (`test_right_to_erasure_workflow.py`)
  - Concurrent load, storage shard clearing, cache invalidation
  - Status: "Not started"

- [ ] **Classification latency perf test** (enhance existing)
  - Verify p95 ≤ 100ms across PII/SPI workloads
  - Status: "Not started" (we have basic perf tests but need PRD-aligned scenarios)

#### Alerting & Notification Service (EPC-4)
- [ ] **Deduplication regression test** (`test_alert_deduplication_regression.py`)
  - Golden-path: input burst vs. deduped incident count
  - Status: "Not started"
  - Use: `AlertFixtureFactory.create_alert_burst()`

- [ ] **Quiet hours suppression test** (`test_quiet_hours_suppression.py`)
  - Time-travel harness, policy loader, channel spy
  - Status: "Not started"
  - Use: `AlertFixtureFactory.create_quiet_hours_alert()`

- [ ] **Alert fatigue controls test** (`test_fatigue_controls_metrics.py`)
  - Metrics-driven: per-tenant alert volume within noise budget
  - Status: "Not started"

- [ ] **P1 paging latency perf test** (`test_p1_paging_latency.py`)
  - Ingestion→delivery latency <30s under load
  - Status: "Not started"

#### Budgeting, Rate-Limiting & Cost Observability (M35)
- [ ] **Budget enforcement bypass test** (`test_budget_enforcement_matrix.py`)
  - Hard-stop vs soft-limit vs throttle for overlapping budgets
  - Status: "Not started"
  - Use: `BudgetFixtureFactory.create_overlapping_budgets()`

- [ ] **Rate limit counter accuracy test** (`test_rate_limit_counter_accuracy.py`)
  - Stress test: 10^6 ops, token/leaky bucket accuracy, no counter skew
  - Status: "Not started"

- [ ] **Budget check latency perf test** (`test_budget_check_latency.py`)
  - `/budgets/check` p95 ≤ 10ms, `/rate-limits/check` p95 ≤ 5ms
  - Status: "Not started"

- [ ] **Threshold breach evidence test** (`test_threshold_breach_evidence.py`)
  - ERIS receipts + alert payloads when budgets exceed thresholds
  - Status: "Not started"

#### Deployment & Infrastructure (EPC-8)
- [ ] **Environment parity test** (`test_environment_parity.py`)
  - Config hashes, resource inventory comparison (dev vs staging vs prod)
  - Status: "Not started"
  - Use: `DeploymentFixtureFactory.create_parity_matrix()`

- [ ] **Rollback preconditions test** (`test_rollback_preconditions.py`)
  - Failure signal injection, state checkpointing, rollback triggers
  - Status: "Not started"

- [ ] **Security misconfig test** (`test_deployment_security_policy.py`)
  - Policy-as-code rules (OPA), fixture k8s manifests, block unsafe configs
  - Status: "Not started"

- [ ] **Deployment evidence pack test** (`test_deployment_evidence.py`)
  - Deployment manifest, approvals, ERIS receipts per rollout
  - Status: "Not started"

### 3. Fix Evidence Plugin Path Issues

- [ ] Verify `tests/pytest_evidence_plugin.py` can import from `tests.shared_harness`
- [ ] Test evidence pack generation in a real pytest run
- [ ] Ensure `artifacts/evidence/` directory is created automatically

### 4. Update Risk→Test Matrix

- [ ] As each test suite is implemented, update `docs/testing/risk_test_matrix.md` status column
- [ ] Change "Not started" → "Complete" when tests pass and evidence packs are generated

### 5. CI/CD Validation

- [ ] Run Jenkins pipeline to verify mandatory test stage works
- [ ] Verify evidence packs are archived correctly
- [ ] Confirm build fails if mandatory markers fail

## Priority Order

1. **High Priority** (Release blockers):
   - Add markers to existing Alerting/Budgeting/Deployment tests
   - Fix evidence plugin import paths
   - Verify CI/CD pipeline works

2. **Medium Priority** (Risk mitigation):
   - Implement missing DG&P Risk→Test Matrix items
   - Implement Alerting deduplication and quiet hours tests
   - Implement Budgeting enforcement bypass test

3. **Lower Priority** (Completeness):
   - Remaining Alerting/Budgeting/Deployment Risk→Test Matrix items
   - Update Risk→Test Matrix status as work completes

## Quick Wins

1. **Add markers to existing tests** (30 minutes):
   ```bash
   # Find all test files
   find src/cloud_services/shared-services/*/tests -name "test_*.py"
   # Add appropriate markers based on test content
   ```

2. **Test evidence plugin** (15 minutes):
   ```bash
   pytest -p tests.pytest_evidence_plugin src/cloud_services/shared-services/data-governance-privacy/tests -v
   # Check artifacts/evidence/ for generated ZIP
   ```

3. **Run mandatory markers** (10 minutes):
   ```bash
   pytest -m "dgp_regression or dgp_security or dgp_performance" -v
   ```

