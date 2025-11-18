# ZeroUI 2.0 Enhanced CLI Commands

## Overview

The ZeroUI 2.0 Enhanced CLI (`tools/enhanced_cli.py`) provides advanced validation features including intelligent rule selection, performance monitoring, context-aware validation, and detailed reporting. This is the main CLI interface for the ZeroUI 2.0 Constitution Validator.

## Installation & Setup

```bash
# Navigate to project root
cd D:\Projects\ZeroUI2.0

# Install dependencies
python -m pip install -r requirements.txt

# Verify system
python tools/enhanced_cli.py --backend-status
python tools/enhanced_cli.py --rule-stats
```

## Basic Commands

### File Validation

```bash
# Validate single file
python tools/enhanced_cli.py --file script.py

# Validate directory recursively
python tools/enhanced_cli.py --directory src/ --recursive

# Validate with specific output format
python tools/enhanced_cli.py --file script.py --format json
python tools/enhanced_cli.py --file script.py --format html --output report.html
python tools/enhanced_cli.py --file script.py --format markdown
```

### Rule Management

```bash
# List all rules
python tools/enhanced_cli.py --list-rules

# Enable/disable specific rules
python tools/enhanced_cli.py --enable-rule 1
python tools/enhanced_cli.py --disable-rule 2 --disable-reason "Testing purposes"

# Search rules
python tools/enhanced_cli.py --search-rules "typescript"
python tools/enhanced_cli.py --rules-by-category "exception_handling"

# Export rules
python tools/enhanced_cli.py --export-rules
python tools/enhanced_cli.py --export-rules --export-enabled-only
```

## Advanced Features

### Backend Management

```bash
# Check backend status
python tools/enhanced_cli.py --backend-status

# Switch backends
python tools/enhanced_cli.py --switch-backend json
python tools/enhanced_cli.py --switch-backend sqlite

# Sync and verify backends
python tools/enhanced_cli.py --sync-backends
python tools/enhanced_cli.py --verify-sync
```

### Performance Monitoring

```bash
# Enable performance monitoring
python tools/enhanced_cli.py --file script.py --monitor-performance

# Check performance metrics
python tools/enhanced_cli.py --performance-stats

# Monitor with detailed output
python tools/enhanced_cli.py --file script.py --monitor-performance --verbose
```

### Context-Aware Validation

```bash
# Validate with context awareness
python tools/enhanced_cli.py --file script.py --context-aware

# Specify validation context
python tools/enhanced_cli.py --file script.py --context "production"

# Use intelligent rule selection
python tools/enhanced_cli.py --file script.py --intelligent-selection
```

## Single Source of Truth

### Rebuild from Markdown

```bash
# Rebuild all sources from markdown
python tools/enhanced_cli.py --rebuild-from-markdown

# Verify consistency after rebuild
python tools/enhanced_cli.py --verify-consistency

# Rebuild with verbose output
python tools/enhanced_cli.py --rebuild-from-markdown --verbose
```

### Consistency Verification

```bash
# Verify all sources are consistent
python tools/enhanced_cli.py --verify-consistency

# Check specific source consistency
python tools/enhanced_cli.py --verify-consistency --sources database json

# Fix inconsistencies
python tools/enhanced_cli.py --repair-sync
```

## Complete Command Reference

### File Validation Options

| Option | Description | Required | Example |
|--------|-------------|----------|---------|
| `--file FILE_PATH` | Validate single file | No | `--file script.py` |
| `--directory DIR_PATH` | Validate directory | No | `--directory src/` |
| `--recursive` | Recursive directory validation | No | `--recursive` |
| `--format FORMAT` | Output format (json, html, markdown) | No | `--format json` |
| `--output OUTPUT_FILE` | Output file path | No | `--output report.html` |
| `--max-files N` | Limit number of files processed | No | `--max-files 100` |

### Rule Management Options

