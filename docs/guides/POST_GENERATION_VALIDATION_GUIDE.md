# Post-Generation Validation Enforcement Guide

## Overview

This guide explains how to enforce pre-implementation hooks to validate **generated code (output)** in addition to prompts (input). This addresses the gap where structural/architectural violations in generated code were not being caught.

## Problem Statement

**Pre-implementation hooks** validate **prompts** (text input) using pattern matching, but cannot detect violations that only appear in **generated code** (output), such as:
- Missing file headers
- Async/await usage
- Logging format issues
- Error envelope structure
- W3C trace context

## Solution: Two-Phase Validation

### Phase 1: Pre-Implementation (Existing)
- Validates prompt text before code generation
- Uses pattern matching and keyword detection
- Blocks generation if prompt contains prohibited patterns

### Phase 2: Post-Generation (New)
- Validates generated code after AI service returns code
- Uses AST parsing and code structure analysis
- Blocks if violations found in generated code

## Implementation

### 1. Post-Generation Validator

**File**: `validator/post_generation_validator.py`

**Purpose**: Validates generated code using AST analysis against all 415 constitution rules.

**Key Features**:
- Parses generated code into AST
- Validates against existing `ConstitutionValidator`
- Checks structural violations (file headers, async/await, decorators, logging, etc.)
- Returns violations with fix suggestions

### 2. Integration with AI Service Wrapper

**File**: `validator/integrations/ai_service_wrapper.py`

**Changes**: Modified `_validate_and_generate()` method to add post-generation validation:

```python
# Step 1: Pre-implementation validation (existing)
validation_result = self.hook_manager.validate_before_generation(...)

# Step 2: Block if prompt violations (existing)
if not validation_result['valid']:
    return {'success': False, 'error': 'CONSTITUTION_VIOLATION', ...}

# Step 3: Generate code (existing)
ai_result = self._call_ai_service(prompt, context)

# Step 4: Post-generation validation (NEW)
post_validator = PostGenerationValidator()
post_validation_result = post_validator.validate_generated_code(
    ai_result, file_type=file_type, file_path=file_path
)

# Step 5: Block if generated code violations (NEW)
if not post_validation_result['valid']:
    return {
        'success': False,
        'error': 'GENERATED_CODE_VIOLATION',
        'violations': post_validation_result['violations'],
        ...
    }

# Step 6: Return successful generation (NEW)
return {'success': True, 'generated_code': ai_result, ...}
```

## Validation Flow

```
User Prompt
    ↓
[Phase 1: Pre-Implementation Validation]
    ↓ (if valid)
AI Service Generation
    ↓
Generated Code
    ↓
[Phase 2: Post-Generation Validation]
    ↓ (if valid)
Return Code to User
```

## What Post-Generation Validator Checks

### 1. File Headers (Rule 11, Rule 149)
- Checks for comprehensive file header with What/Why/Reads-Writes/Contracts/Risks
- Validates multi-line docstring structure
- **Detection**: Text analysis of first 20 lines

### 2. Async/Await Usage (Rule 332)
- Detects `async def` and `await` expressions
- Allows framework-required exceptions (ASGI middleware)
- **Detection**: AST analysis for `ast.AsyncFunctionDef` and `ast.Await` nodes

### 3. Decorator Usage (Rule 332)
- Detects decorators on functions/classes
- Allows framework-required exceptions (FastAPI route decorators)
- **Detection**: AST analysis for `node.decorator_list`

### 4. Logging Format (Rule 4083, Rule 62, Rule 1641)
- Checks for JSON-structured logging
- Validates service metadata (service, version, env, host)
- **Detection**: Text analysis for `json.dumps()` and metadata fields

### 5. Error Envelope Structure (Rule 4171)
- Validates error response structure: `{"error": {"code": "...", "message": "...", "details": ...}}`
- **Detection**: Text analysis for HTTPException usage and error envelope structure

### 6. W3C Trace Context (Rule 1685)
- Checks for traceId, spanId, parentSpanId in request logging
- **Detection**: Text analysis for trace context fields

### 7. Type Hints
- Validates function return type hints
- **Detection**: AST analysis for `node.returns`

### 8. All Other Rules
- Uses existing `ConstitutionValidator` to check all 415 rules
- **Detection**: Full AST-based validation

## Usage

### Automatic Enforcement

Post-generation validation is **automatically enforced** when using `AIServiceIntegration`:

