# Shared Test Harness Implementation

## Overview

A reusable test harness package (`tests/shared_harness/`) that provides common fixtures and utilities for all ZeroUI modules (DG&P, Alerting, Budgeting, Deployment). This eliminates duplication and ensures consistent test patterns across modules.

## Structure

```
tests/shared_harness/
├── __init__.py              # Exports all harness components
├── tenants.py               # TenantFactory, TenantProfile, AttackerProfile
├── tokens.py                # IAMTokenFactory, IssuedToken
├── perf_runner.py           # PerfRunner, PerfScenario, PerfResult
├── evidence.py              # EvidencePackBuilder (compliance artifacts)
├── alerting_fixtures.py     # AlertFixtureFactory, AlertEvent
├── budgeting_fixtures.py    # BudgetFixtureFactory, BudgetFixture, RateLimitFixture
└── deployment_fixtures.py   # DeploymentFixtureFactory, EnvironmentConfig, DeploymentManifest
```

## Core Components

### 1. Tenant Factory (`tenants.py`)
- `TenantFactory.create()` - Generate deterministic tenant profiles
- `TenantFactory.create_pair()` - Get two tenants (A/B) for isolation tests
- `TenantFactory.create_attacker_profile()` - Synthetic attacker for security tests
- `TenantProfile.to_headers()` - Convert to API headers

### 2. IAM Token Factory (`tokens.py`)
- `IAMTokenFactory.issue_token()` - Mint signed tokens with roles/scopes
- `IAMTokenFactory.issue_admin_token()` - Admin-level tokens
- `IAMTokenFactory.issue_cross_tenant_token()` - Negative test tokens
- `IssuedToken.to_headers()` - Convert to Authorization headers

### 3. Performance Runner (`perf_runner.py`)
- `PerfRunner.run()` - Execute async scenarios under concurrency
- `PerfScenario` - Define workload (iterations, concurrency, latency budget)
- `PerfResult` - Captures p50/p95/p99 latencies, enforces PRD budgets

### 4. Evidence Pack Builder (`evidence.py`)
- `EvidencePackBuilder.add_receipt()` - Collect ERIS receipts
- `EvidencePackBuilder.add_config_snapshot()` - Capture policy/configs
- `EvidencePackBuilder.add_metrics()` - Include performance metrics
- `EvidencePackBuilder.build()` - Generate timestamped ZIP artifact

## Module-Specific Fixtures

### Alerting (`alerting_fixtures.py`)
- `AlertFixtureFactory.create_alert()` - Synthetic alert events
- `AlertFixtureFactory.create_alert_burst()` - Test deduplication
- `AlertFixtureFactory.create_quiet_hours_alert()` - Test suppression

### Budgeting (`budgeting_fixtures.py`)
- `BudgetFixtureFactory.create_budget()` - Budget configurations
- `BudgetFixtureFactory.create_overlapping_budgets()` - Test priority resolution
- `BudgetFixtureFactory.create_rate_limit()` - Rate limit configs

### Deployment (`deployment_fixtures.py`)
- `DeploymentFixtureFactory.create_environment_config()` - Environment configs
- `DeploymentFixtureFactory.create_deployment_manifest()` - Deployment manifests
- `DeploymentFixtureFactory.create_parity_matrix()` - Multi-environment parity

## Usage Example

```python
from tests.shared_harness import (
    TenantFactory,
    IAMTokenFactory,
    PerfRunner,
    PerfScenario,
    AlertFixtureFactory,
    EvidencePackBuilder,
)

def test_alerting_deduplication():
    tenant_factory = TenantFactory()
    alert_factory = AlertFixtureFactory()
    tenant = tenant_factory.create()
    
    # Create burst of alerts with same dedup_key
    alerts = alert_factory.create_alert_burst(tenant, count=10, dedup_key="same-key")
    
    # Verify deduplication reduces to single incident
    incidents = deduplicate_alerts(alerts)
    assert len(incidents) == 1

async def test_budget_latency_budget():
    perf_runner = PerfRunner()
    tenant_factory = TenantFactory()
    tenant = tenant_factory.create()
    
    async def check_budget():
        await budget_service.check_budget(tenant.tenant_id, "api_calls")
    
    scenario = PerfScenario(
        name="budget-check",
        iterations=100,
        concurrency=10,
        coroutine_factory=check_budget,
        latency_budget_ms=10.0,  # PRD requirement
    )
    
    results = await perf_runner.run([scenario])
    assert results[0].p95 <= 10.0
```

## Integration with Risk→Test Matrix

The harness directly supports the test requirements in `docs/testing/risk_test_matrix.md`:

- **Multi-tenant isolation**: `TenantFactory.create_pair()` + `IAMTokenFactory.issue_cross_tenant_token()`
- **Performance budgets**: `PerfRunner` enforces PRD latency caps
- **Evidence packs**: `EvidencePackBuilder` generates compliance artifacts
- **Module-specific scenarios**: Alert bursts, budget overlaps, deployment parity

## Next Steps

1. **Alerting**: Create test suites for deduplication, quiet hours, routing (using `AlertFixtureFactory`)
2. **Budgeting**: Create test suites for enforcement bypass, rate limit accuracy (using `BudgetFixtureFactory`)
3. **Deployment**: Create test suites for parity drift, rollback preconditions (using `DeploymentFixtureFactory`)
4. **CI Integration**: Wire evidence pack generation into CI/CD pipelines

## Status

✅ **Core harness**: Complete (tenants, tokens, perf, evidence)  
✅ **Module fixtures**: Complete (alerting, budgeting, deployment)  
⏳ **Test suites**: In progress (targeted suites for missing Risk→Test Matrix items)  
⏳ **CI integration**: Pending (evidence pack uploads, mandatory markers)

