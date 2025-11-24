# Rule Category to Validator and Test Mapping

## Overview

This document provides a comprehensive mapping of rule categories to their corresponding validators and test files. This mapping ensures developers can quickly locate the validator implementation and associated tests for any rule category.

## Mapping Structure

Each rule category maps to:
1. **Validator Module**: Python validator class in `validator/rules/`
2. **Config File**: JSON configuration in `config/rules/`
3. **Test Files**: Test suites that validate the category
4. **Rule Numbers**: Range of rules covered by the category

---

## Complete Category Mapping

### 1. Basic Work (`basic_work`)

**Validator**: `validator/rules/basic_work.py` → `BasicWorkValidator`  
**Config**: `config/rules/basic_work.json`  
**Rules**: 4, 5, 10, 13, 20  
**Test Files**:
- `tests/test_constitution_all_files.py` (category coverage)
- `tests/test_constitution_comprehensive_runner.py` (comprehensive tests)
- `tests/test_master_generic_rules_all.py` (rule-specific tests)

**Validator Initialization**:
```python
# In validator/optimized_core.py
("basic_work", "rules.basic_work", "BasicWorkValidator")
```

---

### 2. Requirements & Specifications (`requirements`)

**Validator**: `validator/rules/requirements.py` → `RequirementsValidator`  
**Config**: `config/rules/requirements.json`  
**Rules**: 1, 2  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/test_constitution_comprehensive_runner.py`

**Validator Initialization**:
```python
("requirements", "rules.requirements", "RequirementsValidator")
```

---

### 3. Privacy & Security (`privacy_security`)

**Validator**: `validator/rules/privacy.py` → `PrivacyValidator`  
**Config**: `config/rules/privacy_security.json`  
**Rules**: 3, 11, 12, 27, 36  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/test_data_governance_privacy_*.py` (comprehensive suite)
- `tests/privacy_imports.py`

**Validator Initialization**:
```python
("privacy_security", "rules.privacy", "PrivacyValidator")
```

---

### 4. Performance (`performance`)

**Validator**: `validator/rules/performance.py` → `PerformanceValidator`  
**Config**: `config/rules/performance.json`  
**Rules**: 8, 67  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/test_constitution_comprehensive_runner.py`

**Validator Initialization**:
```python
("performance", "rules.performance", "PerformanceValidator")
```

---

### 5. Architecture (`architecture`)

**Validator**: `validator/rules/architecture.py` → `ArchitectureValidator`  
**Config**: `config/rules/architecture.json`  
**Rules**: 19, 21, 23, 24, 28  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/test_architecture_artifacts_validation.py`

**Validator Initialization**:
```python
("architecture", "rules.architecture", "ArchitectureValidator")
```

---

### 6. System Design (`system_design`)

**Validator**: `validator/rules/system_design.py` → `SystemDesignValidator`  
**Config**: `config/rules/system_design.json`  
**Rules**: 22, 25, 26, 29, 30, 31, 32  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/test_constitution_comprehensive_runner.py`

**Validator Initialization**:
```python
("system_design", "rules.system_design", "SystemDesignValidator")
```

---

### 7. Problem Solving (`problem_solving`)

**Validator**: `validator/rules/problem_solving.py` → `ProblemSolvingValidator`  
**Config**: `config/rules/problem_solving.json`  
**Rules**: 33, 34, 35, 37, 38, 39, 41  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/test_constitution_comprehensive_runner.py`

**Validator Initialization**:
```python
("problem_solving", "rules.problem_solving", "ProblemSolvingValidator")
```

---

### 8. Platform (`platform`)

**Validator**: `validator/rules/platform.py` → `PlatformValidator`  
**Config**: `config/rules/platform.json`  
**Rules**: 42-51  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/platform/` (platform-specific tests)

**Validator Initialization**:
```python
("platform", "rules.platform", "PlatformValidator")
```

---

### 9. Teamwork (`teamwork`)

**Validator**: `validator/rules/teamwork.py` → `TeamworkValidator`  
**Config**: `config/rules/teamwork.json`  
**Rules**: 52-77 (excluding some gaps)  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/test_constitution_comprehensive_runner.py`

**Validator Initialization**:
```python
("teamwork", "rules.teamwork", "TeamworkValidator")
```

---

### 10. Code Review (`code_review`)

**Validator**: `validator/rules/code_review.py` → `CodeReviewValidator`  
**Config**: `config/rules/code_review.json`  
**Rules**: Various  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/test_cursor_testing_rules.py` (testing rules)

**Validator Initialization**:
```python
("code_review", "rules.code_review", "CodeReviewValidator")
```

---

### 11. Coding Standards (`coding_standards`)

**Validator**: `validator/rules/coding_standards.py` → `CodingStandardsValidator`  
**Config**: `config/rules/coding_standards.json`  
**Rules**: Various  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/test_constitution_comprehensive_runner.py`

