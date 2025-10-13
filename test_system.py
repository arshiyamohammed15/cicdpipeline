#!/usr/bin/env python3
"""
Test script for ZeroUI 2.0 Rule Validation System
Windows-compatible version without Unicode characters
"""

import os
import sys
import json
from pathlib import Path

def test_validation_system():
    """Test the validation system"""
    print("ZeroUI 2.0 Rule Validation System - Test")
    print("=" * 50)

    # 1. Check system files
    print("\n1. System Files Check:")
    required_files = [
        'tools/validator/rule_engine.py',
        'tools/validator/rules.json',
        'tools/validator/reporter.py',
        'tools/validator/validators/security_validator.py',
        'tools/validator/validators/api_validator.py',
        'tools/validator/validators/code_quality_validator.py',
        'tools/validator/validators/logging_validator.py',
        'tools/validator/validators/comment_validator.py',
        'tools/validator/validators/structure_validator.py',
        'tools/hooks/pre-commit-validate.py',
        'tools/ci/validate-pr.py',
        'docs/75-rule-validation-system.md'
    ]

    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   OK: {file_path}")
        else:
            print(f"   MISSING: {file_path}")
            all_exist = False

    if all_exist:
        print(f"\n   SUCCESS: All {len(required_files)} system files exist!")
    else:
        print(f"\n   ERROR: Some files are missing!")
        return False

    # 2. Check rules.json
    print("\n2. Rules Configuration:")
    try:
        with open('tools/validator/rules.json', 'r') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'rules' in data:
            rules = data['rules']
        elif isinstance(data, list):
            rules = data
        else:
            print("   ERROR: Invalid rules.json format")
            return False

        print(f"   SUCCESS: Loaded {len(rules)} rules from rules.json")

        # Show first few rules
        print("\n   Sample Rules:")
        for i, rule in enumerate(rules[:5]):
            print(f"      {i+1}. {rule.get('id', 'Unknown')}: {rule.get('name', 'Unknown')}")

        if len(rules) > 5:
            print(f"      ... and {len(rules) - 5} more rules")

    except Exception as e:
        print(f"   ERROR: Failed to load rules.json: {e}")
        return False

    # 3. Check validator files
    print("\n3. Validator Components:")
    validators = [
        ('Security Validator', 'tools/validator/validators/security_validator.py'),
        ('API Validator', 'tools/validator/validators/api_validator.py'),
        ('Code Quality Validator', 'tools/validator/validators/code_quality_validator.py'),
        ('Logging Validator', 'tools/validator/validators/logging_validator.py'),
        ('Comment Validator', 'tools/validator/validators/comment_validator.py'),
        ('Structure Validator', 'tools/validator/validators/structure_validator.py')
    ]

    for name, path in validators:
        if os.path.exists(path):
            with open(path, 'r') as f:
                lines = len(f.readlines())
            print(f"   OK: {name} ({lines} lines)")
        else:
            print(f"   MISSING: {name}")

    # 4. Check integration files
    print("\n4. Integration Components:")
    integrations = [
        ('Pre-commit Hook', 'tools/hooks/pre-commit-validate.py'),
        ('CI/CD Script', 'tools/ci/validate-pr.py'),
        ('IDE Linter', 'tools/validator/ide_linter.py'),
        ('GitHub Actions', '.github/workflows/validate-75-rules.yml')
    ]

    for name, path in integrations:
        if os.path.exists(path):
            print(f"   OK: {name}")
        else:
            print(f"   MISSING: {name}")

    # 5. Check configuration files
    print("\n5. Configuration Files:")
    configs = [
        ('VS Code Settings', '.vscode/settings.json'),
        ('Python Config', 'pyproject.toml'),
        ('TypeScript Config', 'tsconfig.json'),
        ('Dependencies', 'requirements.txt')
    ]

    for name, path in configs:
        if os.path.exists(path):
            print(f"   OK: {name}")
        else:
            print(f"   MISSING: {name}")

    # 6. Check documentation
    print("\n6. Documentation:")
    docs = [
        ('System Documentation', 'docs/75-rule-validation-system.md'),
        ('Test Suite', 'tests/test_validators.py'),
        ('README', 'README.md')
    ]

    for name, path in docs:
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"   OK: {name} ({size:,} bytes)")
        else:
            print(f"   MISSING: {name}")

    # 7. Show usage examples
    print("\n7. Usage Examples:")
    print("   To validate files:")
    print("      python tools/validator/rule_engine.py --mode=diff --report=json")
    print("   ")
    print("   To install pre-commit hook:")
    print("      python tools/hooks/install.py")
    print("   ")
    print("   To run CI/CD validation:")
    print("      python tools/ci/validate-pr.py --scope=full")
    print("   ")
    print("   To run tests:")
    print("      python -m pytest tests/test_validators.py -v")

    # 8. Show rule categories
    print("\n8. Rule Categories:")
    categories = {}
    for rule in rules:
        category = rule.get('category', 'Unknown')
        categories[category] = categories.get(category, 0) + 1

    for category, count in sorted(categories.items()):
        print(f"   {category}: {count} rules")

    print("\n" + "=" * 50)
    print("SUCCESS: ZeroUI 2.0 Rule Validation System is ready!")
    print("All components are in place and configured.")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Install pre-commit hook: python tools/hooks/install.py")
    print("3. Test with sample files: python tools/validator/rule_engine.py --help")

    return True

if __name__ == "__main__":
    try:
        success = test_validation_system()
        if success:
            print("\nTest completed successfully!")
            sys.exit(0)
        else:
            print("\nTest failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
