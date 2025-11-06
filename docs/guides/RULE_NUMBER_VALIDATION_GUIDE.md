# Rule Number Validation Guide
## Root Cause Analysis and Prevention

## Root Cause of Rule Number Errors

### Error Description
Rule numbers 4083, 4171, 1685, 1641, 1531 were used instead of actual rule numbers 172, 176, 63, 61, 56.

### Root Cause Analysis

#### 1. **Manual File Reading Confusion**
**Problem**: When reading `config/constitution_rules.json` manually, line numbers in the file (4083, 4171, etc.) were mistaken for rule numbers.

**Example**:
```json
"172": {                    // Line 4078 - JSON key
  "rule_number": 172,       // Line 4079 - ACTUAL rule number
  "title": "Structured Logs", // Line 4080
  "category": "observability", // Line 4081
  "priority": "critical",     // Line 4082
  "content": "..."            // Line 4083 - NOT a rule number!
}
```

**Error**: Used line 4083 (content field) instead of line 4079 (rule_number field).

#### 2. **No Programmatic Lookup**
**Problem**: Rule numbers were hardcoded instead of being looked up programmatically from the rules database.

**Incorrect Approach**:
```python
# Hardcoded - error prone
rule_number = 4083  # Wrong - this was a line number
```

**Correct Approach**:
```python
# Programmatic lookup
rule = rule_loader.get_rule_by_number(172)  # Correct
rule_number = rule.get('rule_number')  # Always use this
```

#### 3. **No Validation**
**Problem**: No validation that rule numbers are within valid range (1-415) or that they actually exist.

**Missing**: Validation check before using rule numbers.

#### 4. **No Single Source of Truth Access**
**Problem**: Did not use the existing APIs (`ConstitutionRulesJSON`, `ConstitutionRulesDB`) to get rule numbers.

**Available APIs** (not used):
- `ConstitutionRulesJSON.get_rule_by_number(rule_number)`
- `ConstitutionRulesDB.get_rule_by_number(rule_number)`
- `ConstitutionRuleLoader.get_rule_by_id(rule_id)`

---

## Prevention Strategies

### Strategy 1: Always Use Programmatic Rule Lookup

**NEVER** hardcode rule numbers. **ALWAYS** look them up:

```python
from config.constitution.constitution_rules_json import ConstitutionRulesJSON

rule_loader = ConstitutionRulesJSON()

# CORRECT: Look up rule by number
rule = rule_loader.get_rule_by_number(172)
if rule:
    rule_number = rule.get('rule_number')  # 172
    rule_title = rule.get('title')  # "Structured Logs"
else:
    raise ValueError(f"Rule 172 not found")
```

### Strategy 2: Validate Rule Numbers Exist

**ALWAYS** validate rule numbers before using them:

```python
def validate_rule_number(rule_number: int) -> bool:
    """
    Validate that a rule number exists in the constitution rules.
    
    Args:
        rule_number: Rule number to validate
        
    Returns:
        True if rule exists, False otherwise
    """
    from config.constitution.constitution_rules_json import ConstitutionRulesJSON
    
    rule_loader = ConstitutionRulesJSON()
    rule = rule_loader.get_rule_by_number(rule_number)
    
    if not rule:
        raise ValueError(f"Rule {rule_number} does not exist. Valid range: 1-415")
    
    return True

# Usage
validate_rule_number(172)  # Valid
validate_rule_number(4083)  # Raises ValueError - rule doesn't exist
```

### Strategy 3: Use Rule Lookup by Title/Content

**When you know the rule title but not the number**, look it up:

```python
def get_rule_number_by_title(title_keyword: str) -> Optional[int]:
    """
    Get rule number by searching for title keyword.
    
    Args:
        title_keyword: Keyword in rule title (e.g., "Structured Logs")
        
    Returns:
        Rule number if found, None otherwise
    """
    from config.constitution.constitution_rules_json import ConstitutionRulesJSON
    
    rule_loader = ConstitutionRulesJSON()
    all_rules = rule_loader.get_all_rules()
    
    for rule in all_rules:
        if title_keyword.lower() in rule.get('title', '').lower():
            return rule.get('rule_number')
    
    return None

# Usage
rule_num = get_rule_number_by_title("Structured Logs")  # Returns 172
```