| Option | Description | Required | Example |
|--------|-------------|----------|---------|
| `--list-rules` | List all rules | No | `--list-rules` |
| `--enable-rule RULE_ID` | Enable specific rule | No | `--enable-rule 1` |
| `--disable-rule RULE_ID` | Disable specific rule | No | `--disable-rule 2` |
| `--disable-reason REASON` | Reason for disabling | No | `--disable-reason "Testing"` |
| `--search-rules PATTERN` | Search rules by pattern | No | `--search-rules "typescript"` |
| `--rules-by-category CATEGORY` | Rules by category | No | `--rules-by-category "exception_handling"` |
| `--export-rules` | Export rules | No | `--export-rules` |
| `--export-enabled-only` | Export only enabled rules | No | `--export-enabled-only` |

### Backend Management Options

| Option | Description | Required | Example |
|--------|-------------|----------|---------|
| `--backend-status` | Check backend status | No | `--backend-status` |
| `--switch-backend BACKEND` | Switch backend (sqlite/json) | No | `--switch-backend json` |
| `--sync-backends` | Sync all backends | No | `--sync-backends` |
| `--verify-sync` | Verify backend sync | No | `--verify-sync` |
| `--repair-sync` | Repair sync issues | No | `--repair-sync` |

### Single Source of Truth Options

| Option | Description | Required | Example |
|--------|-------------|----------|---------|
| `--rebuild-from-markdown` | Rebuild from markdown | No | `--rebuild-from-markdown` |
| `--verify-consistency` | Verify consistency | No | `--verify-consistency` |
| `--sources SOURCE_LIST` | Specify sources to check | No | `--sources database json` |

### Performance Options

| Option | Description | Required | Example |
|--------|-------------|----------|---------|
| `--monitor-performance` | Enable performance monitoring | No | `--monitor-performance` |
| `--performance-stats` | Show performance statistics | No | `--performance-stats` |
| `--cache-enabled` | Enable caching | No | `--cache-enabled` |
| `--cache-clear` | Clear cache | No | `--cache-clear` |

### General Options

| Option | Description | Required | Example |
|--------|-------------|----------|---------|
| `--verbose` | Enable verbose output | No | `--verbose` |
| `--help` | Show help message | No | `--help` |
| `--version` | Show version information | No | `--version` |

## Common Workflows

### 1. Development Workflow

```bash
# Check system status
python tools/enhanced_cli.py --backend-status

# Validate current changes
python tools/enhanced_cli.py --directory src/ --recursive --format json

# Check rule statistics
python tools/enhanced_cli.py --rule-stats
```

### 2. Production Validation

```bash
# Validate with production context
python tools/enhanced_cli.py --directory src/ --context "production" --recursive

# Generate HTML report
python tools/enhanced_cli.py --directory src/ --format html --output production_report.html

# Monitor performance
python tools/enhanced_cli.py --directory src/ --monitor-performance --recursive
```

### 3. Rule Management

```bash
# List current rules
python tools/enhanced_cli.py --list-rules

# Disable problematic rule
python tools/enhanced_cli.py --disable-rule 42 --disable-reason "Conflicts with new architecture"

# Export current configuration
python tools/enhanced_cli.py --export-rules --export-enabled-only --output current_rules.json
```

### 4. Maintenance Mode

```bash
# Rebuild from markdown (after rule changes)
python tools/enhanced_cli.py --rebuild-from-markdown

# Verify consistency
python tools/enhanced_cli.py --verify-consistency

# Sync all backends
python tools/enhanced_cli.py --sync-backends
```

## Output Examples

### Validation Output

```
File Validation Results
======================
File: script.py
Status: ❌ FAILED
Rules Checked: 45
Violations Found: 3

Violations:
1. Rule 15: Missing type annotations
   Line 23: def process_data(data):
   Severity: HIGH
   Category: TypeScript

2. Rule 42: Missing error handling
   Line 45: result = api_call()
   Severity: MEDIUM
   Category: Exception Handling

3. Rule 78: Inconsistent naming
   Line 12: user_name vs user_name
   Severity: LOW
   Category: Coding Standards

Performance Metrics:
  Processing Time: 0.234s
  Memory Usage: 12.5MB
  Cache Hit Rate: 85%
```

### Backend Status Output

```
Backend Status
=============
Primary Backend: SQLite
Status: ✅ CONNECTED
Rules: 293
Enabled Rules: 245
Disabled Rules: 48

Secondary Backend: JSON
Status: ✅ CONNECTED
Rules: 293
Last Sync: 2025-01-23T10:30:00Z
Sync Status: ✅ IN SYNC

Configuration:
  Auto-sync: Enabled
  Cache: Enabled
  Performance Monitoring: Enabled
```

