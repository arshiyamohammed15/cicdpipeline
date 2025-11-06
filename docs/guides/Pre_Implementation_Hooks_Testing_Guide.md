# Pre-Implementation Hooks Testing Guide

## Overview

This guide provides comprehensive instructions for testing and verifying that pre-implementation hooks are working correctly. The hooks enforce all enabled constitution rules from JSON files (single source of truth) before AI code generation occurs.

## Quick Verification

Run the quick verification script:

```bash
python tests/verify_hooks_working.py
```

This script verifies:
1. Rule loading (from JSON files - single source of truth)
2. Violation detection
3. Blocking behavior
4. Integration points
5. Rule count accuracy (matches JSON files)

## Comprehensive Test Suite

Run the full test suite:

```bash
python -m pytest tests/test_pre_implementation_hooks_comprehensive.py -v
```

Or using unittest:

```bash
python tests/test_pre_implementation_hooks_comprehensive.py
```

## Manual Testing Steps

### 1. Verify Rule Loading

```python
from validator.pre_implementation_hooks import PreImplementationHookManager

hook_manager = PreImplementationHookManager()
print(f"Loaded {hook_manager.total_rules} rules")  # Actual count from JSON files
```

### 2. Test Violation Detection

```python
from validator.pre_implementation_hooks import PreImplementationHookManager

hook_manager = PreImplementationHookManager()

# Test with known violation
prompt = "create a function with hardcoded password = 'secret123'"
result = hook_manager.validate_before_generation(prompt)

print(f"Valid: {result['valid']}")  # Should be False
print(f"Violations: {len(result['violations'])}")  # Should be > 0
print(f"Rules checked: {result['total_rules_checked']}")  # Actual count from JSON files
```

### 3. Test Blocking Behavior

```python
from validator.integrations.integration_registry import IntegrationRegistry

registry = IntegrationRegistry()

# Invalid prompt should be blocked
invalid_prompt = "create function with hardcoded password"
result = registry.generate_code('openai', invalid_prompt, {
    'file_type': 'python',
    'task_type': 'general'
})

print(f"Success: {result['success']}")  # Should be False
print(f"Error: {result.get('error')}")  # Should be 'CONSTITUTION_VIOLATION'
print(f"Blocked by: {result.get('blocked_by')}")  # Should be 'pre_implementation_hooks'
```

### 4. Test Valid Prompts

```python
from validator.pre_implementation_hooks import PreImplementationHookManager

hook_manager = PreImplementationHookManager()

# Valid prompt should pass
valid_prompt = "create a Python function that calculates the sum of two numbers"
result = hook_manager.validate_before_generation(valid_prompt)

print(f"Valid: {result['valid']}")
print(f"Violations: {len(result['violations'])}")
print(f"Rules checked: {result['total_rules_checked']}")  # Actual count from JSON files
```

### 5. Test API Endpoints

Start the API service:

```bash
python tools/start_validation_service.py
```

Then test the endpoints:

```bash
# Test validation endpoint
curl -X POST http://localhost:5000/validate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "create function with hardcoded password",
    "file_type": "python",
    "task_type": "general"
  }'

# Expected response:
# {
#   "valid": false,
#   "violations": [...],
#   "total_rules_checked": <actual_count_from_json_files>,
#   ...
# }
```

### 6. Test Integration Points

Verify all integrations have hook managers:

```python
from validator.integrations.openai_integration import OpenAIIntegration
from validator.integrations.cursor_integration import CursorIntegration

openai = OpenAIIntegration()
cursor = CursorIntegration()

# Both should have hook_manager
assert hasattr(openai, 'hook_manager')
assert hasattr(cursor, 'hook_manager')

# Test blocking
invalid_prompt = "create function with hardcoded password"
result = openai.generate_code(invalid_prompt, {})
assert result['success'] == False
assert result['error'] == 'CONSTITUTION_VIOLATION'
```

## Test Cases

### Known Violations to Test

1. **Hardcoded Credentials**
   - Prompt: `"create function with hardcoded password = 'secret'"`
   - Expected: Should detect violation

2. **Assumptions**
   - Prompt: `"assume the user wants X and create a function"`
   - Expected: Should detect violation

3. **Scope Creep**
   - Prompt: `"create a function and also add logging and also include error handling"`
   - Expected: Should detect violation

