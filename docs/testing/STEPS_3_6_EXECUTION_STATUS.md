# Steps 3-6 Execution Status

## Step 3: Verify Test Execution - ✅ IN PROGRESS

### Fixes Applied:
1. ✅ Fixed import paths in DG&P tests:
   - `test_cross_tenant_export_blocked.py` - Changed from `tests.shared_harness` to `data_governance_privacy.tests.harness`
   - `test_right_to_erasure_workflow.py` - Changed from `tests.shared_harness` to `data_governance_privacy.tests.harness`

2. ✅ Fixed Alerting test fixtures:
   - Added fixtures to `test_alert_deduplication_regression.py` for `tenant_factory` and `alert_factory`
   - Fixed missing `alert_factory` parameter in test functions

3. ✅ Updated Alerting conftest.py:
   - Added path setup for shared harness imports

### Test Files Status:
- ✅ `test_cross_tenant_export_blocked.py` - Import paths fixed
- ✅ `test_right_to_erasure_workflow.py` - Import paths fixed
- ✅ `test_alert_deduplication_regression.py` - Fixtures added, parameters fixed
- ⏳ Remaining alerting test files need similar fixture fixes

### Next Actions:
1. Apply similar fixture fixes to:
   - `test_quiet_hours_suppression.py`
   - `test_p1_paging_latency.py`
   - `test_fatigue_controls_metrics.py`

2. Fix Budgeting test imports (if needed)

3. Fix Deployment test imports (if needed)

4. Run pytest collection to verify all tests can be discovered

## Step 4: Test Evidence Plugin - ⏳ PENDING

**Status:** Waiting for Step 3 completion

**Command to run:**
```bash
pytest -p tests.pytest_evidence_plugin src/cloud_services/shared-services/data-governance-privacy/tests -v
```

## Step 5: Run Mandatory Marker Suites - ⏳ PENDING

**Status:** Waiting for Step 3 completion

**Command to run:**
```bash
pytest -m "dgp_regression or dgp_security or dgp_performance or alerting_regression or alerting_security or budgeting_regression or deployment_regression" -v --tb=short
```

## Step 6: Fix Runtime Issues - ⏳ PENDING

**Status:** Will address issues found during Steps 3-5

**Common fixes applied so far:**
- Import path corrections
- Missing fixture parameters
- Fixture factory initialization