**Validator Initialization**:
```python
("coding_standards", "rules.coding_standards", "CodingStandardsValidator")
```

---

### 12. Comments (`comments`)

**Validator**: `validator/rules/comments.py` → `CommentsValidator`  
**Config**: `config/rules/comments.json`  
**Rules**: Various  
**Test Files**:
- `tests/test_constitution_all_files.py` (includes COMMENTS RULES.json)
- `tests/test_constitution_comprehensive_runner.py`

**Validator Initialization**:
```python
("comments", "rules.comments", "CommentsValidator")
```

---

### 13. Folder Standards (`folder_standards`)

**Validator**: `validator/rules/folder_standards.py` → `FolderStandardsValidator`  
**Config**: `config/rules/folder_standards.json`  
**Rules**: Various  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/test_constitution_comprehensive_runner.py`

**Validator Initialization**:
```python
("folder_standards", "rules.folder_standards", "FolderStandardsValidator")
```

---

### 14. Logging (`logging`)

**Validator**: `validator/rules/logging.py` → `LoggingValidator`  
**Config**: `config/rules/logging.json`  
**Rules**: Various (includes LOGGING & TROUBLESHOOTING RULES.json)  
**Test Files**:
- `tests/test_constitution_all_files.py` (includes LOGGING & TROUBLESHOOTING RULES.json)
- `tests/test_logging_config.py`
- `tests/test_constitution_comprehensive_runner.py`

**Validator Initialization**:
```python
("logging", "rules.logging", "LoggingValidator")
```

---

### 15. Exception Handling (`exception_handling`)

**Validator**: `validator/rules/exception_handling.py` → `ExceptionHandlingValidator`  
**Config**: `config/rules/exception_handling.json` (if exists)  
**Rules**: 150-181 (31 rules)  
**Test Files**:
- `tests/test_constitution_all_files.py` (constitution rule tests)
- `tests/test_constitution_comprehensive_runner.py` (comprehensive tests)
- **Note**: Test directories `config/constitution/tests/test_exception_handling/` are referenced in README.md but may not exist yet. Use general constitution tests above.

**Validator Initialization**:
```python
("exception_handling", "rules.exception_handling", "ExceptionHandlingValidator")
```

**Validator Methods** (31 rules):
- `R150`: `_validate_prevent_first`
- `R151`: `_validate_error_codes`
- `R152`: `_validate_wrap_chain`
- `R153`: `_validate_central_handler`
- `R154`: `_validate_friendly_detailed`
- `R155`: `_validate_no_silent_catches`
- `R156`: `_validate_add_context`
- `R157`: `_validate_cleanup_always`
- `R158`: `_validate_recovery_patterns`
- `R160`: `_validate_onboarding`
- `R161`: `_validate_timeouts`
- `R162`: `_validate_retries_backoff`
- `R163`: `_validate_no_retry_nonretriables`
- `R164`: `_validate_idempotency`
- `R165`: `_validate_http_exit_mapping`
- `R166`: `_validate_message_catalog`
- `R167`: `_validate_ui_behavior`
- `R168`: `_validate_structured_logs`
- `R169`: `_validate_correlation`
- `R170`: `_validate_privacy_secrets`
- `R171`: `_validate_failure_paths`
- `R172`: `_validate_contracts_docs`
- `R173`: `_validate_consistency`
- `R174`: `_validate_safe_defaults`
- `R175`: `_validate_ai_transparency`
- `R176`: `_validate_ai_sandbox`
- `R177`: `_validate_ai_learning`
- `R178`: `_validate_ai_thresholds`
- `R179`: `_validate_graceful_degradation`
- `R180`: `_validate_state_recovery`
- `R181`: `_validate_feature_flags`

---

### 16. TypeScript (`typescript`)

**Validator**: `validator/rules/typescript.py` → `TypeScriptValidator`  
**Config**: `config/rules/typescript.json` (if exists)  
**Rules**: 182-215 (34 rules)  
**Test Files**:
- `tests/test_constitution_all_files.py` (constitution rule tests)
- `tests/test_constitution_comprehensive_runner.py` (comprehensive tests)
- **Note**: Test directories `config/constitution/tests/test_typescript_rules/` are referenced in README.md but may not exist yet. Use general constitution tests above.

**Validator Initialization**:
```python
("typescript", "rules.typescript", "TypeScriptValidator")
```

**Validator Methods** (34 rules):
- `R182`: `_validate_no_any_in_committed_code`
- `R183`: `_validate_handle_null_undefined`
- `R184`: `_validate_small_clear_functions`
- `R185`: `_validate_consistent_naming`
- `R186`: `_validate_clear_shape_strategy`
- `R187`: `_validate_let_compiler_infer`
- `R188`: `_validate_keep_imports_clean`
- `R189`: `_validate_describe_the_shape`
- `R190`: `_validate_union_narrowing`
- `R191`: `_validate_readonly_by_default`
- `R192`: `_validate_discriminated_unions`
- `R193`: `_validate_utility_types_not_duplicates`
- `R194`: `_validate_generics_but_simple`
- `R195`: `_validate_no_unhandled_promises`
- `R196`: `_validate_timeouts_cancel`
- `R197`: `_validate_friendly_errors_at_edges`
- `R198`: `_validate_map_errors_to_codes`
- `R199`: `_validate_retries_are_limited`
- `R200`: `_validate_one_source_of_truth`
- `R201`: `_validate_folder_layout`
- `R202`: `_validate_paths_aliases`
- `R203`: `_validate_modern_output_targets`
- `R204`: `_validate_lint_format`
- `R205`: `_validate_type_check_in_ci`
- `R206`: `_validate_tests_for_new_behavior`
- `R207`: `_validate_comments_in_simple_english`
- `R208`: `_validate_no_secrets_in_code_or_logs`
- `R209`: `_validate_validate_untrusted_inputs_at_runtime`
- `R210`: `_validate_keep_the_ui_responsive`
- `R211`: `_validate_review_ai_code_thoroughly`
- `R212`: `_validate_monitor_bundle_impact`
- `R213`: `_validate_quality_dependencies`
- `R214`: `_validate_test_type_boundaries`
- `R215`: `_validate_gradual_migration_strategy`

---

### 17. Storage Governance (`storage_governance`)

**Validator**: `validator/rules/storage_governance.py` → `StorageGovernanceValidator`  
**Config**: `config/rules/storage_governance.json`  
**Rules**: 216-228 (13 rules)  
**Test Files**:
- `tests/bdr/test_storage.py` (BDR storage tests)
- `tests/cccs/test_redaction.py` (redaction tests)
- `src/edge-agent/shared/storage/__tests__/*.spec.ts` (TypeScript/Edge Agent tests)
- `storage-scripts/tests/test-*.ps1` (PowerShell scaffold tests)

**Validator Initialization**:
```python
("storage_governance", "rules.storage_governance", "StorageGovernanceValidator")
```

**Validator Methods** (13 rules):
- `R216`: `_validate_name_casing` (kebab-case enforcement)
- `R217`: `_validate_no_code_pii` (no source code/PII in stores)
- `R218`: `_validate_no_secrets` (no secrets/private keys on disk)
- `R219`: `_validate_jsonl_receipts` (JSONL, signed, append-only)
- `R220`: `_validate_time_partitions` (UTC dt=YYYY-MM-DD format)
- `R221`: `_validate_policy_signatures` (policy snapshots must be signed)
- `R222`: `_validate_dual_storage` (JSONL authority, DB mirrors)
- `R223`: `_validate_path_resolution` (ZU_ROOT environment variable)
- `R224`: `_validate_receipts_validation` (receipts validation)
- `R225`: `_validate_evidence_watermarks` (per-consumer watermarks)
- `R226`: `_validate_rfc_fallback` (UNCLASSIFIED__slug pattern)
- `R227`: `_validate_observability_partitions` (dt= partitions for observability)
- `R228`: `_validate_laptop_receipts_partitioning` (YYYY/MM partitioning)

**Related Files**:
- `storage-scripts/folder-business-rules.md` (authoritative specification v1.1)
- `storage-scripts/INTEGRATION.md` (integration documentation)
- `src/edge-agent/shared/storage/README.md` (Edge Agent storage module)

---

### 18. API Contracts (`api_contracts`)

**Validator**: `validator/rules/api_contracts.py` → `APIContractsValidator`  
**Config**: `config/rules/api_contracts.json`  
**Rules**: Various  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/contracts/` (contract test suite)
- `tests/test_contracts_schema_registry*.py`

**Validator Initialization**:
```python
("api_contracts", "rules.api_contracts", "APIContractsValidator")
```

---

### 19. Code Quality (`code_quality`)

**Validator**: `validator/rules/quality.py` → `QualityValidator`  
**Config**: `config/rules/code_quality.json`  
**Rules**: 15, 18, 68  
**Test Files**:
- `tests/test_constitution_all_files.py`
- `tests/test_constitution_comprehensive_runner.py`

**Validator Initialization**:
```python
("code_quality", "rules.quality", "QualityValidator")
```

---

## Validator Registration Flow

All validators are registered in `validator/optimized_core.py` in the `_initialize_rule_processors()` method:

```python
mapping = [
    ("category_name", "rules.module_name", "ValidatorClassName"),
    # ... all categories listed above
]

for category, module_path, class_name in mapping:
    module = __import__(f"validator.{module_path}", fromlist=[class_name])
    validator_class = getattr(module, class_name)
    processors[category] = validator_class(rule_config)
```

## Configuration Loading

Rule configurations are loaded from `config/rules/*.json` files via `config/enhanced_config_manager.py`:

```python
def get_rule_config(self, category: str) -> Dict[str, Any]:
    """Load rule configuration for a category."""
    config_file = self.config_dir / "rules" / f"{category}.json"
    # ... load and return JSON
```

## Test Discovery

Tests are organized by:
1. **Category-based**: Tests in `tests/test_constitution_*.py` cover multiple categories
2. **Rule-specific**: Tests in `config/constitution/tests/test_*/` cover specific rule ranges
3. **Integration**: Tests in `tests/cccs/`, `tests/bdr/`, etc. test cross-cutting concerns
4. **Edge Agent**: TypeScript tests in `src/edge-agent/shared/storage/__tests__/`

## Usage Examples

### Finding Validator for a Category

```python
from validator.optimized_core import OptimizedConstitutionValidator

