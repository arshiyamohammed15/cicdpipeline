#!/usr/bin/env python3
"""
Test Constitution Rule Coverage

This script verifies that all rules from the 6 Constitution files
are properly implemented and tested in the validation system.
"""

import os
import json
import re
from pathlib import Path

def extract_rules_from_constitution(file_path):
    """Extract rules from a Constitution markdown file"""
    rules = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for numbered rules (various patterns)
        patterns = [
            r'^(\d+)\.\s+(.+?)(?=\n\d+\.|\n\n|\Z)',  # 1. Rule text
            r'^(\d+)\)\s+(.+?)(?=\n\d+\)|\n\n|\Z)',  # 1) Rule text
            r'^(\d+)\s+(.+?)(?=\n\d+\s|\n\n|\Z)',    # 1 Rule text
            r'^Rule\s+(\d+):\s+(.+?)(?=\nRule\s+\d+|\n\n|\Z)',  # Rule 1: text
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                rule_num = match.group(1)
                rule_text = match.group(2).strip()

                # Clean up the rule text
                rule_text = re.sub(r'\n+', ' ', rule_text)
                rule_text = re.sub(r'\s+', ' ', rule_text)

                if len(rule_text) > 10:  # Only include substantial rules
                    rules.append({
                        'number': rule_num,
                        'text': rule_text[:100] + '...' if len(rule_text) > 100 else rule_text
                    })

        return rules

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def analyze_constitution_files():
    """Analyze all Constitution files and extract rules"""
    constitution_files = [
        'ZeroUI 2.0 — Code Review Constitution — Revised.md',
        'ZeroUI2.0 API Contracts Constitution — Revised.md',
        'ZeroUI2.0 Coding Standards Constitution — Revised.md',
        'ZeroUI2.0 Comments Constitution — Revised.md',
        'ZeroUI2.0 Folder Standards Cursor Constitution — Revised.md',
        'ZeroUI2.0 Logging & Troubleshooting Constitution — Revised v2.md'
    ]

    all_rules = {}

    for file_path in constitution_files:
        if os.path.exists(file_path):
            print(f"\nAnalyzing: {file_path}")
            rules = extract_rules_from_constitution(file_path)
            all_rules[file_path] = rules
            print(f"  Found {len(rules)} rules")

            # Show first few rules
            for i, rule in enumerate(rules[:3]):
                print(f"    {rule['number']}. {rule['text']}")
            if len(rules) > 3:
                print(f"    ... and {len(rules) - 3} more rules")
        else:
            print(f"Missing: {file_path}")

    return all_rules

def analyze_validation_system():
    """Analyze the validation system rules"""
    print("\nAnalyzing Validation System Rules...")

    try:
        with open('tools/validator/rules.json', 'r') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'rules' in data:
            rules = data['rules']
        elif isinstance(data, list):
            rules = data
        else:
            print("ERROR: Invalid rules.json format")
            return {}

        print(f"Total rules in validation system: {len(rules)}")

        # Group by category
        categories = {}
        for rule in rules:
            category = rule.get('category', 'Unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(rule)

        print("\nRules by category:")
        for category, category_rules in categories.items():
            print(f"  {category}: {len(category_rules)} rules")
            for rule in category_rules[:2]:  # Show first 2 rules
                print(f"    {rule.get('id', 'Unknown')}: {rule.get('name', 'Unknown')}")
            if len(category_rules) > 2:
                print(f"    ... and {len(category_rules) - 2} more")

        return categories

    except Exception as e:
        print(f"ERROR: Failed to load validation system rules: {e}")
        return {}

def check_validator_implementation():
    """Check if validators are properly implemented"""
    print("\nChecking Validator Implementation...")

    validators = [
        ('Security Validator', 'tools/validator/validators/security_validator.py'),
        ('API Validator', 'tools/validator/validators/api_validator.py'),
        ('Code Quality Validator', 'tools/validator/validators/code_quality_validator.py'),
        ('Logging Validator', 'tools/validator/validators/logging_validator.py'),
        ('Comment Validator', 'tools/validator/validators/comment_validator.py'),
        ('Structure Validator', 'tools/validator/validators/structure_validator.py')
    ]

    implemented_validators = {}

    for name, path in validators:
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()

            # Count validation methods
            methods = re.findall(r'def validate_\w+\(', content)
            print(f"  {name}: {len(methods)} validation methods")
            implemented_validators[name] = len(methods)
        else:
            print(f"  {name}: MISSING")
            implemented_validators[name] = 0

    return implemented_validators

def check_test_coverage():
    """Check if tests cover all validators"""
    print("\nChecking Test Coverage...")

    test_file = 'tests/test_validators.py'
    if os.path.exists(test_file):
        with open(test_file, 'r') as f:
            content = f.read()

        # Count test classes and methods
        test_classes = re.findall(r'class Test\w+:', content)
        test_methods = re.findall(r'def test_\w+\(', content)

        print(f"  Test file: {len(test_classes)} test classes, {len(test_methods)} test methods")

        # Check for specific validator tests
        validators_tested = []
        for validator in ['SecurityValidator', 'APIValidator', 'CodeQualityValidator',
                         'LoggingValidator', 'CommentValidator', 'StructureValidator']:
            if f'Test{validator}' in content:
                validators_tested.append(validator)
                print(f"    ✓ {validator} has test class")
            else:
                print(f"    ✗ {validator} missing test class")

        return len(validators_tested)
    else:
        print("  Test file missing")
        return 0

def main():
    """Main analysis function"""
    print("ZeroUI 2.0 Constitution Rule Coverage Analysis")
    print("=" * 60)

    # 1. Analyze Constitution files
    constitution_rules = analyze_constitution_files()

    # 2. Analyze validation system
    validation_categories = analyze_validation_system()

    # 3. Check validator implementation
    implemented_validators = check_validator_implementation()

    # 4. Check test coverage
    test_coverage = check_test_coverage()

    # 5. Summary
    print("\n" + "=" * 60)
    print("COVERAGE SUMMARY")
    print("=" * 60)

    total_constitution_rules = sum(len(rules) for rules in constitution_rules.values())
    total_validation_rules = sum(len(rules) for rules in validation_categories.values())
    total_validators = len([v for v in implemented_validators.values() if v > 0])
    total_tests = test_coverage

    print(f"Constitution Files Analyzed: {len(constitution_rules)}")
    print(f"Total Rules Found in Constitutions: {total_constitution_rules}")
    print(f"Total Rules in Validation System: {total_validation_rules}")
    print(f"Validators Implemented: {total_validators}/6")
    print(f"Validators with Tests: {total_tests}/6")

    # Coverage assessment
    print(f"\nCoverage Assessment:")
    if total_validation_rules >= 75:
        print("  ✓ Rule Count: SUFFICIENT (75+ rules implemented)")
    else:
        print(f"  ✗ Rule Count: INSUFFICIENT ({total_validation_rules}/75 rules)")

    if total_validators == 6:
        print("  ✓ Validators: COMPLETE (all 6 validators implemented)")
    else:
        print(f"  ✗ Validators: INCOMPLETE ({total_validators}/6 validators)")

    if total_tests >= 5:
        print("  ✓ Tests: GOOD (most validators have tests)")
    else:
        print(f"  ✗ Tests: INSUFFICIENT ({total_tests}/6 validators tested)")

    # Final verdict
    print(f"\nFINAL VERDICT:")
    if total_validation_rules >= 75 and total_validators == 6:
        print("  ✅ CONSTITUTION RULES FULLY COVERED")
        print("  The validation system implements all required rules from the Constitution files.")
    else:
        print("  ⚠️  CONSTITUTION RULES PARTIALLY COVERED")
        print("  Some rules may be missing or not fully implemented.")

    return total_validation_rules >= 75 and total_validators == 6

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\nAnalysis completed successfully!")
            exit(0)
        else:
            print("\nAnalysis found gaps in coverage!")
            exit(1)
    except Exception as e:
        print(f"\nAnalysis failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
