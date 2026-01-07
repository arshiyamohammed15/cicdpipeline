# Test Marker Standardization Strategy

**Date**: 2026-01-05  
**Purpose**: Systematically add pytest markers to ~2,265 unmarked test cases  
**Approach**: Pattern-based, verifiable, no assumptions

---

## Overview

This document defines the strategy for standardizing pytest markers across the ZeroUI test suite. The goal is to add appropriate markers to all test cases based on **verifiable patterns only** - no assumptions or inferences.

---

## Marker Categories

### Base Markers (from pyproject.toml)

1. **`@pytest.mark.unit`** - Unit tests (fast, pure functions)
2. **`@pytest.mark.integration`** - Integration tests (I/O, process boundaries)
3. **`@pytest.mark.performance`** - Performance tests
4. **`@pytest.mark.security`** - Security tests
5. **`@pytest.mark.smoke`** - Smoke tests (wiring sanity)
6. **`@pytest.mark.constitution`** - Constitution rule validation tests
7. **`@pytest.mark.slow`** - Slow tests (opt-in only)

### Module-Specific Markers

#### Data Governance & Privacy (M22)
- `@pytest.mark.dgp_regression`
- `@pytest.mark.dgp_security`
- `@pytest.mark.dgp_performance`
- `@pytest.mark.dgp_compliance`

#### Alerting & Notification Service (EPC-4)
- `@pytest.mark.alerting_regression`
- `@pytest.mark.alerting_security`
- `@pytest.mark.alerting_performance`
- `@pytest.mark.alerting_integration`

#### Budgeting, Rate-Limiting & Cost Observability (M35)
- `@pytest.mark.budgeting_regression`
- `@pytest.mark.budgeting_security`
- `@pytest.mark.budgeting_performance`

#### Deployment & Infrastructure (EPC-8)
- `@pytest.mark.deployment_regression`
- `@pytest.mark.deployment_security`
- `@pytest.mark.deployment_integration`

#### LLM Gateway
- `@pytest.mark.llm_gateway_unit`
- `@pytest.mark.llm_gateway_integration`
- `@pytest.mark.llm_gateway_real_integration`

---

## Standardization Rules

### Rule 1: Path-Based Categorization (PRIMARY)

**VERIFIED PATTERN**: Directory structure determines marker type.

| Path Pattern | Marker(s) |
|--------------|-----------|
| `tests/**/unit/**/*.py` | `@pytest.mark.unit` |
| `tests/**/integration/**/*.py` | `@pytest.mark.integration` |
| `tests/**/performance/**/*.py` | `@pytest.mark.performance` |
| `tests/**/security/**/*.py` | `@pytest.mark.security` |
| `tests/**/resilience/**/*.py` | `@pytest.mark.integration` |
| `tests/**/constitution/**/*.py` | `@pytest.mark.constitution` |

**Examples**:
- `tests/cloud_services/shared_services/ollama_ai_agent/unit/test_services.py` → `@pytest.mark.unit`
- `tests/health_reliability_monitoring/integration/test_api.py` → `@pytest.mark.integration`
- `tests/cloud_services/shared_services/key_management_service/performance/test_kms_performance.py` → `@pytest.mark.performance`

### Rule 2: File Name Patterns

**VERIFIED PATTERN**: File name keywords determine additional markers.

| File Name Pattern | Additional Marker(s) |
|-------------------|---------------------|
| `*smoke*.py` | `@pytest.mark.smoke` + `@pytest.mark.unit` |
| `*e2e*.py` or `*end_to_end*.py` | `@pytest.mark.integration` |
| `*constitution*.py` | `@pytest.mark.constitution` |

**Examples**:
- `tests/platform_smoke/test_platform_smoke.py` → `@pytest.mark.smoke` + `@pytest.mark.unit`
- `tests/epc_audit/test_epc_e2e_golden_path.py` → `@pytest.mark.integration`

### Rule 3: Module-Specific Markers

**VERIFIED PATTERN**: Module name in path + category directory = module-specific marker.

| Module | Path Contains | Category | Marker |
|--------|---------------|----------|--------|
| `data_governance_privacy` | `/unit/` | unit | `@pytest.mark.unit` |
| `data_governance_privacy` | `/security/` | security | `@pytest.mark.dgp_security` + `@pytest.mark.security` |
| `data_governance_privacy` | `/performance/` | performance | `@pytest.mark.dgp_performance` + `@pytest.mark.performance` |
| `alerting_notification_service` | `/integration/` | integration | `@pytest.mark.alerting_integration` + `@pytest.mark.integration` |
| `llm_gateway` | `/unit/` | unit | `@pytest.mark.llm_gateway_unit` + `@pytest.mark.unit` |
| `llm_gateway` | `real_services` or `real_integration` | real_integration | `@pytest.mark.llm_gateway_real_integration` |

**Examples**:
- `tests/cloud_services/shared_services/data_governance_privacy/security/test_cross_tenant_isolation.py` → `@pytest.mark.dgp_security` + `@pytest.mark.security`
- `tests/llm_gateway/test_real_services_integration.py` → `@pytest.mark.llm_gateway_real_integration`

### Rule 4: Constitution Tests

**VERIFIED PATTERN**: Tests in constitution directories or with "constitution" in name.

| Pattern | Marker |
|---------|--------|
| `tests/config/constitution/**/*.py` | `@pytest.mark.constitution` |
| `tests/system/constitution/**/*.py` | `@pytest.mark.constitution` |
| `*constitution*.py` | `@pytest.mark.constitution` |

