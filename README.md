# ZeroUI 2.0 - 75 Rule Validation System

A comprehensive validation system that enforces all 75 unique rules from the ZeroUI 2.0 constitutions across pre-commit hooks, CI/CD pipelines, and IDE integration.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Pre-commit Hook

```bash
python tools/hooks/install.py install
```

### 3. Run Validation

```bash
# Validate new changes (fast)
python tools/validator/rule_engine.py --mode=diff --report=json

# Validate entire codebase
python tools/validator/rule_engine.py --mode=full --report=html
```

## 📊 What It Validates

The system validates **75 unique rules** across 6 constitutions:

- **🔒 Security Rules** (8 rules) - No secrets/PII, proper secret management
- **🌐 API Contract Rules** (18 rules) - HTTP standards, versioning, idempotency
- **💻 Code Quality Rules** (15 rules) - Python/TS standards, testing, migrations
- **📝 Comment Rules** (9 rules) - Simple English, documentation standards
- **📁 Structure Rules** (12 rules) - Folder organization, path management
- **📋 Logging Rules** (20 rules) - JSONL format, trace context, performance

## 🛠️ Integration Points

### Pre-commit Hook
- Validates staged files only
- Fast execution (<5 seconds)
- Blocks commits on violations

### CI/CD Pipeline
- Comprehensive validation of all 75 rules
- Generates detailed reports
- Posts results as PR comments

### IDE Integration
- Real-time validation in VS Code
- Linter integration
- Error highlighting

## 📈 Report Formats

- **JSON** - Machine-readable, API integration
- **HTML** - Beautiful, interactive reports
- **Markdown** - GitHub-compatible, PR comments

## 🔧 Usage Examples

### Command Line

```bash
# Validate specific categories
python tools/validator/rule_engine.py --categories security code_quality

# Validate specific files
python tools/validator/rule_engine.py --files src/api/auth.py src/models/user.py

# Generate HTML report
python tools/validator/rule_engine.py --mode=full --report=html --output=report.html
```

### CI/CD

```bash
# Validate PR
python tools/ci/validate-pr.py --pr 123 --post-comment

# Validate full codebase
python tools/ci/validate-pr.py --full --output-dir=reports/
```

### GitHub Actions

The system includes a GitHub Actions workflow that automatically:
- Runs on every pull request
- Validates all 75 rules
- Posts results as PR comments
- Uploads detailed reports

## 📚 Documentation

- [Complete Documentation](docs/75-rule-validation-system.md)
- [Troubleshooting Guide](docs/75-rule-validation-system.md#troubleshooting)
- [Rule Reference](tools/validator/rules.json)

## 🎯 Success Criteria

- ✅ All 75 rules have automated validators
- ✅ Pre-commit hook runs in <5 seconds
- ✅ CI/CD generates comprehensive reports
- ✅ 100% rule coverage with tests
- ✅ Clear error messages with suggestions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new rules
4. Submit a pull request

## 📄 License

Part of the ZeroUI 2.0 project. See project license for details.

---

**Total Rules: 75** | **Categories: 6** | **Integration Points: 3** | **Report Formats: 3**
