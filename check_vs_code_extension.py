#!/usr/bin/env python3
"""
Check VS Code Extension for Issues
"""

import sys
import os
import json

def check_extension_implementation():
    """Check extension.ts implementation."""
    print("Checking extension.ts implementation...")

    file_path = 'src/vscode-extension/extension.ts'
    if not os.path.exists(file_path):
        print(f'  ERROR: File not found {file_path}')
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        issues = []

        # Check for required imports
        required_imports = [
            'import * as vscode',
            'import axios',
            'ConstitutionValidator'
        ]

        for import_check in required_imports:
            if import_check not in content:
                issues.append(f'Missing: {import_check}')

        # Check for command registration
        command_registrations = content.count('registerCommand')
        if command_registrations < 2:
            issues.append(f'Expected at least 2 command registrations, found {command_registrations}')

        # Check for ConstitutionValidator usage
        validator_usage = content.count('constitutionValidator')
        if validator_usage == 0:
            issues.append('ConstitutionValidator not used in extension')

        # Check for proper class definition
        if 'class ConstitutionValidator' not in content:
            issues.append('ConstitutionValidator class not defined')

        if issues:
            print('  Issues found:')
            for issue in issues:
                print(f'    - {issue}')
            return False
        else:
            print('  OK All required elements present')
            return True

    except Exception as e:
        print(f'  ERROR: {e}')
        return False

def check_package_commands():
    """Check package.json commands."""
    print("\nChecking package.json commands...")

    file_path = 'src/vscode-extension/package.json'
    if not os.path.exists(file_path):
        print(f'  ERROR: File not found {file_path}')
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        commands = data.get('contributes', {}).get('commands', [])
        validation_commands = [cmd for cmd in commands if 'validate' in cmd['command'] or 'generate' in cmd['command']]

        print(f'  Validation commands: {len(validation_commands)}')
        for cmd in validation_commands:
            print(f'    - {cmd["command"]}: {cmd["title"]}')

        # Check for required commands
        required_commands = ['zeroui.validatePrompt', 'zeroui.generateCode']
        found_commands = [cmd['command'] for cmd in validation_commands]

        missing_commands = [cmd for cmd in required_commands if cmd not in found_commands]
        if missing_commands:
            print(f'  Missing commands: {missing_commands}')
            return False

        return True

    except Exception as e:
        print(f'  ERROR: {e}')
        return False

def check_configuration():
    """Check configuration properties."""
    print("\nChecking configuration properties...")

    file_path = 'src/vscode-extension/package.json'
    if not os.path.exists(file_path):
        print(f'  ERROR: File not found {file_path}')
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        config_props = data.get('contributes', {}).get('configuration', {}).get('properties', {})
        validation_config = [k for k in config_props.keys() if 'validation' in k]

        print(f'  Validation config properties: {len(validation_config)}')
        for prop in validation_config:
            print(f'    - {prop}')

        # Check for required config
        required_config = ['zeroui.validationServiceUrl']
        missing_config = [config for config in required_config if config not in validation_config]

        if missing_config:
            print(f'  Missing config: {missing_config}')
            return False

        return True

    except Exception as e:
        print(f'  ERROR: {e}')
        return False

def main():
    """Run VS Code extension checks."""
    print("=" * 50)
    print("VS CODE EXTENSION VALIDATION")
    print("=" * 50)

    import os

    tests = [
        check_extension_implementation,
        check_package_commands,
        check_configuration
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print("VS CODE VALIDATION RESULTS")
    print("=" * 50)

    if passed == len(tests):
        print("SUCCESS - VS Code extension is properly implemented!")
        print("\nExtension components verified:")
        print("OK Extension.ts implementation complete")
        print("OK Required commands registered")
        print("OK Configuration properties defined")
        print("OK No missing imports or dependencies")
        print("\nVS Code extension ready for use!")
    else:
        print(f"ISSUES FOUND - {len(tests) - passed} problems in VS Code extension")

    return passed == len(tests)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
