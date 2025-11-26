# Real Service Integration Testing

This document explains how to run integration tests against actual backend services.

## Prerequisites

1. All backend services must be running and accessible:
   - IAM Service (EPC-1)
   - Policy Service (EPC-3/EPC-10)
   - Data Governance Service (EPC-2)
   - Budget Service (EPC-13)
   - ERIS Service
   - Alerting Service (EPC-4)

2. Services must expose health check endpoints at `/health` (or `/alerts` for Alerting)

## Configuration

### Environment Variables

Set `USE_REAL_SERVICES=true` to enable real service integration tests:

```bash
# Windows PowerShell
$env:USE_REAL_SERVICES="true"
npm run test:llm-gateway:real-services

# Linux/Mac
USE_REAL_SERVICES=true npm run test:llm-gateway:real-services
```

### Service URLs

Service URLs can be configured via environment variables (defaults shown):

```bash
IAM_SERVICE_URL=http://localhost:8001/iam/v1
POLICY_SERVICE_URL=http://localhost:8003
DATA_GOVERNANCE_SERVICE_URL=http://localhost:8002/privacy/v1
BUDGET_SERVICE_URL=http://localhost:8035
ERIS_SERVICE_URL=http://localhost:8007
ALERTING_SERVICE_URL=http://localhost:8004/v1
```

## Running Tests

### All Real Service Integration Tests

```bash
USE_REAL_SERVICES=true npm run test:llm-gateway:real-services
```

### Specific Test

```bash
USE_REAL_SERVICES=true pytest tests/llm_gateway/test_real_services_integration.py::test_real_services_benign_prompt_allowed -v
```

## Test Behavior

- **Automatic Health Checks**: Tests automatically check service health before running
- **Graceful Skipping**: If services are unavailable, tests are skipped (not failed)
- **Isolated Execution**: Each test uses a fresh service instance
- **Real HTTP Calls**: All tests make actual HTTP requests to backend services

## Test Coverage

The real service integration tests cover:

- **IT-LLM-01**: Benign prompt allowed through real stack
- **IT-LLM-02**: Adversarial prompt blocked by real safety pipeline
- **IT-LLM-03**: IAM validation failure handling
- **IT-LLM-04**: Budget enforcement
- **IT-LLM-05**: Data governance redaction
- **IT-LLM-06**: ERIS receipt emission
- **IT-LLM-07**: Policy snapshot caching

## Troubleshooting

### Services Not Available

If tests are skipped with "Real services not available", check:

1. All services are running
2. Health endpoints are accessible
3. Service URLs are correct
4. Network connectivity is working

### Test Failures

If tests fail:

1. Check service logs for errors
2. Verify service configurations match expected contracts
3. Ensure test data (corpus entries) are valid
4. Check IAM permissions for test actors

## CI Integration

In CI/CD pipelines:

- Real service tests are **optional** (won't fail builds if services unavailable)
- Use mocked integration tests (`test:llm-gateway:integration`) for standard CI runs
- Run real service tests in pre-production environments
- Set service URLs via CI environment variables

## See Also

- `docs/architecture/tests/LLM_Gateway_TestPlan.md` - Full test plan documentation
- `tests/llm_gateway/service_health.py` - Health check implementation
- `tests/llm_gateway/conftest.py` - Test fixtures and configuration

