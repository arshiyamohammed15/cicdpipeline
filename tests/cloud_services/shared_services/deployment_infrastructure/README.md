# Deployment Infrastructure Tests

## Test Organization

This directory contains all tests for the Deployment Infrastructure module.

### Structure

- `unit/` - Unit tests for services, repositories, models
- `integration/` - Integration tests for API endpoints and workflows
- `security/` - Security tests (authentication, authorization, tenant isolation)
- `performance/` - Performance tests (latency, throughput)
- `resilience/` - Resilience tests (circuit breakers, degradation modes)

### Running Tests

```bash
# Run all tests for this module
pytest tests/cloud_services/shared_services/deployment_infrastructure/

# Run specific test category
pytest tests/cloud_services/shared_services/deployment_infrastructure/unit/
pytest tests/cloud_services/shared_services/deployment_infrastructure/security/

# Run with markers
pytest -m unit tests/cloud_services/shared_services/deployment_infrastructure/
pytest -m security tests/cloud_services/shared_services/deployment_infrastructure/
```

### Test Framework

Tests can also be run using the test registry framework:

```bash
python tools/test_registry/test_runner.py --module deployment-infrastructure
```
