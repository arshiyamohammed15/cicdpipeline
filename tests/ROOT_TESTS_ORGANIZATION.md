# Root-Level Tests Organization

## Overview

Tests in the root `tests/` directory that don't belong to specific cloud service modules.

**Note**: This document has been updated to reflect the reorganization completed on 2025-01-27. Service-specific tests have been moved to `cloud_services/`, system-level tests to `system/`, and infrastructure tests to `infrastructure/`.

---

## Test Categories

### 1. System-Level Tests (`tests/system/`)

**Purpose**: System-level tests for validators, constitution, and enforcement

**Structure**:
```
tests/system/
├── constitution/          # Constitution rule validation tests
│   ├── test_constitution_all_files.py
│   ├── test_constitution_comprehensive_runner.py
│   ├── test_constitution_coverage_analysis.py
│   ├── test_constitution_rule_semantics.py
│   ├── test_constitution_rule_specific_coverage.py
│   └── test_master_generic_rules_all.py
├── validators/            # Validator tests
│   ├── test_pre_implementation_artifacts.py
│   ├── test_pre_implementation_hooks_comprehensive.py
│   ├── test_post_generation_validator.py
│   ├── test_receipt_validator.py
│   └── test_receipt_invariants_end_to_end.py
├── enforcement/           # Enforcement flow tests
│   ├── test_enforcement_flow.py
│   └── test_deterministic_enforcement.py
├── test_architecture_artifacts_validation.py
└── test_cursor_testing_rules.py
```

**Constitution Positive/Negative Suite** (`tests/constitution_positive_negative/`): Table-driven positive/negative invariants for all 415 constitution rules using controlled mutations (designed to avoid overlap with existing suites)

### 2. LLM Gateway Tests (`tests/llm_gateway/`)

**Purpose**: Tests for LLM Gateway service

**Files**: 10 test files
- `test_clients_contracts.py`
- `test_incident_store_unit.py`
- `test_policy_refresh_integration.py`
- `test_provider_routing_unit.py`
- `test_real_services_integration.py`
- `test_routes_integration.py`
- `test_safety_pipeline_unit.py`
- `test_security_regression.py`
- `test_service_unit.py`

**Organization**: Keep in `tests/llm_gateway/` directory (service-specific)

### 3. BDR Tests (`tests/bdr/`)

**Purpose**: Backup & Disaster Recovery tests

**Files**: 12 test files
- `test_catalog.py`
- `test_dr_module.py`
- `test_engine.py`
- `test_models.py`
- `test_observability.py`
- `test_policy.py`
- `test_receipts.py`
- `test_scheduler.py`
- `test_security.py`
- `test_service_end_to_end.py`
- `test_storage.py`
- `test_verification.py`

**Organization**: Keep in `tests/bdr/` directory (service-specific)

### 4. CCCS Tests (`tests/cccs/`)

**Purpose**: Cross-Cutting Concern Services tests

**Files**: 10 test files
- `test_adapters.py`
- `test_e2e.py`
- `test_identity.py`
- `test_integration.py`
- `test_policy_and_config.py`
- `test_rate_limiter.py`
- `test_receipts.py`
- `test_redaction.py`
- `test_runtime.py`
- `test_wal_durability.py`

**Organization**: Keep in `tests/cccs/` directory (service-specific)

### 5. SIN Tests (`tests/sin/`)

**Purpose**: Signal Ingestion Normalization tests (legacy location)

**Files**: 22 test files
- Integration tests: `test_api_endpoints.py`, `test_dlq_workflows.py`, etc.
- Unit tests: `test_deduplication.py`, `test_normalization.py`, etc.

**Note**: Some SIN tests were migrated to `tests/cloud_services/product_services/signal_ingestion_normalization/`

**Organization**: 
- **Option 1**: Keep legacy tests in `tests/sin/` for backward compatibility
- **Option 2**: Migrate remaining tests to new structure
- **Recommendation**: Keep for now, migrate later if needed

### 6. Infrastructure Tests (`tests/infrastructure/`)

**Purpose**: Infrastructure and platform-level tests

