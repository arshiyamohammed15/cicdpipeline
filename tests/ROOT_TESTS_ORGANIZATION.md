# Root-Level Tests Organization

## Overview

Tests in the root `tests/` directory that don't belong to specific cloud service modules.

**Total Root-Level Test Files**: 46 files

---

## Test Categories

### 1. Validator Tests (`tests/test_*.py`)

**Purpose**: System-level tests for the validator/constitution system

**Files**:
- `test_constitution_*.py` - Constitution rules validation
- `test_rule_*.py` - Rule validation logic
- `test_pre_implementation_*.py` - Pre-implementation hooks
- `test_post_generation_*.py` - Post-generation validation
- `test_enforcement_*.py` - Enforcement flow tests
- `test_deterministic_*.py` - Deterministic enforcement tests

**Organization**: Keep in root `tests/` directory (system-level, not module-specific)

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

### 6. Other Test Directories

- **`tests/manual/`**: Manual test cases
- **`tests/health_reliability_monitoring/`**: Health monitoring tests (may need migration)
- **`tests/mmm_engine/`**: MMM Engine tests (may need migration)
- **`tests/platform/`**: Platform tests
- **`tests/shared_harness/`**: Shared test utilities
- **`tests/vscode-extension/`**: VS Code Extension tests (TypeScript)

---

## Organization Strategy

### Keep in Root `tests/` Directory

**Reason**: System-level or cross-cutting tests

1. **Validator Tests** (`test_*.py`): System-level constitution/rule validation
2. **Service-Specific Directories**: Keep organized by service (`llm_gateway/`, `bdr/`, `cccs/`, etc.)

### Potential Migrations

**Consider Migrating**:
- `tests/health_reliability_monitoring/` → `tests/cloud_services/shared_services/health_reliability_monitoring/`
- `tests/mmm_engine/` → `tests/cloud_services/product_services/mmm_engine/`

**Keep As-Is**:
- Validator tests (system-level)
- LLM Gateway tests (service-specific directory)
- BDR tests (service-specific directory)
- CCCS tests (service-specific directory)
- Manual tests (manual test cases)
- VS Code Extension tests (TypeScript, different structure)

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

### Running Root-Level Tests

```bash
# Run validator tests
pytest tests/test_constitution*.py
pytest tests/test_rule*.py

# Run LLM Gateway tests
pytest tests/llm_gateway/

# Run BDR tests
pytest tests/bdr/

# Run CCCS tests
pytest tests/cccs/

# Run all root-level tests
pytest tests/ -k "not cloud_services"
```

---

**Status**: ✅ **ORGANIZED AND DOCUMENTED**

**Last Updated**: 2025-01-27