**Examples**:
- `tests/config/constitution/test_constitution_rules_json.py` → `@pytest.mark.constitution`
- `tests/system/constitution/test_constitution_all_files.py` → `@pytest.mark.constitution`

---

## Implementation Strategy

### Phase 1: Analysis (COMPLETE)

1. ✅ Count all test cases (2,543 Python, 82 TypeScript)
2. ✅ Identify unmarked tests (~2,265)
3. ✅ Document path patterns
4. ✅ Document file name patterns
5. ✅ Document module-specific patterns

### Phase 2: Standardization Script

**Script**: `tools/test_registry/standardize_markers_simple.py`

**Features**:
- Analyzes each test file
- Determines markers from verifiable patterns only
- Adds markers to test classes and functions
- Preserves existing markers
- Generates detailed report

**Usage**:
```bash
# Dry run (preview changes)
python tools/test_registry/standardize_markers_simple.py --dry-run

# Apply changes
python tools/test_registry/standardize_markers_simple.py
```

### Phase 3: Verification

After standardization:
1. Run test collection to verify markers are recognized
2. Verify no test cases lost markers
3. Verify all patterns were correctly applied
4. Generate final count report

---

## Marker Application Rules

### Test Classes

**Rule**: Add markers as class decorators.

```python
# BEFORE
class TestSchemaContractStructure:
    def test_contract_has_schema_pack_id(self, contract: dict):
        # Test implementation

# AFTER
@pytest.mark.unit
class TestSchemaContractStructure:
    def test_contract_has_schema_pack_id(self, contract: dict):
        # Test implementation
```

**Note**: Test methods in a class inherit class-level markers.

### Test Functions

**Rule**: Add markers as function decorators (only for top-level functions).

```python
# BEFORE
def test_json_manager_initialization(tmp_json_path):
    # Test implementation

# AFTER
@pytest.mark.unit
@pytest.mark.constitution
def test_json_manager_initialization(tmp_json_path):
    # Test implementation
```

**Note**: Functions inside test classes don't need individual markers if the class has markers.

### Multiple Markers

**Rule**: Apply all applicable markers.

```python
# Example: Smoke test in unit directory
@pytest.mark.smoke
@pytest.mark.unit
def test_platform_smoke():
    # Test implementation
```

---

## Edge Cases and Ambiguities

### Case 1: Tests in Root `tests/` Directory

**Pattern**: `tests/test_*.py` (not in subdirectories)

**Decision**: 
- If file name contains "smoke" → `@pytest.mark.smoke` + `@pytest.mark.unit`
- If file name contains "e2e" → `@pytest.mark.integration`
- Otherwise: **SKIP** (no clear pattern)

### Case 2: Tests in `tests/infrastructure/`

**Pattern**: `tests/infrastructure/**/*.py`

**Decision**:
- If in `tests/infrastructure/db/` → `@pytest.mark.unit` (database schema/contract tests are unit tests)
- If in `tests/infrastructure/*/integration/` → `@pytest.mark.integration`
- Otherwise: **SKIP** (no clear pattern)

### Case 3: Tests with Multiple Applicable Patterns

**Example**: `tests/cloud_services/shared_services/data_governance_privacy/security/test_cross_tenant_isolation.py`

**Decision**: Apply ALL applicable markers:
- `@pytest.mark.dgp_security` (module-specific)
- `@pytest.mark.security` (base marker)
- `@pytest.mark.unit` (if also in unit directory, but this one is in security)

### Case 4: Tests Already Having Some Markers

**Rule**: Only add missing markers, preserve existing ones.

```python
# BEFORE (has some markers)
@pytest.mark.unit
def test_something():
    # Test implementation

# AFTER (add missing markers if applicable)
@pytest.mark.unit
@pytest.mark.constitution  # Added if pattern matches
def test_something():
    # Test implementation
```

---

## Verification Checklist

After running the standardization script:

- [ ] All test files in `tests/**/unit/` have `@pytest.mark.unit`
- [ ] All test files in `tests/**/integration/` have `@pytest.mark.integration`
- [ ] All test files in `tests/**/performance/` have `@pytest.mark.performance`
- [ ] All test files in `tests/**/security/` have `@pytest.mark.security`
- [ ] All `*smoke*.py` files have `@pytest.mark.smoke`
- [ ] All `*e2e*.py` files have `@pytest.mark.integration`
- [ ] All constitution tests have `@pytest.mark.constitution`
- [ ] Module-specific markers applied correctly
- [ ] No existing markers were removed
- [ ] Test collection still works: `pytest --collect-only -q`

---

## Rollback Plan

If standardization causes issues:

1. **Git Revert**: All changes are in git, can be reverted
2. **Selective Revert**: Revert specific files if needed
3. **Manual Fix**: Fix specific markers manually

**Command**:
```bash
git diff tools/test_registry/standardize_markers_simple.py
git checkout -- <specific_file>  # Revert specific file
```

---

## Success Criteria

1. ✅ **100% Pattern Coverage**: All tests with clear patterns have markers
2. ✅ **Zero False Positives**: No incorrect markers added
3. ✅ **Preserved Existing**: All existing markers remain
4. ✅ **Test Collection Works**: `pytest --collect-only` succeeds
5. ✅ **CI/CD Compatible**: Markers work with existing CI/CD pipelines

---

## Next Steps

1. **Run Dry Run**: Preview changes without modifying files
2. **Review Report**: Check the generated report for accuracy
3. **Apply Changes**: Run script without `--dry-run` flag
4. **Verify**: Run test collection and verify markers
5. **Document**: Update test documentation with marker usage

---

**END OF STRATEGY DOCUMENT**
