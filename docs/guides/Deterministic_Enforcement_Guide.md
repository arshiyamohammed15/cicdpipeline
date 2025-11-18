# Deterministic Enforcement Guide

## Overview

This guide ensures that pre-implementation hooks enforce rules **deterministically, consistently, and repeatably**. The same prompt must always produce the same validation result, regardless of execution order, timing, or instance creation.

## Determinism Requirements

### 1. Rule Loading Determinism

**Requirement**: Rules must be loaded in the same order every time.

**Implementation**:
- JSON files are sorted by filename before loading
- Rules within files maintain their JSON order
- Disabled rules are consistently excluded

**Verification**:
```python
from validator.pre_implementation_hooks import ConstitutionRuleLoader

loader1 = ConstitutionRuleLoader()
loader2 = ConstitutionRuleLoader()

rules1 = [r.get('rule_id') for r in loader1.get_all_rules()]
rules2 = [r.get('rule_id') for r in loader2.get_all_rules()]

assert rules1 == rules2  # Must be identical
```

### 2. Validation Determinism

**Requirement**: Same prompt must produce same validation result every time.

**Implementation**:
- Rules are processed in consistent order
- Violations are sorted by rule_id for deterministic output
- No random or time-based logic
- Case-insensitive matching is consistent

**Verification**:
```python
from validator.pre_implementation_hooks import PreImplementationHookManager

manager = PreImplementationHookManager()
prompt = "create function with hardcoded password"

result1 = manager.validate_before_generation(prompt)
result2 = manager.validate_before_generation(prompt)
result3 = manager.validate_before_generation(prompt)

# All must be identical
assert result1['valid'] == result2['valid'] == result3['valid']
assert len(result1['violations']) == len(result2['violations']) == len(result3['violations'])
# Rule count should be consistent (from JSON files - single source of truth)
assert result1['total_rules_checked'] == result2['total_rules_checked'] == result3['total_rules_checked']
```

### 3. Consistency Requirements

**Requirement**: Results must be consistent across different instances and executions.

**Implementation**:
- No shared state between instances
- No global variables
- No mutable module-level state
- Each instance loads rules independently

**Verification**:
```python
from validator.pre_implementation_hooks import PreImplementationHookManager

manager1 = PreImplementationHookManager()
manager2 = PreImplementationHookManager()
manager3 = PreImplementationHookManager()

prompt = "test prompt"
result1 = manager1.validate_before_generation(prompt)
result2 = manager2.validate_before_generation(prompt)
result3 = manager3.validate_before_generation(prompt)

# All must produce identical results
assert result1 == result2 == result3
```

### 4. Repeatability Requirements

**Requirement**: Same input must produce same output across different runs.

**Implementation**:
- No time-based decisions
- No random number generation
- No external state dependencies
- Deterministic file loading order

## Current Implementation Analysis

### Deterministic Components

✅ **Rule Loading**:
- Files sorted by name: `sorted(list(self.constitution_dir.glob("*.json")))`
- Rules processed in JSON order
- Disabled rules consistently excluded

✅ **Validation**:
- Rules processed in fixed order
- Violations sorted by rule_id
- No random or time-based logic

✅ **State Management**:
- No global state
- Each instance is independent
- No shared mutable data

### Potential Issues Addressed

1. **File Loading Order** - Fixed by sorting files by name
2. **Violation Order** - Fixed by sorting violations by rule_id
3. **Case Sensitivity** - Consistent lowercase conversion
4. **Whitespace** - Consistent handling via strip()

## Testing Determinism

### Run Determinism Tests

```bash
python tests/test_deterministic_enforcement.py
```

### Manual Verification

```python
from validator.pre_implementation_hooks import PreImplementationHookManager

# Test 1: Same prompt, same result
manager = PreImplementationHookManager()
prompt = "create function with hardcoded password"

results = []
for _ in range(10):
    result = manager.validate_before_generation(prompt)
    results.append({
        'valid': result['valid'],
        'violations': len(result['violations']),
        'rules_checked': result['total_rules_checked']
    })

# All should be identical
assert len(set(str(r) for r in results)) == 1

# Test 2: Different instances, same result
manager1 = PreImplementationHookManager()
manager2 = PreImplementationHookManager()

result1 = manager1.validate_before_generation(prompt)
result2 = manager2.validate_before_generation(prompt)

assert result1['valid'] == result2['valid']
assert len(result1['violations']) == len(result2['violations'])
# Rule count should be consistent (from JSON files - single source of truth)
assert result1['total_rules_checked'] == result2['total_rules_checked']
```

