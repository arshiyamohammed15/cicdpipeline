# ZEROUI 2.0 Constitution Validator - Test Suite

Comprehensive test suite for all validator categories with 100% rule coverage.

## Overview

This test suite provides enterprise-grade testing for 18 validator categories covering 216+ constitution rules.

## Test Structure

```
validator/rules/tests/
├── __init__.py                      # Test package initialization
├── base_test.py                     # Base test framework with utilities
├── test_utils.py                    # Test utilities and helpers
├── fixtures/                        # Test fixtures and sample data
│   ├── __init__.py
│   ├── code_samples.py             # Reusable code samples
│   ├── config_samples.py           # Mock configurations
│   └── mock_files.py               # Mock file structures
├── test_api_contracts.py           # API contracts validation tests (19 rules)
├── test_architecture.py            # Architecture validation tests
├── test_basic_work.py              # Basic work principles tests
├── test_code_review.py             # Code review standards tests
├── test_coding_standards.py        # Coding standards tests (22 rules)
├── test_comments.py                # Documentation tests
├── test_exception_handling.py      # Exception handling tests (32 rules)
├── test_folder_standards.py        # Folder organization tests
├── test_logging.py                 # Logging standards tests
├── test_performance.py             # Performance validation tests
├── test_platform.py                # Platform-specific tests
├── test_privacy.py                 # Privacy & security tests (5 rules)
├── test_problem_solving.py         # Problem-solving tests
├── test_quality.py                 # Code quality tests
├── test_requirements.py            # Requirements validation tests
├── test_storage_governance.py      # Storage governance tests (13 rules)
├── test_system_design.py           # System design tests
├── test_teamwork.py                # Teamwork tests
├── test_typescript.py              # TypeScript validation tests (34 rules)
├── test_config_integration.py      # Configuration integration tests
├── test_e2e_validation.py          # End-to-end validation tests
├── run_all_tests.py                # Test runner script
└── README.md                       # This file
```

## Running Tests

### Run All Tests

```bash
# From project root
python -m validator.rules.tests.run_all_tests

# Or using unittest directly
python -m unittest discover validator/rules/tests
```

### Run Specific Test File

```bash
# Run storage governance tests
python -m unittest validator.rules.tests.test_storage_governance

# Run privacy tests
python -m unittest validator.rules.tests.test_privacy

# Run exception handling tests
python -m unittest validator.rules.tests.test_exception_handling
```

### Run Specific Test Class

```bash
python -m unittest validator.rules.tests.test_storage_governance.TestStorageGovernanceValidator
```

### Run Specific Test Method

```bash
python -m unittest validator.rules.tests.test_storage_governance.TestStorageGovernanceValidator.test_rule_216_kebab_case_valid
```

## Test Categories

### Critical Priority (Security & Architecture)
- **test_api_contracts.py** - 19 rules covering API design, versioning, idempotency
- **test_exception_handling.py** - 32 rules for error handling, retries, AI safety
- **test_privacy.py** - 5 rules for credential protection, PII, encryption

### High Priority (Code Quality & Standards)
- **test_coding_standards.py** - 22 rules for naming, complexity, type hints
- **test_typescript.py** - 34 rules for TypeScript validation
- **test_architecture.py** - 7 rules for separation of concerns, hybrid design
- **test_code_review.py** - Code review checklist compliance

### Medium Priority (Development Process)
- **test_basic_work.py** - Core development principles
- **test_requirements.py** - Specification compliance
- **test_performance.py** - Optimization patterns
- **test_logging.py** - Logging standards
- **test_comments.py** - Documentation standards
- **test_folder_standards.py** - Directory organization

### Standard Priority (Supporting Categories)
- **test_quality.py** - Code quality metrics
- **test_system_design.py** - Design patterns
- **test_problem_solving.py** - Solution approaches
- **test_platform.py** - Platform compatibility
- **test_teamwork.py** - Collaboration standards

