# Root Cause Analysis: Rule Number Errors

## Error Summary

**Error**: Rule numbers 4083, 4171, 1685, 1641, 1531 were used instead of actual rule numbers 172, 176, 63, 61, 56.

**Impact**: Invalid rule references in `PostGenerationValidator` causing validation failures.

---

## Root Cause Analysis

### 1. **Primary Root Cause: Manual File Reading Confusion**

**Problem**: When manually reading `config/constitution_rules.json`, line numbers in the file were mistaken for rule numbers.

**Example from JSON file**:
```json
"172": {                    // Line 4078 - JSON key (rule identifier)
  "rule_number": 172,       // Line 4079 - ACTUAL rule number field
  "title": "Structured Logs", // Line 4080
  "category": "observability", // Line 4081
  "priority": "critical",     // Line 4082
  "content": "..."            // Line 4083 - NOT a rule number!
}
```

**Error Pattern**:
- Line 4083 contains the `content` field
- Line 4079 contains the `rule_number` field (172)
- **Mistake**: Used line number 4083 instead of rule_number value 172

**Why This Happened**:
- Manual inspection of JSON file
- Visual confusion between line numbers and field values
- No programmatic validation

---

### 2. **Secondary Root Cause: No Programmatic Lookup**

**Problem**: Rule numbers were hardcoded instead of being looked up programmatically.

**Incorrect Approach** (what happened):
```python
# Hardcoded - error prone
rule_number = 4083  # Wrong - this was a JSON line number
```

**Correct Approach** (should have been):
```python
# Programmatic lookup
from config.constitution.constitution_rules_json import ConstitutionRulesJSON
rule_loader = ConstitutionRulesJSON()
rule = rule_loader.get_rule_by_number(172)  # Correct
rule_number = rule.get('rule_number')  # Always use this
```

**Why This Happened**:
- Did not use existing APIs (`ConstitutionRulesJSON`, `ConstitutionRulesDB`)
- Manual copy-paste from file inspection
- No validation layer

---

### 3. **Tertiary Root Cause: No Validation**

**Problem**: No validation that rule numbers are within valid range (1-415) or that they actually exist.

**Missing Validation**:
- No range check (1-415)
- No existence check
- No initialization-time validation

**Why This Happened**:
- No validation utility existed
- No pre-initialization checks
- No unit tests for rule number references

---

### 4. **Quaternary Root Cause: No Single Source of Truth Access**

**Problem**: Did not use the existing rule loader APIs that provide validated rule access.

**Available APIs** (not used):
- `ConstitutionRulesJSON.get_rule_by_number(rule_number)`
- `ConstitutionRulesDB.get_rule_by_number(rule_number)`
- `ConstitutionRuleLoader.get_rule_by_id(rule_id)`

**Why This Happened**:
- Unfamiliarity with existing APIs
- Manual file reading seemed faster
- No enforcement to use APIs

---

## Prevention Strategies Implemented

### ✅ Strategy 1: Rule Number Validator Utility

**Created**: `validator/utils/rule_validator.py`

**Features**:
- Validates rule numbers exist and are in range (1-415)
- Provides programmatic rule lookup
- Raises clear errors if rule numbers are invalid
- Detects common mistakes (e.g., JSON line numbers > 415)

**Usage**:
```python
from validator.utils.rule_validator import RuleNumberValidator

validator = RuleNumberValidator()
validator.validate_rule_number(172)  # ✓ Valid
validator.validate_rule_number(4083)  # ✗ Raises ValueError
```

---

### ✅ Strategy 2: Initialization-Time Validation

**Implemented**: `PostGenerationValidator.__init__()` now validates all rule numbers

**Features**:
- Validates all referenced rule numbers at initialization
- Fails fast if invalid rule numbers detected
- Clear error messages identifying which rules are invalid

**Code**:
```python
def __init__(self):
    self.rule_validator = RuleNumberValidator()
    self._validate_all_rule_references()  # Validates all rules at startup
```

---

