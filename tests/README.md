# ZeroUI 2.0 Test Organization

## Overview

This directory contains all tests for the ZeroUI 2.0 project, organized into a scalable, maintainable structure.

---

## Test Organization Structure

### Cloud Services Tests

**Location**: `tests/cloud_services/`

All cloud service tests are organized by service category and module:

```
tests/cloud_services/
├── client_services/          # Client Services (company-owned, private data)
│   ├── integration_adapters/
│   ├── compliance_security_challenges/
│   └── [other client service modules...]
│
├── product_services/         # Product Services (ZeroUI-owned, cross-tenant)
│   ├── detection_engine_core/
│   ├── mmm_engine/
│   ├── signal_ingestion_normalization/
│   └── [other product service modules...]
│
└── shared_services/         # Shared Services (ZeroUI-owned, infrastructure)
    ├── identity_access_management/
    ├── key_management_service/
    ├── data_governance_privacy/
    └── [other shared service modules...]
```

### Module Test Structure

Each module follows this structure:

```
tests/cloud_services/{category}/{module_name}/
├── unit/                     # Unit tests (services, repositories, models)
├── integration/              # Integration tests (API endpoints, workflows)
├── security/                 # Security tests (authentication, authorization, tenant isolation)
├── performance/             # Performance tests (latency, throughput)
└── resilience/              # Resilience tests (circuit breakers, degradation modes)
```

### System-Level Tests

**Location**: `tests/system/`

System-level tests that validate cross-cutting concerns and platform functionality:

```
tests/system/
├── constitution/          # Constitution rule validation tests
├── validators/           # Pre/post-generation validators, receipt validators
└── enforcement/          # Enforcement flow and deterministic enforcement tests
```

### Infrastructure Tests

**Location**: `tests/infrastructure/`

Infrastructure and platform-level tests:

```
tests/infrastructure/
├── health/               # Health check and monitoring tests
├── api/                  # API service and endpoint tests
└── openapi/              # OpenAPI infrastructure service tests
```

### Service-Specific Test Directories

**Location**: `tests/` (root level)

Tests for services that have their own dedicated directories:

- **Constitution Positive/Negative Suite** (`tests/constitution_positive_negative/`): Table-driven positive/negative invariants for all 415 constitution rules using controlled mutations (designed to avoid overlap with existing constitution suites)
- **LLM Gateway Tests** (`tests/llm_gateway/`): LLM Gateway service tests
- **BDR Tests** (`tests/bdr/`): Backup & Disaster Recovery tests
- **CCCS Tests** (`tests/cccs/`): Cross-Cutting Concern Services tests
- **SIN Tests** (`tests/sin/`): Signal Ingestion Normalization tests (legacy)
- **Manual Tests** (`tests/manual/`): Manual test cases
- **Platform Tests** (`tests/platform/`): Platform-specific tests (TypeScript)
- **Shared Harness** (`tests/shared_harness/`): Shared test utilities and fixtures

---

## Running Tests

### Run All Cloud Service Tests

```bash
# Run all cloud service tests
pytest tests/cloud_services/

# Run with parallel execution
pytest tests/cloud_services/ -n auto
```

### Run Tests for Specific Module

```bash
# Run all tests for a module
pytest tests/cloud_services/shared_services/identity_access_management/

# Run specific test category
pytest tests/cloud_services/shared_services/identity_access_management/security/
pytest tests/cloud_services/shared_services/identity_access_management/unit/
```

### Run Tests with Markers

```bash
# Run unit tests
pytest tests/cloud_services/ -m unit

# Run security tests
pytest tests/cloud_services/ -m security

# Run performance tests
pytest tests/cloud_services/ -m performance
```

### Run System-Level Tests

```bash
# Run all system tests
pytest tests/system/

# Run constitution tests
pytest tests/system/constitution/

# Run validator tests
pytest tests/system/validators/

# Run enforcement tests
pytest tests/system/enforcement/
```

### Run Infrastructure Tests

```bash
# Run all infrastructure tests
pytest tests/infrastructure/

# Run health tests
pytest tests/infrastructure/health/

# Run API tests
pytest tests/infrastructure/api/
```

### Run Service-Specific Tests

```bash
# Run LLM Gateway tests
pytest tests/llm_gateway/

# Run BDR tests
pytest tests/bdr/

# Run CCCS tests
pytest tests/cccs/

# Run constitution positive/negative tests
pytest tests/constitution_positive_negative/
```

### Using Test Registry Framework