4. **Hardcoded Values**
   - Prompt: `"create function with timeout = 30 and retries = 5 and max_connections = 100"`
   - Expected: Should detect violation if no config mentioned

5. **TypeScript 'any' Type**
   - Prompt: `"create TypeScript function using any type"`
   - Expected: Should detect violation

### Valid Prompts to Test

1. **Simple Function**
   - Prompt: `"create a Python function that calculates the sum of two numbers"`
   - Expected: Should pass validation

2. **Well-Defined Request**
   - Prompt: `"create a function that validates email addresses using regex"`
   - Expected: Should pass validation

## Verification Checklist

- [ ] Rule loading: All enabled rules loaded from JSON files (single source of truth)
- [ ] Disabled rules excluded: Only enabled rules loaded
- [ ] Violation detection: Known violations detected
- [ ] Blocking: Generation blocked when violations found
- [ ] Allowing: Generation proceeds when no violations
- [ ] Integration points: All integrations use hooks
- [ ] API endpoints: Validation endpoints work
- [ ] Edge cases: Empty prompts, long prompts handled
- [ ] Rule count: Matches JSON files (no hardcoded values)

## Continuous Testing

### Run Tests Before Commit

```bash
# Quick verification
python tests/verify_hooks_working.py

# Full test suite
python tests/test_pre_implementation_hooks_comprehensive.py

# Integration tests
python tests/test_integration.py
python tests/test_enforcement_flow.py
```

### CI/CD Integration

Add to your CI pipeline:

```yaml
- name: Test Pre-Implementation Hooks
  run: |
    python tests/verify_hooks_working.py
    python -m pytest tests/test_pre_implementation_hooks_comprehensive.py -v
```

## Troubleshooting

### Rules Not Loading

**Symptoms**: `total_rules_checked` doesn't match JSON files

**Check**:
1. Verify JSON files exist in `docs/constitution/`
2. Check file permissions
3. Verify JSON files are valid JSON

**Fix**:
```python
from pathlib import Path
import json

constitution_dir = Path("docs/constitution")
for json_file in constitution_dir.glob("*.json"):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"{json_file.name}: {len(data.get('constitution_rules', []))} rules")
    except Exception as e:
        print(f"Error loading {json_file.name}: {e}")
```

### Violations Not Detected

**Symptoms**: Invalid prompts pass validation

**Check**:
1. Verify validation logic in `PromptValidator`
2. Check rule patterns match prompt content
3. Verify rules are enabled

**Test**:
```python
from validator.pre_implementation_hooks import PreImplementationHookManager

hook_manager = PreImplementationHookManager()
# Test with known violation
result = hook_manager.validate_before_generation("hardcoded password")
print(f"Violations: {len(result['violations'])}")
```

### Generation Not Blocked

**Symptoms**: Code generation proceeds despite violations

**Check**:
1. Verify `_validate_and_generate` is called
2. Check integration implements blocking
3. Verify `block_on_violation` is enabled

**Test**:
```python
from validator.integrations.integration_registry import IntegrationRegistry

registry = IntegrationRegistry()
result = registry.generate_code('openai', "hardcoded password", {})
assert result['success'] == False
assert result['error'] == 'CONSTITUTION_VIOLATION'
```

## Expected Behavior

### When Violations Are Found

1. Validation returns `valid: false`
2. `violations` array contains violation objects
3. `total_rules_checked` matches count from JSON files
4. Code generation is blocked
5. Error response includes violation details

### When No Violations Are Found

1. Validation returns `valid: true`
2. `violations` array is empty
3. `total_rules_checked` matches count from JSON files
4. Code generation proceeds
5. Success response includes validation info

## Success Criteria

All tests pass when:
- ✓ All enabled rules from JSON files are loaded (single source of truth)
- ✓ Known violations are detected
- ✓ Generation is blocked for invalid prompts
- ✓ Generation proceeds for valid prompts
- ✓ All integration points work
- ✓ API endpoints function correctly
- ✓ Edge cases are handled
- ✓ Rule counts match JSON files (no hardcoded values)

## Additional Resources

- Main implementation: `validator/pre_implementation_hooks.py`
- Integration wrapper: `validator/integrations/ai_service_wrapper.py`
- API service: `validator/integrations/api_service.py`
- Test suite: `tests/test_pre_implementation_hooks_comprehensive.py`

