# Feature Development Blind Spots Tests

## Test Organization

This directory contains all tests for the Feature Development Blind Spots module.

### Structure

- `unit/` - Unit tests for services, repositories, models
- `integration/` - Integration tests for API endpoints and workflows
- `security/` - Security tests (authentication, authorization, tenant isolation)
- `performance/` - Performance tests (latency, throughput)
- `resilience/` - Resilience tests (circuit breakers, degradation modes)

### Running Tests

```bash
# Run all tests for this module
pytest tests/cloud_services/client_services/feature_development_blind_spots/

# Run specific test category
pytest tests/cloud_services/client_services/feature_development_blind_spots/unit/
pytest tests/cloud_services/client_services/feature_development_blind_spots/security/

# Run with markers
pytest -m unit tests/cloud_services/client_services/feature_development_blind_spots/
pytest -m security tests/cloud_services/client_services/feature_development_blind_spots/
```

### Test Framework

Tests can also be run using the test registry framework:

```bash
python tools/test_registry/test_runner.py --module feature-development-blind-spots
```