### Strategy 4: Add Rule Number Validation to Post-Generation Validator

**Add validation at initialization**:

```python
class PostGenerationValidator:
    def __init__(self):
        """Initialize the post-generation validator."""
        self.code_validator = ConstitutionValidator()
        self.rule_loader = ConstitutionRulesJSON()
        self._validate_rule_references()
    
    def _validate_rule_references(self):
        """Validate all rule numbers referenced in this class."""
        referenced_rules = [11, 149, 332, 172, 62, 61, 176, 63, 56]
        
        for rule_num in referenced_rules:
            rule = self.rule_loader.get_rule_by_number(rule_num)
            if not rule:
                raise ValueError(
                    f"Invalid rule number {rule_num} referenced in PostGenerationValidator. "
                    f"Rule does not exist. Valid range: 1-415"
                )
```

### Strategy 5: Use Rule ID Instead of Rule Number

**Rule IDs are more stable** than rule numbers:

```python
# Instead of rule_number, use rule_id
rule_id = "R-172"  # More explicit
rule = rule_loader.get_rule_by_id(rule_id)
```

### Strategy 6: Add Unit Tests for Rule Number Validation

**Test that all referenced rule numbers exist**:

```python
def test_post_generation_validator_rule_numbers():
    """Test that all rule numbers in PostGenerationValidator are valid."""
    from validator.post_generation_validator import PostGenerationValidator
    from config.constitution.constitution_rules_json import ConstitutionRulesJSON
    
    validator = PostGenerationValidator()
    rule_loader = ConstitutionRulesJSON()
    
    # Extract rule numbers from validator source code
    # (Could be done via AST parsing or explicit list)
    referenced_rules = [11, 149, 332, 172, 62, 61, 176, 63, 56]
    
    for rule_num in referenced_rules:
        rule = rule_loader.get_rule_by_number(rule_num)
        assert rule is not None, f"Rule {rule_num} does not exist"
        assert rule.get('rule_number') == rule_num, f"Rule number mismatch"
```

### Strategy 7: Add Linting Rule

**Create a custom linter rule** to detect hardcoded rule numbers:

```python
# .pylintrc or custom linter
# Detect patterns like: rule_number=4083, Rule 4083, etc.
# Warn if number > 415 (max rule count)
```

### Strategy 8: Use Constants File

**Create a constants file** with validated rule numbers:

```python
# validator/rule_constants.py
from config.constitution.constitution_rules_json import ConstitutionRulesJSON

rule_loader = ConstitutionRulesJSON()

# Look up and validate all rule numbers
RULE_FILE_HEADERS = rule_loader.get_rule_by_number(11).get('rule_number')
RULE_FILE_HEADERS_AUDIT = rule_loader.get_rule_by_number(149).get('rule_number')
RULE_NO_ADVANCED_CONCEPTS = rule_loader.get_rule_by_number(332).get('rule_number')
RULE_STRUCTURED_LOGS = rule_loader.get_rule_by_number(172).get('rule_number')
RULE_SERVICE_IDENTIFICATION = rule_loader.get_rule_by_number(62).get('rule_number')
RULE_LOG_LEVEL_ENUM = rule_loader.get_rule_by_number(61).get('rule_number')
RULE_ERROR_ENVELOPE = rule_loader.get_rule_by_number(176).get('rule_number')
RULE_TRACE_CONTEXT = rule_loader.get_rule_by_number(63).get('rule_number')
RULE_MONOTONIC_TIME = rule_loader.get_rule_by_number(56).get('rule_number')

# Usage
rule_number = RULE_STRUCTURED_LOGS  # Always correct
```

---

## Implementation: Add Rule Number Validation

### Step 1: Create Rule Number Validator Utility

