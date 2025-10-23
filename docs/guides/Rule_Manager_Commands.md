# ZeroUI 2.0 Rule Manager Commands

## Overview

The ZeroUI 2.0 Rule Manager (`tools/rule_manager.py`) provides comprehensive rule management capabilities across all 5 sources in the constitution system:

- **Database** (SQLite)
- **JSON Export** (constitution_rules.json)
- **Config** (constitution_config.json)
- **Hooks** (Pre-implementation hooks)
- **Markdown** (read-only for content)

## Installation & Setup

```bash
# Navigate to project root
cd D:\Projects\ZeroUI2.0

# Ensure Python path includes project root
# The script automatically adds the project root to sys.path
```

## Parameter Format Guide

The rule manager uses **two different parameter formats**:

### **Simple String Parameters** (No escaping needed)
- `--reason`: Simple text string
- Example: `--reason "System maintenance"`

### **JSON Parameters** (PowerShell requires escaping)
- `--config-data`: JSON object string
- Example: `--config-data '{\"key\": \"value\"}'`

**Why the difference?**
- `--reason` is a simple text field (no JSON parsing)
- `--config-data` is parsed as JSON (requires valid JSON syntax)

## Basic Commands

### Enable/Disable Individual Rules

```bash
# Enable a specific rule
python tools/rule_manager.py --enable-rule 150

# Disable a specific rule with reason (SIMPLE STRING - no escaping needed)
python tools/rule_manager.py --disable-rule 150 --reason "Too restrictive for current project"

# Enable with custom configuration (JSON FORMAT - PowerShell requires escaped quotes)
python tools/rule_manager.py --enable-rule 150 --config-data '{\"priority\": \"high\", \"notes\": \"Critical rule\"}'
```

### Enable/Disable All Rules

```bash
# Enable all rules
python tools/rule_manager.py --enable-all

# Disable all rules for maintenance (SIMPLE STRING - no escaping needed)
python tools/rule_manager.py --disable-all --reason "System maintenance"

# Enable all rules with configuration (JSON FORMAT - PowerShell requires escaped quotes)
python tools/rule_manager.py --enable-all --config-data '{\"maintenance_complete\": true, \"enabled_at\": \"2024-01-15\"}'
```

## Status and Monitoring

### Check Rule Status

```bash
# Show status of all rules
python tools/rule_manager.py --status

# Show status of a specific rule
python tools/rule_manager.py --status-rule 150

# Example output:
# Rule 150:
#   Markdown exists: Yes
#   Database enabled: True
#   JSON export enabled: True
#   Config enabled: True
#   Hooks enabled: True
#   Consistent: Yes
```

### Synchronize Sources

```bash
# Synchronize all sources to fix inconsistencies
python tools/rule_manager.py --sync-all

# Example output:
# SYNC ALL SOURCES RESULTS:
# ==================================================
#   Result: OK All sources are already consistent
#   Fixed inconsistencies: 0
```

## Advanced Options

### Source Selection

Control which sources to update (default: all except markdown):

```bash
# Update only database and config
python tools/rule_manager.py --disable-rule 150 --sources database config

# Update only JSON export
python tools/rule_manager.py --enable-rule 150 --sources json_export

# Update all sources (including markdown - read-only)
python tools/rule_manager.py --enable-rule 150 --sources markdown database json_export config hooks
```

### Configuration Data

Add custom configuration when enabling rules:

```bash
# Enable with priority and notes (PowerShell - use escaped quotes)
python tools/rule_manager.py --enable-rule 150 --config-data '{\"priority\": \"high\", \"notes\": \"Critical for security\"}'

# Enable all with maintenance metadata (PowerShell - use escaped quotes)
python tools/rule_manager.py --enable-all --config-data '{\"maintenance_complete\": true, \"version\": \"2.1\", \"updated_by\": \"admin\"}'
```

### Detailed Reasons

Provide detailed reasons for disabling rules:

```bash
# Disable with specific reason
python tools/rule_manager.py --disable-rule 150 --reason "Conflicts with new architecture requirements"

# Disable all with maintenance reason
python tools/rule_manager.py --disable-all --reason "Database migration in progress - estimated 2 hours"
```

## Complete Command Reference

### Command Line Options

| Option | Description | Required | Example |
|--------|-------------|----------|---------|
| `--enable-rule RULE_NUMBER` | Enable a specific rule | No | `--enable-rule 150` |
| `--disable-rule RULE_NUMBER` | Disable a specific rule | No | `--disable-rule 150` |
| `--enable-all` | Enable all rules | No | `--enable-all` |
| `--disable-all` | Disable all rules | No | `--disable-all` |
| `--reason REASON` | Reason for disabling rules | No | `--reason "Maintenance mode"` |
| `--config-data CONFIG_DATA` | JSON configuration data | No | `--config-data '{"priority": "high"}'` |
| `--status` | Show status of all rules | No | `--status` |
| `--status-rule RULE_NUMBER` | Show status of a specific rule | No | `--status-rule 150` |
| `--sync-all` | Synchronize all sources | No | `--sync-all` |
| `--sources SOURCE_LIST` | Specify which sources to update | No | `--sources database config hooks` |
| `--help` | Show help message | No | `--help` |

### Available Sources

| Source | Description | Read/Write |
|--------|-------------|------------|
| `markdown` | Master Constitution markdown file | Read-only for content |
| `database` | SQLite constitution rules database | Read/Write |
| `json_export` | JSON export file | Read/Write |
| `config` | Configuration file | Read/Write |
| `hooks` | Pre-implementation hooks configuration | Read/Write |

