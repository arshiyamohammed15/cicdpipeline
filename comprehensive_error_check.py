#!/usr/bin/env python3
"""
Comprehensive Error Check Across Implementation
"""

import sys
import os
import json
import ast

def check_python_syntax():
    """Check Python files for syntax errors."""
    print("Checking Python syntax...")

    python_files = [
        'validator/pre_implementation_hooks.py',
        'validator/integrations/ai_service_wrapper.py',
        'validator/integrations/integration_registry.py',
        'validator/integrations/api_service.py',
        'tools/enhanced_cli.py',
        'tools/start_validation_service.py'
    ]

    syntax_errors = []
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content, file_path)
            print(f'  OK {file_path}')
        except SyntaxError as e:
            print(f'  SYNTAX ERROR {file_path}: {e}')
            syntax_errors.append((file_path, str(e)))
        except Exception as e:
            print(f'  ERROR {file_path}: {e}')
            syntax_errors.append((file_path, str(e)))

    return len(syntax_errors) == 0, syntax_errors

def check_imports():
    """Check for import errors."""
    print("\nChecking imports...")

    import_modules = [
        'validator.models',
        'validator.analyzer',
        'validator.reporter',
        'config.enhanced_config_manager',
        'tools.enhanced_cli'
    ]

    import_errors = []
    for module in import_modules:
        try:
            __import__(module)
            print(f'  OK {module}')
        except ImportError as e:
            print(f'  IMPORT ERROR {module}: {e}')
            import_errors.append((module, str(e)))
        except Exception as e:
            print(f'  ERROR {module}: {e}')
            import_errors.append((module, str(e)))

    return len(import_errors) == 0, import_errors

def check_json_files():
    """Check JSON files for validity."""
    print("\nChecking JSON files...")

    json_files = [
        'config/hook_config.json',
        'config/constitution_rules.json',
        'src/vscode-extension/package.json'
    ]

    json_errors = []
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            print(f'  OK {file_path}')
        except Exception as e:
            print(f'  JSON ERROR {file_path}: {e}')
            json_errors.append((file_path, str(e)))

    return len(json_errors) == 0, json_errors

def check_typescript_files():
    """Check TypeScript files."""
    print("\nChecking TypeScript files...")

    ts_files = ['src/vscode-extension/extension.ts']
    ts_errors = []

    for file_path in ts_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Basic checks
            issues = []

            if 'import * as vscode' not in content:
                issues.append('Missing vscode import')

            if 'ConstitutionValidator' not in content:
                issues.append('Missing ConstitutionValidator')

            if 'axios' in content and 'import axios' not in content:
                issues.append('Missing axios import')

            if issues:
                print(f'  ISSUES {file_path}: {len(issues)} issues')
                for issue in issues:
                    print(f'    - {issue}')
                ts_errors.append((file_path, ', '.join(issues)))
            else:
                print(f'  OK {file_path}')

        except Exception as e:
            print(f'  ERROR {file_path}: {e}')
            ts_errors.append((file_path, str(e)))

    return len(ts_errors) == 0, ts_errors

def test_functionality():
    """Test basic functionality."""
    print("\nTesting basic functionality...")

    try:
        from validator.pre_implementation_hooks import PreImplementationHookManager
        hook_manager = PreImplementationHookManager()
        result = hook_manager.validate_before_generation('test prompt', 'python', 'general')
        print(f'  OK Basic validation: {len(result["violations"])} violations')
        return True, []
    except Exception as e:
        print(f'  RUNTIME ERROR: {e}')
        return False, [('functionality', str(e))]

def main():
    """Run comprehensive error check."""
    print("=" * 60)
    print("COMPREHENSIVE ERROR CHECK ACROSS IMPLEMENTATION")
    print("=" * 60)

    tests = [
        check_python_syntax,
        check_imports,
        check_json_files,
        check_typescript_files,
        test_functionality
    ]

    passed = 0
    total_errors = []

    for test in tests:
        passed_test, errors = test()
        if passed_test:
            passed += 1
        total_errors.extend(errors)

    print("\n" + "=" * 60)
    print("COMPREHENSIVE ERROR CHECK RESULTS")
    print("=" * 60)
    print(f"Tests passed: {passed}/{len(tests)}")

    if total_errors:
        print(f"\nERRORS FOUND ({len(total_errors)} total):")
        for file_path, error in total_errors:
            print(f"  - {file_path}: {error}")
    else:
        print("\nSUCCESS - No errors found in implementation!")
        print("\nAll components validated:")
        print("OK Python syntax correct in all files")
        print("OK All imports successful")
        print("OK JSON configuration files valid")
        print("OK TypeScript files properly structured")
        print("OK Basic functionality operational")
        print("\nNo problems window errors detected!")

    return len(total_errors) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