validator = OptimizedConstitutionValidator()
processor = validator.processors.get("exception_handling")
# Returns: ExceptionHandlingValidator instance
```

### Finding Tests for a Category

```bash
# Run all tests for exception handling
python -m pytest tests -k "exception_handling" -v

# Run TypeScript rule tests
python -m pytest config/constitution/tests/test_typescript_rules/ -v

# Run storage governance tests
python -m pytest tests/bdr/test_storage.py -v
```

### Checking Rule Coverage

```python
from config.enhanced_config_manager import EnhancedConfigManager

manager = EnhancedConfigManager()
rules = manager.get_rules_for_category("exception_handling")
# Returns: [150, 151, 152, ..., 181]
```

## Summary Table

| Category | Validator Class | Config File | Rule Range | Test Location |
|----------|----------------|-------------|------------|---------------|
| basic_work | BasicWorkValidator | basic_work.json | 4,5,10,13,20 | tests/test_constitution_*.py |
| requirements | RequirementsValidator | requirements.json | 1,2 | tests/test_constitution_*.py |
| privacy_security | PrivacyValidator | privacy_security.json | 3,11,12,27,36 | tests/test_data_governance_privacy_*.py |
| performance | PerformanceValidator | performance.json | 8,67 | tests/test_constitution_*.py |
| architecture | ArchitectureValidator | architecture.json | 19,21,23,24,28 | tests/test_architecture_artifacts_validation.py |
| system_design | SystemDesignValidator | system_design.json | 22,25,26,29,30,31,32 | tests/test_constitution_*.py |
| problem_solving | ProblemSolvingValidator | problem_solving.json | 33,34,35,37,38,39,41 | tests/test_constitution_*.py |
| platform | PlatformValidator | platform.json | 42-51 | tests/platform/ |
| teamwork | TeamworkValidator | teamwork.json | 52-77 | tests/test_constitution_*.py |
| code_review | CodeReviewValidator | code_review.json | Various | tests/test_cursor_testing_rules.py |
| coding_standards | CodingStandardsValidator | coding_standards.json | Various | tests/test_constitution_*.py |
| comments | CommentsValidator | comments.json | Various | tests/test_constitution_*.py |
| folder_standards | FolderStandardsValidator | folder_standards.json | Various | tests/test_constitution_*.py |
| logging | LoggingValidator | logging.json | Various | tests/test_logging_config.py |
| exception_handling | ExceptionHandlingValidator | (N/A) | 150-181 | config/constitution/tests/test_exception_handling/ |
| typescript | TypeScriptValidator | (N/A) | 182-215 | config/constitution/tests/test_typescript_rules/ |
| storage_governance | StorageGovernanceValidator | storage_governance.json | 216-228 | tests/bdr/test_storage.py, src/edge-agent/... |
| api_contracts | APIContractsValidator | api_contracts.json | Various | tests/contracts/ |
| code_quality | QualityValidator | code_quality.json | 15,18,68 | tests/test_constitution_*.py |

---

**Last Updated**: 2025-01-XX  
**Maintained By**: ZeroUI 2.0 Constitution Team  
**Source of Truth**: `validator/optimized_core.py`, `config/rules/*.json`, `docs/constitution/*.json`