### ✅ Strategy 3: Documentation

**Created**: `docs/guides/RULE_NUMBER_VALIDATION_GUIDE.md`

**Content**:
- Root cause analysis
- Prevention strategies
- Code examples
- Best practices

---

## Prevention Checklist

### For Developers

- [ ] **NEVER hardcode rule numbers** - Always use `RuleNumberValidator`
- [ ] **NEVER use JSON line numbers** - Always use `rule_number` field
- [ ] **ALWAYS validate rule numbers** - Use `validate_rule_number()` before using
- [ ] **ALWAYS use programmatic lookup** - Use `get_rule_by_number()` from APIs
- [ ] **ALWAYS check valid range** - Rule numbers must be 1-415

### For Code Reviews

- [ ] Check for hardcoded rule numbers > 415 (likely JSON line numbers)
- [ ] Verify rule numbers are validated at initialization
- [ ] Ensure rule lookup uses APIs, not manual file reading
- [ ] Confirm unit tests validate rule number references

### For CI/CD

- [ ] Add pre-commit hook to detect invalid rule numbers
- [ ] Add unit tests for rule number validation
- [ ] Add linting rule for hardcoded rule numbers > 415

---

## Error Detection Pattern

### How to Detect This Error

**Pattern**: Rule numbers > 415 are likely JSON line numbers, not actual rule numbers.

**Detection**:
```python
# Invalid rule numbers (JSON line numbers)
invalid = [4083, 4171, 1685, 1641, 1531]

# Valid rule numbers (actual rule_number field values)
valid = [172, 176, 63, 61, 56]

# Detection check
MAX_RULE_NUMBER = 415
if rule_number > MAX_RULE_NUMBER:
    raise ValueError(f"Rule number {rule_number} > {MAX_RULE_NUMBER}. "
                     f"Did you use a JSON line number instead of rule_number?")
```

---

## Summary

### Root Causes (Priority Order)

1. **Manual file reading confusion** - Mistook JSON line numbers for rule numbers
2. **No programmatic lookup** - Hardcoded numbers instead of using APIs
3. **No validation** - No check that rule numbers exist or are in valid range
4. **No single source of truth** - Didn't use existing rule loader APIs

### Prevention (Implemented)

1. ✅ **Rule Number Validator Utility** - `RuleNumberValidator` class
2. ✅ **Initialization-Time Validation** - Validates all rule numbers at startup
3. ✅ **Documentation** - Comprehensive guide and root cause analysis
4. ✅ **Clear Error Messages** - Detects and explains common mistakes

### Critical Rule

**NEVER hardcode rule numbers. ALWAYS look them up from the constitution rules database using the provided APIs (`RuleNumberValidator` or `ConstitutionRulesJSON`).**

---

## Testing

### Manual Test

```python
# Test that validator initializes correctly
from validator.post_generation_validator import PostGenerationValidator
validator = PostGenerationValidator()  # Should succeed - all rules validated
```

### Automated Test

```python
def test_post_generation_validator_rule_numbers():
    """Test that all rule numbers in PostGenerationValidator are valid."""
    from validator.post_generation_validator import PostGenerationValidator
    from validator.utils.rule_validator import RuleNumberValidator

    # This will raise ValueError if any rule numbers are invalid
    validator = PostGenerationValidator()

    # Verify all referenced rules exist
    rule_validator = RuleNumberValidator()
    referenced_rules = [11, 149, 332, 172, 62, 61, 176, 63, 56]

    for rule_num in referenced_rules:
        rule = rule_validator.get_rule_by_number(rule_num)
        assert rule is not None, f"Rule {rule_num} does not exist"
        assert rule.get('rule_number') == rule_num, f"Rule number mismatch"
```

---

## Future Improvements

1. **Pre-commit hook** - Detect invalid rule numbers before commit
2. **Linting rule** - Warn on hardcoded rule numbers > 415
3. **Constants file** - Centralized, validated rule number constants
4. **AST-based detection** - Automatically detect rule number references in code
