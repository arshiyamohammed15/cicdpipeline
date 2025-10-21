# ZeroUI 2.0 Local Deployment Guide

## Overview

This guide covers deploying and running the ZeroUI 2.0 Constitution Validator in **Local without Docker** mode. The system is a Python-based code validation tool that enforces 218 enterprise-grade development rules.

## Prerequisites

- **Python 3.9+** (tested with Python 3.11.9)
- **Windows/Linux/macOS** (tested on Windows 10)
- **No Docker required** - runs natively on the host system

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
python -m pip install -r requirements.txt
```

### 2. Verify System

```bash
# Check backend status and rule statistics
python enhanced_cli.py --backend-status
python enhanced_cli.py --rule-stats
```

### 3. Basic Usage

```bash
# Validate a single file
python enhanced_cli.py --file script.py

# Validate a directory
python enhanced_cli.py --directory src/ --recursive

# Generate HTML report
python enhanced_cli.py --directory src/ --format html --output report.html
```

## System Architecture

### Core Components

- **`enhanced_cli.py`** - Main CLI interface with advanced features
- **`config/constitution/`** - Rule management and database system
- **`validator/`** - Code analysis and validation engine
- **`ZeroUI2.0_Master_Constitution.md`** - Source of truth for all 218 rules

### Database System

- **SQLite Database** (`config/constitution_rules.db`) - Primary storage
- **JSON Fallback** (`config/constitution_rules.json`) - Backup storage
- **Auto-sync** - Keeps both backends synchronized
- **218 Rules** - Complete rule set with 13 categories

## Rule Categories

| Category | Rules | Description |
|----------|-------|-------------|
| **TypeScript** | 34 | Type safety and modern JavaScript patterns |
| **Exception Handling** | 32 | Error handling and recovery patterns |
| **Teamwork** | 26 | Collaboration and communication rules |
| **API Contracts** | 22 | HTTP API design and contracts |
| **Basic Work** | 18 | Fundamental development practices |
| **Logging** | 18 | Structured logging and monitoring |
| **Coding Standards** | 15 | Code quality and consistency |
| **System Design** | 12 | Architecture and design patterns |
| **Comments** | 10 | Documentation and code comments |
| **Platform** | 10 | Platform-specific requirements |
| **Code Review** | 9 | Review processes and standards |
| **Problem Solving** | 9 | Debugging and issue resolution |
| **Documentation** | 3 | Documentation standards |

## CLI Commands

### File Validation

```bash
# Validate single file
python enhanced_cli.py --file path/to/file.py

# Validate directory recursively
python enhanced_cli.py --directory src/ --recursive

# Output formats
python enhanced_cli.py --file script.py --format json
python enhanced_cli.py --file script.py --format html --output report.html
python enhanced_cli.py --file script.py --format markdown
```

### Rule Management

```bash
# List all rules
python enhanced_cli.py --list-rules

# Enable/disable specific rules
python enhanced_cli.py --enable-rule 1
python enhanced_cli.py --disable-rule 2 --disable-reason "Testing purposes"

# Search rules
python enhanced_cli.py --search-rules "typescript"
python enhanced_cli.py --rules-by-category "exception_handling"

# Export rules
python enhanced_cli.py --export-rules
python enhanced_cli.py --export-rules --export-enabled-only
```

### Backend Management

```bash
# Check backend status
python enhanced_cli.py --backend-status

# Switch backends
python enhanced_cli.py --switch-backend json
python enhanced_cli.py --switch-backend sqlite

# Sync and verify backends
python enhanced_cli.py --sync-backends
python enhanced_cli.py --verify-sync
```

## Configuration

### Main Configuration

The system uses `config/constitution_config.json` for configuration:

```json
{
  "version": "2.0",
  "primary_backend": "sqlite",
  "total_rules": 218,
  "sync": {
    "enabled": true,
    "auto_sync_on_write": true
  }
}
```

### Rule Configuration

Individual rules can be enabled/disabled:

```json
{
  "rules": {
    "1": {
      "enabled": 1,
      "updated_at": "2025-10-20T15:05:53.387074"
    }
  }
}
```

## Validation Features

### Output Formats

- **Console** - Human-readable terminal output
- **JSON** - Machine-readable structured data
- **HTML** - Rich web-based reports
- **Markdown** - Documentation-friendly format

### Performance Monitoring

- **Processing Time** - Per-file validation timing
- **Cache Hit Rates** - Performance optimization metrics
- **Memory Usage** - Resource consumption tracking

### Error Handling

- **Structured Logging** - JSONL format with correlation IDs
- **Error Recovery** - Graceful handling of validation failures
- **User-Friendly Messages** - Clear, actionable error descriptions

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure all dependencies are installed
   python -m pip install -r requirements.txt
   ```

2. **Database Issues**
   ```bash
   # Check database status
   python enhanced_cli.py --backend-status
   
   # Repair synchronization
   python enhanced_cli.py --repair-sync
   ```

3. **Rule Synchronization**
   ```bash
   # Verify all sources are in sync
   python sync_validation.py
   ```

### Performance Issues

- **Large Files**: Use `--max-files` to limit processing
- **Memory Usage**: Process files in smaller batches
- **Cache**: Enable caching for repeated validations

## Development

### Adding New Rules

1. Add rule to `ZeroUI2.0_Master_Constitution.md`
2. Update category definitions in `config/constitution/rule_extractor.py`
3. Re-run rule extraction:
   ```bash
   python -c "from config.constitution.rule_extractor import ConstitutionRuleExtractor; extractor = ConstitutionRuleExtractor(); rules = extractor.extract_all_rules(); print(f'Extracted {len(rules)} rules')"
   ```

### Testing

```bash
# Run validation tests
python sync_validation.py

# Test CLI functionality
python enhanced_cli.py --help
python enhanced_cli.py --rule-stats
```

## Production Deployment

### Local Production Setup

1. **Install Dependencies**
   ```bash
   python -m pip install -r requirements.txt
   ```

2. **Initialize System**
   ```bash
   python enhanced_cli.py --backend-status
   ```

3. **Verify Rules**
   ```bash
   python sync_validation.py
   ```

4. **Test Validation**
   ```bash
   python enhanced_cli.py --file your_code.py
   ```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Validate Code
  run: |
    python enhanced_cli.py src/ --format json --output validation.json
    if [ $? -ne 0 ]; then
      echo "Validation failed"
      exit 1
    fi
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: constitution-validator
        name: ZEROUI Constitution Validator
        entry: python enhanced_cli.py
        language: system
        files: \.py$
        args: [--format=json, --severity=error]
```

## Support

### System Information

- **Version**: 2.0
- **Total Rules**: 218
- **Categories**: 13
- **Backend**: SQLite + JSON hybrid
- **Platform**: Cross-platform (Windows/Linux/macOS)

### Performance Metrics

- **Startup Time**: < 2 seconds
- **Processing Speed**: < 2 seconds per file
- **Memory Usage**: Optimized for large codebases
- **Accuracy**: < 2% false positives for critical rules

## License

This project follows the ZEROUI 2.0 Constitution principles for open, transparent, and ethical development.
