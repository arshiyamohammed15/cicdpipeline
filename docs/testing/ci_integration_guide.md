# CI/CD Integration Guide for Test Suites

## Overview

ZeroUI test suites are integrated into CI/CD with:
1. **Mandatory pytest markers** that gate releases
2. **Automatic evidence pack generation** after test runs
3. **Artifact uploads** to Jenkins for compliance auditing

## Pytest Markers

### Mandatory Markers (Release Gates)

These markers **must pass** before a release is approved:

- `dgp_regression` - DG&P regression tests
- `dgp_security` - DG&P security tests
- `dgp_performance` - DG&P performance tests
- `alerting_regression` - Alerting regression tests
- `alerting_security` - Alerting security tests
- `budgeting_regression` - Budgeting regression tests
- `deployment_regression` - Deployment regression tests

### Optional Markers

- `dgp_compliance` - Compliance evidence collection
- `alerting_performance` - Alerting performance tests
- `budgeting_performance` - Budgeting performance tests
- `deployment_integration` - Deployment integration tests

## Running Tests Locally

### Run all mandatory suites:
```bash
pytest -m "dgp_regression or dgp_security or dgp_performance" -v
```

### Run specific module:
```bash
pytest -m "dgp_regression" -v
pytest -m "alerting_security" -v
```

### Run with evidence generation:
```bash
pytest -p tests.pytest_evidence_plugin -v
```

## CI/CD Integration

### Jenkins Pipeline

The `Jenkinsfile` includes a **Mandatory Test Suites** stage that:

1. Runs all mandatory marker suites sequentially
2. Fails the build if any suite fails
3. Generates evidence packs automatically
4. Archives evidence packs and JUnit XML reports

### Evidence Packs

Evidence packs are automatically generated after test runs and contain:

- **manifest.json** - Test execution summary
- **receipts.jsonl** - ERIS receipts collected during tests
- **configs.json** - Configuration snapshots
- **metrics.json** - Performance and operational metrics

Location: `artifacts/evidence/*.zip`

### Artifact Storage

Jenkins automatically archives:
- Evidence packs (`artifacts/evidence/*.zip`)
- JUnit XML reports (`artifacts/junit-*.xml`)
- Coverage reports (`htmlcov/`, `coverage.xml`)

## Adding Markers to New Tests

### Example: Unit Test
```python
import pytest

@pytest.mark.dgp_regression
@pytest.mark.unit
def test_classification_engine():
    # Test implementation
    pass
```

### Example: Security Test
```python
@pytest.mark.dgp_security
@pytest.mark.security
def test_cross_tenant_isolation():
    # Test implementation
    pass
```

### Example: Performance Test
```python
@pytest.mark.dgp_performance
@pytest.mark.performance
@pytest.mark.asyncio
async def test_latency_budget():
    # Test implementation
    pass
```

## Evidence Collection in Tests

Tests can collect evidence using the evidence collector:

```python
from tests.pytest_evidence_plugin import get_evidence_collector

def test_with_evidence():
    collector = get_evidence_collector()
    if collector:
        collector.add_receipt({
            "receipt_id": "receipt-123",
            "operation": "classification",
            "tenant_id": "tenant-1",
        })
```

## Troubleshooting

### Markers not recognized
- Ensure `pyproject.toml` includes the marker definition
- Run `pytest --markers` to verify markers are registered

### Evidence packs not generated
- Check that `tests.pytest_evidence_plugin` is loaded: `pytest -p tests.pytest_evidence_plugin`
- Verify `artifacts/evidence/` directory exists and is writable

### CI stage fails
- Check Jenkins console output for specific test failures
- Review JUnit XML reports in Jenkins artifacts
- Verify evidence packs were generated (check `artifacts/evidence/`)

## Release Checklist

Before releasing, ensure:

- [ ] All mandatory marker suites pass: `pytest -m "dgp_regression and dgp_security and dgp_performance"`
- [ ] Evidence packs are generated and archived
- [ ] JUnit XML reports are available in Jenkins
- [ ] Coverage reports meet thresholds
- [ ] Risk→Test Matrix status is updated