### Integration Tests
- **test_config_integration.py** - Configuration file validation
- **test_e2e_validation.py** - Complete workflow testing

## Test Coverage

### Rule Coverage by Category
- Storage Governance: 13 rules (R216-R228)
- Exception Handling: 32 rules (R150-R181)
- API Contracts: 19 rules (R013-R026, R080, R083-R086)
- TypeScript: 34 rules (R182-R215)
- Coding Standards: 22 rules (R027-R045, R087-R088)
- Privacy & Security: 5 rules (R003, R011, R012, R027, R036)
- Architecture: 7 rules
- And more...

### Test Methodology
Each rule typically has:
1. **Valid case test** - Code that passes the rule
2. **Violation test** - Code that violates the rule
3. **Edge case tests** - Boundary conditions
4. **Severity verification** - Correct ERROR/WARNING/INFO level
5. **Integration test** - Multiple rules together

## Writing New Tests

### Example Test Structure

```python
import unittest
from validator.rules.your_validator import YourValidator
from validator.models import Severity
from .base_test import BaseValidatorTest


class TestYourValidator(unittest.TestCase):
    """Test suite for your validator rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = YourValidator()
        self.test_file_path = "test.py"
    
    def test_rule_XXX_valid(self):
        """Test Rule XXX: Valid scenario."""
        content = '''
# Valid code here
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        self.assertEqual(len(violations), 0)
    
    def test_rule_XXX_violation(self):
        """Test Rule XXX: Violation scenario."""
        content = '''
# Code that violates rule
'''
        violations = self.validator.validate(self.test_file_path, content)
        
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 'RXXX')
        self.assertEqual(violations[0].severity, Severity.ERROR)
```

### Using Base Test Utilities

```python
from .base_test import BaseValidatorTest

class TestYourValidator(BaseValidatorTest):
    def test_with_utilities(self):
        # Use helper methods
        self.assertViolation(violations, 'R123', severity=Severity.ERROR)
        self.assertNoViolation(violations, 'R124')
        self.assertViolationCount(violations, 2)
        
        # Load config
        config = self.loadConfigRule('your_config.json')
        
        # Parse code
        tree = self.parseCode(content)
```

## Test Standards

### Requirements
- ✓ No TODOs or placeholders
- ✓ No hardcoded values without context
- ✓ Proper error messages in assertions
- ✓ Comprehensive docstrings
- ✓ Each rule has minimum 3 test scenarios
- ✓ Integration tests for each validator

### Naming Conventions
- Test files: `test_<category>.py`
- Test classes: `Test<Category>Validator`
- Test methods: `test_rule_<rule_id>_<scenario>`
- Example: `test_rule_R216_kebab_case_valid()`

## CI/CD Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/test.yml
- name: Run validator tests
  run: python -m validator.rules.tests.run_all_tests
```

## Coverage Goals

- Overall code coverage: >95%
- Rule coverage: 100%
- Validator coverage: 100%
- Configuration coverage: 100%

## Troubleshooting

### Import Errors
Ensure you're running from the project root:
```bash
cd /path/to/ZeroUI2.0
python -m validator.rules.tests.run_all_tests
```

### Skipped Tests
Some tests skip if configuration files are missing. This is normal for partial implementations.

### Performance Issues
If tests run slowly:
- Check for large sample files
- Verify no infinite loops in validators
- Use smaller code samples for basic validation

## Contributing

When adding new validators:
1. Create comprehensive test file
2. Include valid, violation, and edge case tests
3. Add integration tests
4. Update this README
5. Ensure all tests pass before committing

## Resources

- [ZEROUI Constitution](../../../docs/constitution/)
- [Validator Documentation](../../README.md)
- [Code Samples](fixtures/code_samples.py)

## Support

For issues or questions about tests:
1. Check existing test files for examples
2. Review base_test.py for available utilities
3. Consult validator implementations

---

**Test Suite Version:** 1.0.0  
**Last Updated:** 2025-10-20  
**Total Tests:** 200+  
**Rule Coverage:** 216+ rules

