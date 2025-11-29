# Next Steps for Test Suite Implementation

## ✅ Completed

1. ✅ Shared harness package created (`tests/shared_harness/`)
2. ✅ Missing Risk→Test Matrix test suites implemented (14 new test files)
3. ✅ Markers added to key test files (DG&P, Alerting security/performance/integration, Budgeting, Deployment)
4. ✅ CI/CD integration (Jenkinsfile with mandatory test stage)
5. ✅ Evidence pack generation plugin
6. ✅ All import paths fixed

## 🔄 Immediate Next Steps (Priority Order)

### 1. Update Risk→Test Matrix Status (15 minutes)

Update `docs/testing/risk_test_matrix.md` to reflect implemented tests:

**Data Governance & Privacy (M22):**
- Row 9 (Cross-tenant export): "Not started" → "Complete" (test file: `test_cross_tenant_export_blocked.py`)
- Row 12 (Right-to-erasure): "Not started" → "Complete" (test file: `test_right_to_erasure_workflow.py`)
- Row 11 (Classification latency): "Not started" → "Partial" (test file: `test_latency_budgets.py` exists, may need enhancement)
- Row 13 (ERIS receipts): "Not started" → "Complete" (test file: `test_receipt_emission.py`)

**Alerting & Notification Service (EPC-4):**
- Row 19 (Deduplication): "Not started" → "Complete" (test file: `test_alert_deduplication_regression.py`)
- Row 20 (Quiet hours): "Not started" → "Complete" (test file: `test_quiet_hours_suppression.py`)
- Row 22 (Fatigue controls): "Not started" → "Complete" (test file: `test_fatigue_controls_metrics.py`)
- Row 23 (P1 paging latency): "Not started" → "Complete" (test file: `test_p1_paging_latency.py`)

**Budgeting, Rate-Limiting & Cost Observability (M35):**
- Row 29 (Budget enforcement): "Not started" → "Complete" (test file: `test_budget_enforcement_matrix.py`)
- Row 30 (Rate limit accuracy): "Not started" → "Complete" (test file: `test_rate_limit_counter_accuracy.py`)
- Row 32 (Budget check latency): "Not started" → "Complete" (test file: `test_budget_check_latency.py`)
- Row 33 (Threshold breach evidence): "Not started" → "Complete" (test file: `test_threshold_breach_evidence.py`)

**Deployment & Infrastructure (EPC-8):**
- Row 39 (Environment parity): "Not started" → "Complete" (test file: `test_environment_parity.py`)
- Row 40 (Rollback preconditions): "Not started" → "Complete" (test file: `test_rollback_preconditions.py`)
- Row 42 (Security misconfig): "Not started" → "Complete" (test file: `test_deployment_security_policy.py`)
- Row 43 (Deployment evidence): "Not started" → "Complete" (test file: `test_deployment_evidence.py`)

### 2. Add Markers to Remaining Test Files (30 minutes)

**Alerting tests still needing markers:**
- `test_routes_comprehensive.py` - Add `@pytest.mark.alerting_regression`
- `test_security_quiet_hours.py` - Add `@pytest.mark.alerting_security`
- `test_resilience_chaos.py` - Add `@pytest.mark.alerting_regression` or `chaos`
- `test_performance_ingestion.py` - Add `@pytest.mark.alerting_performance`
- `test_integration_flow.py` - Add `@pytest.mark.alerting_regression`
- `test_notification_delivery_preferences.py` - Add `@pytest.mark.alerting_regression`
- `test_main_endpoints.py` - Add `@pytest.mark.alerting_regression`
- `test_lifecycle_consistency.py` - Add `@pytest.mark.alerting_regression`
- `test_enrichment_and_correlation.py` - Add `@pytest.mark.alerting_regression`
- `test_notification_and_routing_services.py` - Add `@pytest.mark.alerting_regression`
- `test_unit_ingestion.py` - Add `@pytest.mark.alerting_regression`
- `test_clients_and_observability.py` - Add `@pytest.mark.alerting_regression`
- `test_agent_streams_automation.py` - Add `@pytest.mark.alerting_regression`
- `test_dependencies_and_session.py` - Add `@pytest.mark.alerting_regression`

