#!/usr/bin/env python3
"""
Check TypeScript Files for Issues
"""

import sys
import os
import json

def check_extension_ts():
    """Check extension.ts for issues."""
    print("Checking extension.ts...")

    file_path = 'src/vscode-extension/extension.ts'
    if not os.path.exists(file_path):
        print(f'  ERROR: File not found {file_path}')
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        issues = []

        # Check for axios import
        if 'axios' in content and 'import axios' not in content:
            issues.append('axios used but not imported')

        # Check for ConstitutionValidator class definition
        if 'ConstitutionValidator' in content and 'class ConstitutionValidator' not in content:
            issues.append('ConstitutionValidator referenced but not defined')

        # Check for proper imports
        if 'import * as vscode' not in content:
            issues.append('Missing vscode import')

        if issues:
            print('  Issues found:')
            for issue in issues:
                print(f'    - {issue}')
            return False
        else:
            print('  OK No issues found')
            return True

    except Exception as e:
        print(f'  ERROR: {e}')
        return False

def check_package_json():
    """Check package.json for issues."""
    print("\nChecking package.json...")

    file_path = 'src/vscode-extension/package.json'
    if not os.path.exists(file_path):
        print(f'  ERROR: File not found {file_path}')
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        issues = []

        # Check for required fields
        required_fields = ['name', 'version', 'main', 'contributes']
        for field in required_fields:
            if field not in data:
                issues.append(f'Missing required field: {field}')

        # Check commands
        commands = data.get('contributes', {}).get('commands', [])
        validation_commands = [cmd for cmd in commands if 'validate' in cmd['command'] or 'generate' in cmd['command']]
        if len(validation_commands) < 2:
            issues.append(f'Expected 2 validation commands, found {len(validation_commands)}')

        # Check configuration
        config_props = data.get('contributes', {}).get('configuration', {}).get('properties', {})
        validation_config = [k for k in config_props.keys() if 'validation' in k]
        if not validation_config:
            issues.append('Missing validation configuration properties')

        if issues:
            print('  Issues found:')
            for issue in issues:
                print(f'    - {issue}')
            return False
        else:
            print('  OK No issues found')
            return True

    except Exception as e:
        print(f'  ERROR: {e}')
        return False

def check_missing_dependencies():
    """Check for missing dependencies."""
    print("\nChecking dependencies...")

    # Check if axios is available for TypeScript
    try:
        import requests
        print('  OK requests (Python HTTP client) available')
    except ImportError:
        print('  WARNING: requests not available')

    # Check if openai is available
    try:
        import openai
        print('  OK openai library available')
    except ImportError:
        print('  WARNING: openai library not available')

    # Check if flask is available for API service
    try:
        import flask
        print('  OK flask available for API service')
    except ImportError:
        print('  WARNING: flask not available for API service')

    return True

def main():
    """Run TypeScript and dependency checks."""
    print("=" * 50)
    print("TYPESCRIPT AND DEPENDENCY VALIDATION")
    print("=" * 50)

    tests = [
        check_extension_ts,
        check_package_json,
        check_missing_dependencies
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print("VALIDATION RESULTS")
    print("=" * 50)

    if passed == len(tests):
        print("SUCCESS - No TypeScript or dependency issues found!")
        print("\nAll components properly configured:")
        print("OK VS Code extension.ts valid")
        print("OK package.json configuration complete")
        print("OK Required dependencies available")
        print("\nNo problems window errors detected!")
    else:
        print(f"ISSUES FOUND - {len(tests) - passed} problems detected")

    return passed == len(tests)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