```bash
# Generate/update test manifest
python tools/test_registry/generate_manifest.py

# Run tests using test runner
python tools/test_registry/test_runner.py --marker unit --parallel
python tools/test_registry/test_runner.py --module identity-access-management
```

---

## Adding New Tests

### For Existing Modules

1. **Determine Test Category**: unit, integration, security, performance, or resilience
2. **Create Test File**: `tests/cloud_services/{category}/{module_name}/{test_category}/test_*.py`
3. **Follow Naming Convention**: `test_*.py` for test files
4. **Use Markers**: Add appropriate pytest markers (`@pytest.mark.unit`, etc.)

### For New Modules

1. **Create Module Directory**: `tests/cloud_services/{category}/{module_name}/`
2. **Create Test Category Directories**: unit, integration, security, performance, resilience
3. **Create conftest.py**: Module-specific fixtures
4. **Create README.md**: Module test documentation
5. **Add Tests**: Follow standard structure

**Tool**: Use `python tools/test_reorganization/create_structure.py` to create structure automatically.

---

## Test Categories

### Unit Tests (`unit/`)

- **Purpose**: Test individual functions, classes, modules in isolation
- **Scope**: Services, repositories, models, utilities
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: Mocked external dependencies

### Integration Tests (`integration/`)

- **Purpose**: Test component interactions
- **Scope**: API endpoints, workflows, service interactions
- **Speed**: Medium (1-10 seconds per test)
- **Dependencies**: May use test database, mocked external services

### Security Tests (`security/`)

- **Purpose**: Test security controls
- **Scope**: Authentication, authorization, tenant isolation, data protection
- **Speed**: Medium (1-10 seconds per test)
- **Dependencies**: May use test IAM, mocked security services

### Performance Tests (`performance/`)

- **Purpose**: Test performance characteristics
- **Scope**: Latency, throughput, resource usage
- **Speed**: Slow (10+ seconds per test)
- **Dependencies**: May use performance test tools, load generators

### Resilience Tests (`resilience/`)

- **Purpose**: Test system resilience
- **Scope**: Circuit breakers, degradation modes, failure handling
- **Speed**: Medium-Slow (5-30 seconds per test)
- **Dependencies**: May simulate failures, test recovery

---

## Test Markers

Tests use pytest markers for categorization:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.slow` - Slow tests (opt-in only)

Module-specific markers:
- `@pytest.mark.dgp_regression` - DG&P regression tests
- `@pytest.mark.dgp_security` - DG&P security tests
- `@pytest.mark.alerting_regression` - Alerting regression tests
- etc.

---

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Deterministic**: Tests should produce consistent results
3. **Fast**: Unit tests should be fast (< 1 second)
4. **Clear Names**: Test names should clearly describe what they test
5. **Use Fixtures**: Share common setup via pytest fixtures
6. **Mock External Dependencies**: Don't rely on external services
7. **Follow Structure**: Place tests in appropriate category directories

---

## Migration Notes

**Migration Date**: 2025-01-27

**Migrated**: 154 test files from old locations to new structure

**Old Locations** (removed):
- `src/cloud_services/*/tests/` directories
- `src/cloud_services/*/__tests__/` directories

**New Location**: `tests/cloud_services/{category}/{module}/{test_type}/`

---

## Related Documentation

- `TEST_REORGANIZATION_STRATEGY.md` - Test reorganization strategy
- `TEST_REORGANIZATION_IMPLEMENTATION_PLAN.md` - Implementation plan
- `TEST_MIGRATION_EXECUTION_REPORT.md` - Migration execution report
- `tools/test_reorganization/README.md` - Migration tools documentation

---

**Last Updated**: 2025-01-27  
**Status**: ✅ **REORGANIZED FOR MAINTAINABILITY**

## Recent Reorganization (2025-01-27)

**Service Tests Moved to Cloud Services**:
- IAM tests → `cloud_services/shared_services/identity_access_management/`
- KMS tests → `cloud_services/shared_services/key_management_service/`
- Configuration Policy Management tests → `cloud_services/shared_services/configuration_policy_management/`
- Data Governance Privacy tests → `cloud_services/shared_services/data_governance_privacy/`
- Contracts Schema Registry tests → `cloud_services/shared_services/contracts_schema_registry/`
- Ollama AI Agent tests → `cloud_services/shared_services/ollama_ai_agent/`

**System Tests Organized**:
- Constitution tests → `system/constitution/`
- Validator tests → `system/validators/`
- Enforcement tests → `system/enforcement/`

**Infrastructure Tests Organized**:
- Health tests → `infrastructure/health/`
- API tests → `infrastructure/api/`
- OpenAPI tests → `infrastructure/openapi/`
