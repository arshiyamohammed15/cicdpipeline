# Hook Management Guide

## Overview

The ZeroUI2.0 Pre-Implementation Hook system allows fine-grained control over which Constitution rules are enforced during AI code generation. This guide explains how to enable/disable individual hooks through CLI commands.

## 🎯 **What Are Pre-Implementation Hooks?**

Pre-Implementation Hooks validate prompts **before** AI code generation, ensuring Constitution rules are enforced at the source rather than after generation. This prevents violations from reaching the codebase.

## 🔧 **Hook Categories**

The system organizes rules into 9 main categories:

| Category | Rule Range | Description |
|----------|------------|-------------|
| **Basic Work** | 1-75 | Fundamental development practices |
| **Code Review** | 76-99 | Code review and quality assurance |
| **Security & Privacy** | 100-131 | Security and privacy protection |
| **Logging** | 132-149 | Structured logging and observability |
| **Error Handling** | 150-180 | Error handling and recovery patterns |
| **TypeScript** | 181-215 | TypeScript development standards |
| **Storage Governance** | 216-228 | Data storage and governance |
| **GSMD** | 232-252 | Governance, Security, Management of Data |
| **Simple Readability** | 253-280 | Code readability and simplicity |

## 🚀 **Quick Start**

### 1. List All Hooks
```bash
python tools/hook_cli.py list
```

### 2. Disable a Category
```bash
python tools/hook_cli.py disable --category typescript --reason "Too strict for prototyping"
```

### 3. Enable a Specific Rule
```bash
python tools/hook_cli.py enable --rule 42 --reason "Testing specific functionality"
```

### 4. Show Statistics
```bash
python tools/hook_cli.py stats
```

## 📋 **CLI Commands Reference**

### List Commands

#### List All Categories
```bash
python tools/hook_cli.py list
```
**Output:**
```
📋 Hook Categories
==================================================
✅ Basic Work Rules (basic_work)
   Status: ENABLED
   Rules: 75
✅ Code Review Rules (code_review)
   Status: ENABLED
   Rules: 24
❌ TypeScript Rules (typescript)
   Status: DISABLED
   Rules: 35
   Disabled: 2024-12-20T10:30:00
```

#### List Specific Category
```bash
python tools/hook_cli.py list --category typescript
```

#### List Specific Rule
```bash
python tools/hook_cli.py list --rule 42
```

### Enable Commands

#### Enable Entire Category
```bash
python tools/hook_cli.py enable --category typescript --reason "Ready for production"
```

#### Enable Specific Rule
```bash
python tools/hook_cli.py enable --rule 42 --reason "Testing specific functionality"
```

### Disable Commands

#### Disable Entire Category
```bash
python tools/hook_cli.py disable --category logging --reason "Too verbose for development"
```

#### Disable Specific Rule
```bash
python tools/hook_cli.py disable --rule 90 --reason "Secrets detection too aggressive"
```

### Statistics Command

```bash
python tools/hook_cli.py stats
```
**Output:**
```
📊 Hook Statistics
==============================
Total Rules: 280
Enabled Rules: 245 (87.5%)
Disabled Rules: 35
Categories:
  Total: 9
  Enabled: 7
  Disabled: 2
```

### Export Commands

#### Export All Configuration
```bash
python tools/hook_cli.py export --output my_hooks.json
```

#### Export Only Enabled Hooks
```bash
python tools/hook_cli.py export --enabled-only --output enabled_hooks.json
```

### Reset Command

```bash
python tools/hook_cli.py reset --force
```

## 🎯 **Use Cases**

### Development Environment
```bash
# Disable strict rules for rapid prototyping
python tools/hook_cli.py disable --category typescript --reason "Prototyping phase"
python tools/hook_cli.py disable --category simple_readability --reason "Quick development"
```

### Production Environment
```bash
# Enable all rules for production
python tools/hook_cli.py enable --category typescript --reason "Production ready"
python tools/hook_cli.py enable --category simple_readability --reason "Code quality"
```

### Testing Specific Rules
```bash
# Test individual rules
python tools/hook_cli.py disable --rule 42 --reason "Testing without this rule"
python tools/hook_cli.py enable --rule 42 --reason "Rule works correctly"
```

### Team Configuration
```bash
# Export team configuration
python tools/hook_cli.py export --output team_hooks.json

# Share with team members
git add config/hook_config.json
git commit -m "Update hook configuration for team"
```

## 🔧 **Configuration File**