## Enforcement Guarantees

### Guarantee 1: Deterministic Rule Loading

**What**: Rules are loaded in the same order every time.

**How**: Files are sorted by filename before processing.

**Test**: `test_file_loading_order`, `test_rule_ids_consistency`

### Guarantee 2: Deterministic Validation

**What**: Same prompt produces same validation result.

**How**: Rules processed in fixed order, violations sorted by rule_id.

**Test**: `test_same_prompt_same_result`, `test_violation_order_consistency`

### Guarantee 3: Consistent Behavior

**What**: Results are consistent across instances and executions.

**How**: No shared state, independent instances, deterministic logic.

**Test**: `test_isolation_between_instances`, `test_rule_processing_order`

### Guarantee 4: Repeatable Results

**What**: Same input produces same output across runs.

**How**: No time/random dependencies, deterministic file loading.

**Test**: `test_rule_count_consistency`, `test_empty_prompt_consistency`

## Implementation Checklist

- [x] JSON files sorted by filename before loading
- [x] Rules processed in consistent order
- [x] Violations sorted by rule_id
- [x] No global state or shared mutable data
- [x] No random or time-based logic
- [x] Case-insensitive matching is consistent
- [x] Whitespace handling is consistent
- [x] Each instance is independent
- [x] Determinism tests in place

## Code Quality Measures

### 1. Immutable Rule Data

Rules are loaded once and not modified:
```python
self.rules: List[Dict[str, Any]] = []  # Loaded once, never modified
```

### 2. No Global State

No module-level variables:
```python
# No global variables
# Each instance manages its own state
```

### 3. Deterministic Sorting

All collections are sorted for consistency:
```python
json_files = sorted(list(self.constitution_dir.glob("*.json")))
violations_sorted = sorted(violations, key=lambda v: (v.rule_id, v.message))
return sorted(list(categories))
```

### 4. Functional Approach

Validation logic is functional (no side effects):
```python
def validate_prompt(self, prompt: str, ...) -> List[Violation]:
    # Pure function - same input always produces same output
    violations = []
    # ... deterministic processing ...
    return violations
```

## Verification Commands

### Quick Verification

```bash
python tests/verify_hooks_working.py
```

### Determinism Tests

```bash
python tests/test_deterministic_enforcement.py
```

### Comprehensive Tests

```bash
python tests/test_pre_implementation_hooks_comprehensive.py
```

## Expected Test Results

All determinism tests should pass:
- ✅ Rule loading order is deterministic
- ✅ Rule count is consistent
- ✅ Rule IDs are consistent
- ✅ Same prompt produces same result
- ✅ Violation order is consistent
- ✅ Rules checked count is consistent
- ✅ Different instances produce same results
- ✅ Rule processing order is consistent

## Troubleshooting Non-Determinism

### Issue: Different Results on Each Run

**Check**:
1. File loading order - ensure files are sorted
2. Violation order - ensure violations are sorted
3. Set operations - ensure sets are converted to sorted lists
4. Dictionary iteration - Python 3.7+ dicts are ordered, but verify

**Fix**:
```python
# Sort files
json_files = sorted(list(path.glob("*.json")))

# Sort violations
violations = sorted(violations, key=lambda v: v.rule_id)

# Sort sets
categories = sorted(list(categories))
```

### Issue: Different Results Between Instances

**Check**:
1. No shared state between instances
2. Each instance loads rules independently
3. No module-level mutable state

**Fix**: Ensure each instance is independent:
```python
class PreImplementationHookManager:
    def __init__(self, ...):
        # Each instance creates its own loader
        self.rule_loader = ConstitutionRuleLoader(...)
        # No shared state
```

### Issue: Timing-Dependent Behavior

**Check**:
1. No `time.time()` or `datetime.now()` in validation
2. No random number generation
3. No external API calls

**Fix**: Remove all time/random dependencies.

## Best Practices

1. **Always Sort Collections**: Sort files, violations, categories for consistency
2. **No Global State**: Each instance should be independent
3. **Pure Functions**: Validation should be functional with no side effects
4. **Deterministic Logic**: No random, time-based, or external dependencies
5. **Test Determinism**: Include determinism tests in test suite

## Conclusion

The pre-implementation hooks are designed to be **deterministic, consistent, and repeatable**:

- ✅ Rules loaded in deterministic order
- ✅ Validation produces same results for same input
- ✅ No shared state or global variables
- ✅ No time or random dependencies
- ✅ Comprehensive determinism tests verify behavior

**Status**: All determinism requirements are met and verified by tests.
