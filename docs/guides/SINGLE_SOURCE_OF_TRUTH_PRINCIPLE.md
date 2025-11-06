# Single Source of Truth Principle

## Overview

The ZeroUI 2.0 Constitution system follows a strict **Single Source of Truth** principle to prevent rule count discrepancies and ensure consistency across the entire codebase.

## The Principle

**The JSON files in `docs/constitution/` are the ONLY source of truth for rule counts.**

All rule counts MUST be calculated dynamically from these files. **NO hardcoded rule counts are allowed anywhere in the codebase.**

## Why This Matters

Hardcoded rule counts create inconsistencies:
- ❌ Different files claim different rule counts (215, 218, 293, 424, 425)
- ❌ When rules are added/removed, multiple files must be updated
- ❌ Easy to forget to update one file, causing discrepancies
- ❌ Maintenance burden increases with each hardcoded value

Dynamic rule counting eliminates these issues:
- ✅ Single source of truth (JSON files)
- ✅ Automatic calculation from actual rules
- ✅ No manual updates needed when rules change
- ✅ Guaranteed consistency across all files

## Implementation

### Rule Count Loader

The `config.constitution.rule_count_loader` module provides dynamic rule counting:

```python
from config.constitution import get_rule_counts

# Get all counts dynamically
counts = get_rule_counts()
print(f"Total rules: {counts['total_rules']}")
print(f"Enabled rules: {counts['enabled_rules']}")
print(f"Disabled rules: {counts['disabled_rules']}")
print(f"Category counts: {counts['category_counts']}")
```

### Usage in Code

**✅ CORRECT:**
```python
from config.constitution import get_rule_counts

counts = get_rule_counts()
total_rules = counts['total_rules']
enabled_rules = counts['enabled_rules']
```

**❌ INCORRECT:**
```python
# DO NOT DO THIS
total_rules = 425  # Hardcoded - violates principle
enabled_rules = 424  # Hardcoded - violates principle
```

### Configuration Files

**✅ CORRECT:**
```json
{
  "constitution_version": "2.0",
  "_note": "total_rules is dynamically calculated from docs/constitution/*.json files"
}
```

**❌ INCORRECT:**
```json
{
  "constitution_version": "2.0",
  "total_rules": 425  // Hardcoded - violates principle
}
```

## Files That Must Follow This Principle

1. **Configuration Files**:
   - `config/base_config.json` - No hardcoded `total_rules`
   - `config/constitution_config.json` - No hardcoded counts
   - `config/constitution_rules.json` - Counts calculated dynamically

2. **Python Code**:
   - `config/constitution/config_manager.py` - Uses `get_rule_counts()`
   - `config/constitution/database.py` - No hardcoded counts
   - `config/constitution/constitution_rules_json.py` - Counts calculated dynamically
   - `config/constitution/rule_extractor.py` - No hardcoded ranges
   - `validator/pre_implementation_hooks.py` - No hardcoded counts

3. **Documentation**:
   - `README.md` - References dynamic counts, not hardcoded numbers
   - All guide files - No hardcoded rule counts

## Enforcement

### Code Review Checklist

When reviewing code, check for:
- [ ] No hardcoded rule counts in configuration files
- [ ] No hardcoded rule counts in Python code
- [ ] Use of `get_rule_counts()` or `RuleCountLoader` for counts
- [ ] Documentation references dynamic counts, not hardcoded numbers

### Automated Checks

The system includes automated verification:
```bash
# Check for hardcoded rule counts
python -c "from config.constitution import get_rule_counts; print('Rule counts:', get_rule_counts())"
```

## Benefits

1. **Consistency**: All files always show correct counts
2. **Maintainability**: Add/remove rules without updating multiple files
3. **Accuracy**: Counts automatically reflect actual rules
4. **Reliability**: No discrepancies between different parts of system

## Migration Guide

If you find hardcoded rule counts:

1. **Identify the hardcoded value**
2. **Replace with dynamic calculation**:
   ```python
   from config.constitution import get_rule_counts
   counts = get_rule_counts()
   value = counts['total_rules']  # or 'enabled_rules', etc.
   ```
3. **Update documentation** to state counts are dynamic
4. **Test** to ensure counts are calculated correctly

## Example: Adding a New Rule

When adding a new rule:

1. **Edit JSON file** in `docs/constitution/`
2. **That's it!** Rule count is automatically updated everywhere

No need to:
- ❌ Update `base_config.json`
- ❌ Update Python code
- ❌ Update documentation counts
- ❌ Update any hardcoded values

The system automatically:
- ✅ Calculates new total rule count
- ✅ Updates all statistics
- ✅ Maintains consistency

## Conclusion

**Remember**: The JSON files in `docs/constitution/` are the ONLY source of truth. All rule counts are calculated dynamically. Never hardcode rule counts anywhere.