```python
# validator/utils/rule_validator.py
"""Utility to validate rule numbers and look up rules."""

from typing import Optional, Dict, Any
from config.constitution.constitution_rules_json import ConstitutionRulesJSON


class RuleNumberValidator:
    """Validates rule numbers and provides lookup utilities."""
    
    def __init__(self):
        """Initialize rule number validator."""
        self.rule_loader = ConstitutionRulesJSON()
        self.max_rule_number = 415  # From statistics
    
    def validate_rule_number(self, rule_number: int) -> bool:
        """
        Validate that a rule number exists.
        
        Args:
            rule_number: Rule number to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValueError: If rule number is out of range or doesn't exist
        """
        if rule_number < 1 or rule_number > self.max_rule_number:
            raise ValueError(
                f"Rule number {rule_number} is out of valid range (1-{self.max_rule_number})"
            )
        
        rule = self.rule_loader.get_rule_by_number(rule_number)
        if not rule:
            raise ValueError(f"Rule {rule_number} does not exist in constitution rules")
        
        return True
    
    def get_rule_by_number(self, rule_number: int) -> Optional[Dict[str, Any]]:
        """
        Get rule by number with validation.
        
        Args:
            rule_number: Rule number to look up
            
        Returns:
            Rule dictionary or None if not found
        """
        self.validate_rule_number(rule_number)
        return self.rule_loader.get_rule_by_number(rule_number)
    
    def get_rule_number_by_title(self, title_keyword: str) -> Optional[int]:
        """
        Get rule number by title keyword.
        
        Args:
            title_keyword: Keyword in rule title
            
        Returns:
            Rule number if found, None otherwise
        """
        all_rules = self.rule_loader.get_all_rules()
        
        for rule in all_rules:
            title = rule.get('title', '')
            if title_keyword.lower() in title.lower():
                return rule.get('rule_number')
        
        return None
```

### Step 2: Update Post-Generation Validator to Use Validation

```python
# validator/post_generation_validator.py
from validator.utils.rule_validator import RuleNumberValidator

class PostGenerationValidator:
    def __init__(self):
        """Initialize the post-generation validator."""
        self.code_validator = ConstitutionValidator()
        self.rule_validator = RuleNumberValidator()
        
        # Validate all rule numbers at initialization
        self._validate_all_rule_references()
    
    def _validate_all_rule_references(self):
        """Validate all rule numbers referenced in this class."""
        referenced_rules = [11, 149, 332, 172, 62, 61, 176, 63, 56]
        
        for rule_num in referenced_rules:
            try:
                self.rule_validator.validate_rule_number(rule_num)
            except ValueError as e:
                raise ValueError(
                    f"PostGenerationValidator initialization failed: {e}. "
                    f"Fix rule number references before using validator."
                )
```

### Step 3: Add Pre-Commit Hook

**Add validation check before commits**:

```python
# .git/hooks/pre-commit
#!/usr/bin/env python3
"""Pre-commit hook to validate rule numbers."""

import re
import sys
from pathlib import Path

def validate_rule_numbers_in_file(file_path: Path) -> bool:
    """Check for invalid rule numbers (> 415) in file."""
    content = file_path.read_text()
    
    # Pattern: rule_number=XXXX or Rule XXXX
    patterns = [
        r'rule_number\s*=\s*(\d{4,})',  # rule_number=4083
        r'Rule\s+(\d{4,})',  # Rule 4083
        r'"rule_number":\s*(\d{4,})',  # "rule_number": 4083
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            rule_num = int(match)
            if rule_num > 415:
                print(f"ERROR: Invalid rule number {rule_num} in {file_path}")
                print(f"  Rule numbers must be 1-415. Did you use a JSON line number?")
                return False
    
    return True

if __name__ == '__main__':
    # Check staged files
    # ... implementation ...
    pass
```

---

## Summary

### Root Causes
1. **Manual file reading** - Confused JSON line numbers with rule_number field values
2. **No programmatic lookup** - Hardcoded numbers instead of using APIs
3. **No validation** - No check that rule numbers exist or are in valid range
4. **No single source of truth** - Didn't use existing rule loader APIs

### Prevention
1. ✅ **Always use programmatic lookup** - Use `get_rule_by_number()`
2. ✅ **Validate rule numbers** - Check they exist and are in range 1-415
3. ✅ **Use rule lookup utilities** - Create helper functions for rule lookups
4. ✅ **Add unit tests** - Test all rule number references
5. ✅ **Use constants file** - Centralized, validated rule number constants
6. ✅ **Add pre-commit hooks** - Detect invalid rule numbers before commit
7. ✅ **Add initialization validation** - Validate all rule references at startup

### Critical Rule
**NEVER hardcode rule numbers. ALWAYS look them up from the constitution rules database using the provided APIs.**