### Rule Statistics Output

```
Rule Statistics
==============
Total Rules: 293
Enabled Rules: 245 (83.6%)
Disabled Rules: 48 (16.4%)

Categories:
  TypeScript: 34 rules (32 enabled, 2 disabled)
  Exception Handling: 32 rules (30 enabled, 2 disabled)
  Teamwork: 26 rules (25 enabled, 1 disabled)
  API Contracts: 22 rules (22 enabled, 0 disabled)
  Basic Work: 18 rules (18 enabled, 0 disabled)
  Logging: 18 rules (17 enabled, 1 disabled)
  Coding Standards: 15 rules (15 enabled, 0 disabled)
  System Design: 12 rules (12 enabled, 0 disabled)
  Comments: 10 rules (10 enabled, 0 disabled)
  Platform: 10 rules (10 enabled, 0 disabled)
  Code Review: 9 rules (9 enabled, 0 disabled)
  Problem Solving: 9 rules (9 enabled, 0 disabled)
  Documentation: 3 rules (3 enabled, 0 disabled)
```

## Integration with Other Tools

### With Rule Manager

```bash
# Use enhanced CLI for validation
python tools/enhanced_cli.py --file script.py

# Use rule manager for bulk operations
python tools/rule_manager.py --enable-all
```

### With Hook CLI

```bash
# Check hook statistics
python tools/hook_cli.py stats

# Use enhanced CLI for validation
python tools/enhanced_cli.py --file script.py --context-aware
```

### With Constitution Analyzer

```bash
# Analyze constitution first
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --stats

# Use enhanced CLI for validation
python tools/enhanced_cli.py --file script.py
```

## Best Practices

### 1. Regular Validation

```bash
# Run validation before commits
python tools/enhanced_cli.py --directory src/ --recursive --format json
```

### 2. Performance Monitoring

```bash
# Monitor performance during development
python tools/enhanced_cli.py --directory src/ --monitor-performance --recursive
```

### 3. Rule Management

```bash
# Check rule status regularly
python tools/enhanced_cli.py --rule-stats

# Export configuration for backup
python tools/enhanced_cli.py --export-rules --output backup_rules.json
```

### 4. Maintenance

```bash
# Rebuild from markdown after rule changes
python tools/enhanced_cli.py --rebuild-from-markdown

# Verify consistency
python tools/enhanced_cli.py --verify-consistency
```

## Troubleshooting

### Common Issues

1. **Backend Connection Issues**
   ```bash
   # Check backend status
   python tools/enhanced_cli.py --backend-status

   # Repair sync issues
   python tools/enhanced_cli.py --repair-sync
   ```

2. **Performance Issues**
   ```bash
   # Check performance stats
   python tools/enhanced_cli.py --performance-stats

   # Clear cache
   python tools/enhanced_cli.py --cache-clear
   ```

3. **Rule Inconsistencies**
   ```bash
   # Verify consistency
   python tools/enhanced_cli.py --verify-consistency

   # Rebuild from markdown
   python tools/enhanced_cli.py --rebuild-from-markdown
   ```

### Debug Mode

```bash
# Enable verbose output
python tools/enhanced_cli.py --file script.py --verbose

# Check help for additional options
python tools/enhanced_cli.py --help
```

## File Locations

- **Enhanced CLI**: `tools/enhanced_cli.py`
- **Database**: `config/constitution_rules.db`
- **JSON Export**: `config/constitution_rules.json`
- **Config**: `config/constitution_config.json`
- **Master Constitution**: `docs/architecture/ZeroUI2.0_Master_Constitution.md`

## Support

For issues or questions:
1. Check backend status: `python tools/enhanced_cli.py --backend-status`
2. Verify consistency: `python tools/enhanced_cli.py --verify-consistency`
3. Check help: `python tools/enhanced_cli.py --help`
4. Review this documentation

---

*Last updated: 2025-01-23*
*ZeroUI 2.0 Enhanced CLI v1.0*