**Budgeting tests still needing markers:**
- `test_rate_limit_service.py` - Add `@pytest.mark.budgeting_regression` and `@pytest.mark.budgeting_performance`
- `test_cost_service.py` - Add `@pytest.mark.budgeting_regression`
- `test_quota_service.py` - Add `@pytest.mark.budgeting_regression`
- `test_event_subscription_service.py` - Add `@pytest.mark.budgeting_regression`
- `test_receipt_service.py` - Add `@pytest.mark.budgeting_compliance`

**Deployment tests:**
- `test_deployment_infrastructure_routes.py` - Add `@pytest.mark.deployment_regression`

### 3. Verify Test Execution (20 minutes)

Run tests to ensure they work:

```bash
# Test DG&P new suites
pytest src/cloud_services/shared-services/data-governance-privacy/tests/security/test_cross_tenant_export_blocked.py -v
pytest src/cloud_services/shared-services/data-governance-privacy/tests/end_to_end/test_right_to_erasure_workflow.py -v

# Test Alerting new suites
pytest src/cloud_services/shared-services/alerting-notification-service/tests/integration/test_alert_deduplication_regression.py -v
pytest src/cloud_services/shared-services/alerting-notification-service/tests/integration/test_quiet_hours_suppression.py -v
pytest src/cloud_services/shared-services/alerting-notification-service/tests/performance/test_p1_paging_latency.py -v
pytest src/cloud_services/shared-services/alerting-notification-service/tests/performance/test_fatigue_controls_metrics.py -v

# Test Budgeting new suites
pytest src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/tests/integration/test_budget_enforcement_matrix.py -v
pytest src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/tests/performance/test_rate_limit_counter_accuracy.py -v
pytest src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/tests/performance/test_budget_check_latency.py -v
pytest src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/tests/compliance/test_threshold_breach_evidence.py -v

# Test Deployment new suites
pytest src/cloud_services/shared-services/deployment-infrastructure/tests/integration/test_environment_parity.py -v
pytest src/cloud_services/shared-services/deployment-infrastructure/tests/integration/test_rollback_preconditions.py -v
pytest src/cloud_services/shared-services/deployment-infrastructure/tests/security/test_deployment_security_policy.py -v
pytest src/cloud_services/shared-services/deployment-infrastructure/tests/compliance/test_deployment_evidence.py -v
```

### 4. Test Evidence Plugin (10 minutes)

Verify evidence pack generation works:

```bash
# Run with evidence plugin
pytest -p tests.pytest_evidence_plugin src/cloud_services/shared-services/data-governance-privacy/tests -v

# Check for evidence pack
ls -la artifacts/evidence/*.zip
```

### 5. Run Mandatory Marker Suites (15 minutes)

Verify all mandatory markers work:

```bash
# Run all mandatory suites
pytest -m "dgp_regression or dgp_security or dgp_performance or alerting_regression or alerting_security or budgeting_regression or deployment_regression" -v --tb=short
```

### 6. Fix Any Runtime Issues (As needed)

If tests fail:
- Fix import errors
- Fix missing fixtures
- Fix service method signatures
- Fix database session handling

### 7. Validate CI/CD Pipeline (Optional - requires Jenkins)

- Run Jenkins pipeline
- Verify mandatory test stage executes
- Verify evidence packs are archived
- Verify build fails if mandatory markers fail

## Summary

**Immediate actions (1-2 hours):**
1. Update Risk→Test Matrix status
2. Add markers to remaining test files
3. Run tests to verify they work
4. Test evidence plugin

**Validation (30 minutes):**
5. Run mandatory marker suites
6. Fix any runtime issues

**CI/CD (when Jenkins available):**
7. Validate pipeline execution

## Files to Update

1. `docs/testing/risk_test_matrix.md` - Update status column
2. `src/cloud_services/shared-services/alerting-notification-service/tests/*.py` - Add markers
3. `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/tests/*.py` - Add markers
4. `src/cloud_services/shared-services/deployment-infrastructure/tests/*.py` - Add markers