```python
from validator.integrations.integration_registry import IntegrationRegistry

registry = IntegrationRegistry()
result = registry.generate_code('openai', prompt, {
    'file_type': 'python',
    'task_type': 'api'
})

if not result['success']:
    if result['error'] == 'GENERATED_CODE_VIOLATION':
        # Generated code has violations
        violations = result['violations']
        for v in violations:
            print(f"Rule {v['rule_id']}: {v['message']}")
            print(f"Fix: {v['fix_suggestion']}")
```

### Manual Validation

You can also validate code directly:

```python
from validator.post_generation_validator import PostGenerationValidator

validator = PostGenerationValidator()
result = validator.validate_generated_code(
    code="""def my_function():
    pass""",
    file_type="python",
    file_path="my_file.py"
)

if not result['valid']:
    print(f"Found {result['total_violations']} violations")
    for v in result['violations']:
        print(f"  - {v['message']}")
```

## Response Format

### Success Response
```json
{
    "success": true,
    "generated_code": "...",
    "validation_info": {
        "pre_validation": {
            "rules_checked": 415,
            "categories_validated": ["Python", "API"]
        },
        "post_validation": {
            "violations_found": 0,
            "compliance_score": 1.0
        }
    }
}
```

### Violation Response
```json
{
    "success": false,
    "error": "GENERATED_CODE_VIOLATION",
    "violations": [
        {
            "rule_id": "R-011",
            "rule_number": 11,
            "severity": "ERROR",
            "message": "Generated code missing comprehensive file header...",
            "file_path": "generated_code",
            "line_number": 1,
            "code_snippet": "...",
            "fix_suggestion": "Add comprehensive file header..."
        }
    ],
    "total_violations": 1,
    "violations_by_severity": {"ERROR": 1, "WARNING": 0, "INFO": 0},
    "compliance_score": 0.0,
    "blocked_by": "post_generation_validator",
    "generated_code": "..."  // Code included for review
}
```

## Framework Exception Handling

The validator recognizes framework-required patterns and allows them:

### Async/Await Exceptions
- **Allowed**: ASGI middleware `dispatch()` methods
- **Detection**: Checks for `middleware`, `dispatch`, `ASGI`, `BaseHTTPMiddleware` in context

### Decorator Exceptions
- **Allowed**: FastAPI route decorators (`@router.post`, `@router.get`, etc.)
- **Detection**: Checks for `@router.`, `@app.`, `router.post`, `router.get` patterns

## Testing

### Test Post-Generation Validation

```python
from validator.post_generation_validator import PostGenerationValidator

validator = PostGenerationValidator()

# Test 1: Missing file header
code_without_header = """def my_function():
    pass"""

result = validator.validate_generated_code(code_without_header)
assert not result['valid']
assert len(result['violations']) > 0

# Test 2: Async function (non-framework)
code_with_async = """async def my_function():
    await something()"""

result = validator.validate_generated_code(code_with_async)
assert not result['valid']

# Test 3: Valid code
code_valid = '''"""
What: Test file
Why: For testing
Reads/Writes: None
Contracts: None
Risks: None
"""

def my_function() -> None:
    """Test function."""
    pass'''

result = validator.validate_generated_code(code_valid)
assert result['valid']
```

## Integration Points

### 1. AI Service Integrations
- `OpenAIIntegration`
- `CursorIntegration`
- Any custom integration extending `AIServiceIntegration`

### 2. API Service
- `validator/integrations/api_service.py` - HTTP API endpoint
- Automatically uses post-generation validation

### 3. CLI Tools
- `enhanced_cli.py` - Can be extended to use post-generation validation

## Performance Considerations

- **AST Parsing**: Fast for typical file sizes (< 1ms for 1000 lines)
- **Temporary Files**: Created and cleaned up automatically
- **Caching**: Can be added for repeated validations of same code

## Error Handling

- **Syntax Errors**: Caught and reported as violations
- **Parse Errors**: Handled gracefully with error messages
- **File I/O Errors**: Temporary file cleanup in finally block

## Future Enhancements

1. **TypeScript Support**: Add TypeScript parser for TS/TSX files
2. **Incremental Validation**: Validate only changed sections
3. **Caching**: Cache validation results for identical code
4. **Parallel Validation**: Validate multiple files in parallel
5. **Rule-Specific Validators**: Specialized validators for specific rule categories

## Summary

Post-generation validation enforces all 415 constitution rules on **generated code**, not just prompts. This ensures:

✅ **Structural violations** are caught (file headers, async/await, decorators)
✅ **Implementation details** are validated (logging format, error envelopes, trace context)
✅ **Code quality** is enforced (type hints, docstrings, organization)
✅ **All 415 rules** are checked using existing validators

The validation is **automatic** when using `AIServiceIntegration` and **blocks generation** if violations are found, ensuring only compliant code is returned to users.
