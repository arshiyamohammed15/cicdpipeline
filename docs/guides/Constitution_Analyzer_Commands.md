# ZeroUI 2.0 Constitution Analyzer Commands

## Overview

The ZeroUI 2.0 Constitution Analyzer (`tools/constitution_analyzer.py`) provides comprehensive analysis and validation of the Master Constitution markdown file. This tool serves as the single source of truth for constitution analysis and rule extraction.

## Installation & Setup

```bash
# Navigate to project root
cd D:\Projects\ZeroUI2.0

# Ensure Python path includes project root
# The script automatically adds the project root to sys.path
```

## Basic Commands

### Analyze Constitution File

```bash
# Analyze the master constitution file
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md

# Analyze with specific output format
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --output analysis.json

# Analyze with verbose output
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --verbose
```

### Validate Rule Structure

```bash
# Validate rule numbering and structure
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --validate-structure

# Check for duplicate rules
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --check-duplicates

# Validate enable/disable consistency
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --validate-enable-disable
```

## Advanced Analysis

### Rule Extraction

```bash
# Extract all rules to JSON
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --extract-rules --output rules.json

# Extract rules by category
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --extract-category "typescript"

# Extract rules with specific patterns
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --extract-pattern "security"
```

### Statistical Analysis

```bash
# Generate rule statistics
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --stats

# Analyze rule distribution by category
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --category-stats

# Check rule complexity metrics
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --complexity-analysis
```

## Output Formats

### JSON Output

```bash
# Export analysis to JSON
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --format json --output analysis.json
```

**Example JSON Output:**
```json
{
  "analysis": {
    "total_rules": 293,
    "categories": {
      "typescript": 34,
      "exception_handling": 32,
      "teamwork": 26
    },
    "validation_results": {
      "structure_valid": true,
      "duplicates_found": 0,
      "enable_disable_consistent": true
    }
  }
}
```

### Markdown Report

```bash
# Generate markdown report
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --format markdown --output report.md
```

### Console Output

```bash
# Default console output
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md
```

## Complete Command Reference

### Command Line Options

| Option | Description | Required | Example |
|--------|-------------|----------|---------|
| `INPUT_FILE` | Path to constitution markdown file | Yes | `docs/architecture/ZeroUI2.0_Master_Constitution.md` |
| `--output OUTPUT_FILE` | Output file path | No | `--output analysis.json` |
| `--format FORMAT` | Output format (json, markdown, console) | No | `--format json` |
| `--verbose` | Enable verbose output | No | `--verbose` |
| `--validate-structure` | Validate rule structure | No | `--validate-structure` |
| `--check-duplicates` | Check for duplicate rules | No | `--check-duplicates` |
| `--validate-enable-disable` | Validate enable/disable consistency | No | `--validate-enable-disable` |
| `--extract-rules` | Extract rules to output | No | `--extract-rules` |
| `--extract-category CATEGORY` | Extract rules by category | No | `--extract-category "typescript"` |
| `--extract-pattern PATTERN` | Extract rules matching pattern | No | `--extract-pattern "security"` |
| `--stats` | Generate statistics | No | `--stats` |
| `--category-stats` | Category statistics | No | `--category-stats` |
| `--complexity-analysis` | Rule complexity analysis | No | `--complexity-analysis` |
| `--help` | Show help message | No | `--help` |

## Common Workflows

### 1. Initial Analysis

```bash
# Basic analysis of constitution file
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --stats --verbose
```

### 2. Rule Validation

```bash
# Validate all aspects of the constitution
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md \
  --validate-structure \
  --check-duplicates \
  --validate-enable-disable \
  --verbose
```

### 3. Rule Extraction

```bash
# Extract all rules for processing
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md \
  --extract-rules \
  --format json \
  --output extracted_rules.json
```

### 4. Category Analysis

```bash
# Analyze specific category
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md \
  --extract-category "typescript" \
  --category-stats \
  --output typescript_analysis.json
```

## Integration with Other Tools

### With Rule Manager

```bash
# Analyze constitution first
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --validate-structure

# Then use rule manager for bulk operations
python tools/rule_manager.py --sync-all
```

### With Enhanced CLI

```bash
# Extract rules for enhanced CLI
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --extract-rules --output rules.json

# Use enhanced CLI for validation
python tools/enhanced_cli.py --file script.py --rules-file rules.json
```

### With Hook CLI

```bash
# Analyze constitution for hook configuration
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --stats

# Configure hooks based on analysis
python tools/hook_cli.py stats
```

## Output Examples

### Statistics Output

```
Constitution Analysis Results
============================
Total Rules: 293
Categories:
  TypeScript: 34 rules
  Exception Handling: 32 rules
  Teamwork: 26 rules
  API Contracts: 22 rules
  Basic Work: 18 rules
  Logging: 18 rules
  Coding Standards: 15 rules
  System Design: 12 rules
  Comments: 10 rules
  Platform: 10 rules
  Code Review: 9 rules
  Problem Solving: 9 rules
  Documentation: 3 rules

Validation Results:
  Structure Valid: ✓
  No Duplicates: ✓
  Enable/Disable Consistent: ✓
```

### Validation Output

```
Structure Validation
====================
✓ Rule numbering is sequential
✓ No gaps in rule numbers
✓ All rules have proper headers
✓ Categories are properly defined

Duplicate Check
===============
✓ No duplicate rules found
✓ All rule numbers are unique
✓ No content duplication

Enable/Disable Consistency
==========================
✓ All enable/disable markers are consistent
✓ No conflicting states found
✓ Proper syntax for all markers
```

## Best Practices

### 1. Regular Analysis

```bash
# Run analysis before major changes
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --validate-structure
```

### 2. Pre-commit Validation

```bash
# Validate before committing changes
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md \
  --validate-structure \
  --check-duplicates \
  --validate-enable-disable
```

### 3. Documentation Updates

```bash
# Generate updated statistics
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --stats --output stats.json
```

## Troubleshooting

### Common Issues

1. **File Not Found**
   ```bash
   # Check file path
   ls -la docs/architecture/ZeroUI2.0_Master_Constitution.md
   ```

2. **Permission Errors**
   ```bash
   # Check file permissions
   ls -la docs/architecture/ZeroUI2.0_Master_Constitution.md
   ```

3. **Output File Issues**
   ```bash
   # Check output directory permissions
   ls -la output_directory/
   ```

### Debug Mode

```bash
# Enable verbose output for debugging
python tools/constitution_analyzer.py docs/architecture/ZeroUI2.0_Master_Constitution.md --verbose

# Check help for additional options
python tools/constitution_analyzer.py --help
```

## File Locations

- **Constitution Analyzer**: `tools/constitution_analyzer.py`
- **Master Constitution**: `docs/architecture/ZeroUI2.0_Master_Constitution.md`
- **Output Files**: User-specified or current directory

## Support

For issues or questions:
1. Check the file path: `ls -la docs/architecture/ZeroUI2.0_Master_Constitution.md`
2. Run with verbose output: `python tools/constitution_analyzer.py --verbose`
3. Check help: `python tools/constitution_analyzer.py --help`
4. Review this documentation

---

*Last updated: 2025-01-23*
*ZeroUI 2.0 Constitution Analyzer v1.0*
