# Legacy Systems Safety Tests

## Test Organization

This directory contains all tests for the Legacy Systems Safety module.

### Structure

- `unit/` - Unit tests for services, repositories, models
- `integration/` - Integration tests for API endpoints and workflows
- `security/` - Security tests (authentication, authorization, tenant isolation)
- `performance/` - Performance tests (latency, throughput)
- `resilience/` - Resilience tests (circuit breakers, degradation modes)

### Running Tests

```bash
# Run all tests for this module
pytest tests/cloud_services/client_services/legacy_systems_safety/

# Run specific test category
pytest tests/cloud_services/client_services/legacy_systems_safety/unit/
pytest tests/cloud_services/client_services/legacy_systems_safety/security/

# Run with markers
pytest -m unit tests/cloud_services/client_services/legacy_systems_safety/
pytest -m security tests/cloud_services/client_services/legacy_systems_safety/
```

### Test Framework

Tests can also be run using the test registry framework:

```bash
python tools/test_registry/test_runner.py --module legacy-systems-safety
```