The hook configuration is stored in `config/hook_config.json`:

```json
{
  "version": "1.0",
  "created_at": "2024-12-20T10:00:00",
  "updated_at": "2024-12-20T10:30:00",
  "global_settings": {
    "default_status": "enabled",
    "strict_mode": true,
    "context_aware": true
  },
  "categories": {
    "typescript": {
      "name": "TypeScript Rules",
      "status": "disabled",
      "disabled_at": "2024-12-20T10:30:00",
      "disabled_reason": "Too strict for prototyping",
      "rule_count": 35
    }
  },
  "individual_rules": {
    "42": {
      "status": "disabled",
      "disabled_at": "2024-12-20T10:30:00",
      "disabled_reason": "Testing specific rule",
      "category": "basic_work"
    }
  }
}
```

## 🧪 **Testing the System**

Run the test script to verify functionality:

```bash
python tools/test_hook_cli.py
```

This will:
1. Test hook configuration management
2. Test pre-implementation validation with disabled hooks
3. Show CLI command examples

## 🔍 **Integration with Pre-Implementation Hooks**

The hook system integrates seamlessly with the pre-implementation validation:

```python
from validator.pre_implementation_hooks import PreImplementationHookManager

# Initialize hook manager
hook_manager = PreImplementationHookManager()

# Validate prompt (respects enabled/disabled hooks)
result = hook_manager.validate_before_generation(
    prompt="Create a TypeScript function",
    file_type="typescript"
)

# Result will only include violations from enabled rules
print(f"Valid: {result['valid']}")
print(f"Rules checked: {result['total_rules_checked']}")
```

## 🎯 **Best Practices**

### 1. **Start with All Rules Enabled**
```bash
# Check current status
python tools/hook_cli.py stats
```

### 2. **Disable Rules Gradually**
```bash
# Disable one category at a time
python tools/hook_cli.py disable --category typescript --reason "Testing"
```

### 3. **Document Reasons**
Always provide meaningful reasons for enabling/disabling rules:
```bash
python tools/hook_cli.py disable --rule 90 --reason "False positives in test environment"
```

### 4. **Use Categories for Broad Changes**
```bash
# Disable entire category for prototyping
python tools/hook_cli.py disable --category simple_readability --reason "Rapid prototyping"
```

### 5. **Use Individual Rules for Precision**
```bash
# Disable specific problematic rule
python tools/hook_cli.py disable --rule 42 --reason "Too restrictive for this project"
```

### 6. **Export Configurations**
```bash
# Save working configuration
python tools/hook_cli.py export --output production_hooks.json
```

## 🚨 **Troubleshooting**

### Common Issues

#### 1. **Hook CLI Not Found**
```bash
# Make sure you're in the project root
cd /path/to/ZeroUI2.0
python tools/hook_cli.py list
```

#### 2. **Configuration Not Saving**
```bash
# Check file permissions
ls -la config/hook_config.json
```

#### 3. **Rules Not Being Respected**
```bash
# Verify rule status
python tools/hook_cli.py list --rule 42
```

#### 4. **Reset to Defaults**
```bash
# Reset all configurations
python tools/hook_cli.py reset --force
```

## 📚 **Advanced Usage**

### Custom Rule Ranges
The system supports custom rule ranges for specific categories:

```python
from validator.hook_config_manager import HookConfigManager

config_manager = HookConfigManager()

# Get statistics for specific category
ts_status = config_manager.get_category_status(HookCategory.TYPESCRIPT)
print(f"TypeScript rules: {ts_status['rule_count']}")
```

### Programmatic Control
```python
from validator.hook_config_manager import HookConfigManager, HookCategory

config_manager = HookConfigManager()

# Enable category programmatically
config_manager.enable_category(HookCategory.TYPESCRIPT, "Production ready")

# Disable specific rule
config_manager.disable_rule(42, "Testing without this rule")

# Check if rule is enabled
if config_manager.is_rule_enabled(42):
    print("Rule 42 is enabled")
```

## 🎉 **Summary**

The Hook Management system provides:

✅ **Fine-grained control** over individual Constitution rules  
✅ **Category-based management** for broad changes  
✅ **CLI interface** for easy configuration  
✅ **Configuration persistence** across sessions  
✅ **Integration** with pre-implementation validation  
✅ **Statistics and reporting** for monitoring  
✅ **Export/import** for team collaboration  

This system ensures that Constitution rules can be tailored to specific development contexts while maintaining the overall quality and safety of AI-generated code.