## Common Workflows

### 1. Maintenance Mode

```bash
# Enter maintenance mode
python tools/rule_manager.py --disable-all --reason "Scheduled maintenance - 2024-01-15 14:00-16:00"

# Perform maintenance tasks...

# Exit maintenance mode
python tools/rule_manager.py --enable-all --config-data '{"maintenance_complete": true, "completed_at": "2024-01-15T16:00:00Z"}'
```

### 2. Rule Testing

```bash
# Disable a rule for testing
python tools/rule_manager.py --disable-rule 150 --reason "Testing alternative approach"

# Run tests...

# Re-enable the rule
python tools/rule_manager.py --enable-rule 150 --config-data '{"test_complete": true, "result": "passed"}'
```

### 3. Selective Updates

```bash
# Update only database and config (skip JSON export and hooks)
python tools/rule_manager.py --disable-rule 150 --sources database config --reason "Temporary disable for debugging"

# Update only JSON export and hooks
python tools/rule_manager.py --enable-rule 150 --sources json_export hooks
```

### 4. Consistency Checking

```bash
# Check overall status
python tools/rule_manager.py --status

# Check specific rule
python tools/rule_manager.py --status-rule 150

# Fix any inconsistencies
python tools/rule_manager.py --sync-all
```

## Output Examples

### Status Output

```
RULE STATUS SUMMARY:
==================================================
Total rules: 293
Consistent rules: 293
Inconsistent rules: 0
```

### Enable/Disable Output

```
ENABLE RULE 150 RESULTS:
==================================================
  database: OK Enabled in database
  config: OK Enabled in config
  json_export: OK Enabled in JSON export
  hooks: OK Enabled in hooks
```

### Error Handling

```
DISABLE RULE 150 RESULTS:
==================================================
  database: OK Disabled in database
  config: FAIL Config error: Permission denied
  json_export: OK Disabled in JSON export
  hooks: OK Disabled in hooks
```

## Best Practices

### 1. Always Provide Reasons

```bash
# Good
python tools/rule_manager.py --disable-rule 150 --reason "Conflicts with new security requirements"

# Avoid
python tools/rule_manager.py --disable-rule 150
```

### 2. Use Configuration Data for Context

```bash
# Good
python tools/rule_manager.py --enable-rule 150 --config-data '{"updated_by": "admin", "version": "2.1", "notes": "Security enhancement"}'

# Avoid
python tools/rule_manager.py --enable-rule 150
```

### 3. Check Status Before and After

```bash
# Before changes
python tools/rule_manager.py --status-rule 150

# Make changes
python tools/rule_manager.py --disable-rule 150 --reason "Testing"

# After changes
python tools/rule_manager.py --status-rule 150
```

### 4. Use Sync for Consistency

```bash
# After bulk operations
python tools/rule_manager.py --enable-all
python tools/rule_manager.py --sync-all
```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   ```bash
   # Check file permissions
   ls -la config/constitution_config.json
   ls -la config/constitution_rules.json
   ```

2. **Inconsistent Sources**
   ```bash
   # Check status
   python tools/rule_manager.py --status
   
   # Fix inconsistencies
   python tools/rule_manager.py --sync-all
   ```

3. **Rule Not Found**
   ```bash
   # Check if rule exists
   python tools/rule_manager.py --status-rule 150
   
   # List all rules
   python tools/rule_manager.py --status
   ```

4. **PowerShell JSON Issues**
   ```bash
   # ❌ Wrong (PowerShell strips quotes from JSON)
   python tools/rule_manager.py --enable-rule 150 --config-data '{"priority": "high"}'
   
   # ✅ Correct (PowerShell - use escaped quotes for JSON)
   python tools/rule_manager.py --enable-rule 150 --config-data '{\"priority\": \"high\"}'
   
   # ✅ Simple strings work fine (no escaping needed)
   python tools/rule_manager.py --disable-rule 150 --reason "System maintenance"
   
   # Example with multiple JSON properties
   python tools/rule_manager.py --enable-all --config-data '{\"maintenance_complete\": true, \"version\": \"2.1\"}'
   ```

### Debug Mode

```bash
# Enable verbose output (if implemented)
python tools/rule_manager.py --enable-rule 150 --verbose

# Check help for additional options
python tools/rule_manager.py --help
```

## Integration with Other Tools

### With Constitution Analyzer

```bash
# Check Enable/Disable consistency
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --validate-enable-disable

# Use rule manager to fix issues
python tools/rule_manager.py --sync-all
```

### With Enhanced CLI

```bash
# Use existing CLI for individual rule management
python tools/enhanced_cli.py --enable-rule 150
python tools/enhanced_cli.py --disable-rule 150 --disable-reason "Testing"

# Use rule manager for bulk operations
python tools/rule_manager.py --enable-all
```

## File Locations

- **Rule Manager**: `tools/rule_manager.py`
- **Database**: `config/constitution_rules.db`
- **JSON Export**: `config/constitution_rules.json`
- **Config**: `config/constitution_config.json`
- **Hooks**: `config/hook_config.json`
- **Markdown**: `docs/architecture/ZeroUI2.0_Master_Constitution.md`

## Support

For issues or questions:
1. Check the status: `python tools/rule_manager.py --status`
2. Sync sources: `python tools/rule_manager.py --sync-all`
3. Check help: `python tools/rule_manager.py --help`
4. Review this documentation

---

*Last updated: 2025-01-23*
*ZeroUI 2.0 Rule Manager v1.1*