**Structure**:
```
tests/infrastructure/
├── health/                # Health check and monitoring tests
│   ├── test_health.py
│   └── test_health_endpoints.py
├── api/                   # API service and endpoint tests
│   ├── test_api_endpoints.py
│   ├── test_api_service.py
│   └── test_api_service_end_to_end.py
├── openapi/               # OpenAPI infrastructure service tests
│   └── test_openapi_infrastructure_services.py
├── test_errors.py
├── test_integration.py
├── test_logging_config.py
└── test_service_integration_smoke.py
```

### 7. Other Test Directories

- **`tests/manual/`**: Manual test cases
- **`tests/health_reliability_monitoring/`**: Health monitoring tests (legacy, may need migration to cloud_services)
- **`tests/mmm_engine/`**: MMM Engine tests (legacy, may need migration to cloud_services)
- **`tests/platform/`**: Platform tests (TypeScript)
- **`tests/shared_harness/`**: Shared test utilities and fixtures
- **`tests/vscode-extension/`**: VS Code Extension tests (TypeScript)
- **`tests/contracts/`**: Contract validation tests

---

## Organization Strategy

### Service Tests → Cloud Services

**Moved to `tests/cloud_services/`**:
- IAM tests → `shared_services/identity_access_management/`
- KMS tests → `shared_services/key_management_service/`
- Configuration Policy Management tests → `shared_services/configuration_policy_management/`
- Data Governance Privacy tests → `shared_services/data_governance_privacy/`
- Contracts Schema Registry tests → `shared_services/contracts_schema_registry/`
- Ollama AI Agent tests → `shared_services/ollama_ai_agent/`

### System Tests → System Directory

**Moved to `tests/system/`**:
- Constitution tests → `system/constitution/`
- Validator tests → `system/validators/`
- Enforcement tests → `system/enforcement/`

### Infrastructure Tests → Infrastructure Directory

**Moved to `tests/infrastructure/`**:
- Health tests → `infrastructure/health/`
- API tests → `infrastructure/api/`
- OpenAPI tests → `infrastructure/openapi/`

### Keep As-Is

**Service-Specific Directories**:
- LLM Gateway tests (`tests/llm_gateway/`)
- BDR tests (`tests/bdr/`)
- CCCS tests (`tests/cccs/`)
- SIN tests (`tests/sin/`) - legacy
- Manual tests (`tests/manual/`)
- Platform tests (`tests/platform/`) - TypeScript
- VS Code Extension tests (`tests/vscode-extension/`) - TypeScript

### Potential Future Migrations

**Consider Migrating**:
- `tests/health_reliability_monitoring/` → `tests/cloud_services/shared_services/health_reliability_monitoring/`
- `tests/mmm_engine/` → `tests/cloud_services/product_services/mmm_engine/`
- `tests/sin/` → `tests/cloud_services/product_services/signal_ingestion_normalization/`

---

## Recommendations

### Immediate Actions

1. ✅ **Keep Current Organization**: Root-level tests are appropriately organized
2. ⏳ **Document Structure**: Update `tests/README.md` (done)
3. ⏳ **Consider Future Migrations**: Evaluate migrating `health_reliability_monitoring` and `mmm_engine` tests

### Future Considerations

1. **LLM Gateway**: Consider if LLM Gateway should be a cloud service module
2. **BDR**: Consider if BDR should be a cloud service module
3. **CCCS**: Consider if CCCS should be a cloud service module
4. **SIN Legacy**: Migrate remaining SIN tests to new structure

---

## Test Discovery

### Running Tests

```bash
# Run system tests
pytest tests/system/

# Run infrastructure tests
pytest tests/infrastructure/

# Run LLM Gateway tests
pytest tests/llm_gateway/

# Run BDR tests
pytest tests/bdr/

# Run CCCS tests
pytest tests/cccs/

# Run constitution positive/negative tests
pytest tests/constitution_positive_negative/
```

---

**Status**: ✅ **REORGANIZED FOR MAINTAINABILITY**

**Last Updated**: 2025-01-27

## Reorganization Summary (2025-01-27)

**Service Tests Moved**:
- ✅ IAM, KMS, Configuration Policy Management, Data Governance Privacy, Contracts Schema Registry, Ollama AI Agent → `cloud_services/shared_services/`

**System Tests Organized**:
- ✅ Constitution, validators, enforcement → `system/`

**Infrastructure Tests Organized**:
- ✅ Health, API, OpenAPI → `infrastructure/`

**Result**: Improved maintainability with clear separation of concerns and consistent organization patterns.

