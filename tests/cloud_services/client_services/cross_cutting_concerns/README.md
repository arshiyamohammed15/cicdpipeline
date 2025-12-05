# Cross Cutting Concerns Tests

## Test Organization

This directory contains all tests for the Cross Cutting Concerns module.

### Structure

- `unit/` - Unit tests for services, repositories, models
- `integration/` - Integration tests for API endpoints and workflows
- `security/` - Security tests (authentication, authorization, tenant isolation)
- `performance/` - Performance tests (latency, throughput)
- `resilience/` - Resilience tests (circuit breakers, degradation modes)

### Running Tests

```bash
# Run all tests for this module
pytest tests/cloud_services/client_services/cross_cutting_concerns/

# Run specific test category
pytest tests/cloud_services/client_services/cross_cutting_concerns/unit/
pytest tests/cloud_services/client_services/cross_cutting_concerns/security/

# Run with markers
pytest -m unit tests/cloud_services/client_services/cross_cutting_concerns/
pytest -m security tests/cloud_services/client_services/cross_cutting_concerns/
```

### Test Framework

Tests can also be run using the test registry framework:

```bash
python tools/test_registry/test_runner.py --module cross-cutting-concerns
```
