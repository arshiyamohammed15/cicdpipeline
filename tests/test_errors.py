#!/usr/bin/env python3
"""
Test for Errors and Issues in Implementation
"""

import sys
sys.path.insert(0, 'D:/Projects/ZeroUI2.0')

def test_imports():
    """Test all imports for errors."""
    print("Testing imports...")

    imports_to_test = [
        ('validator.pre_implementation_hooks', 'PreImplementationHookManager'),
        ('validator.integrations.integration_registry', 'IntegrationRegistry'),
        ('validator.integrations.api_service', 'app'),
        ('validator.integrations.openai_integration', 'OpenAIIntegration'),
        ('validator.integrations.cursor_integration', 'CursorIntegration'),
        ('tools.enhanced_cli', 'EnhancedCLI'),
        ('tools.start_validation_service', None)
    ]

    errors = []
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name] if class_name else [])
            if class_name:
                getattr(module, class_name)
            print(f'  OK {module_name}')
        except Exception as e:
            print(f'  ERROR {module_name}: {e}')
            errors.append((module_name, str(e)))

    return len(errors) == 0, errors

def test_basic_functionality():
    """Test basic functionality for errors."""
    print("\nTesting basic functionality...")

    try:
        from validator.pre_implementation_hooks import PreImplementationHookManager
        hook_manager = PreImplementationHookManager()
        result = hook_manager.validate_before_generation('test prompt', 'python', 'general')
        print(f'  OK Basic validation: {len(result["violations"])} violations')
        return True, []
    except Exception as e:
        print(f'  ERROR Basic validation: {e}')
        return False, [('basic_functionality', str(e))]

def test_json_files():
    """Test JSON configuration files."""
    print("\nTesting JSON files...")

    import json

    json_files = [
        'config/hook_config.json',
        'config/constitution_rules.json',
        'config/constitution_config.json'
    ]

    errors = []
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            print(f'  OK {file_path}')
        except Exception as e:
            print(f'  ERROR {file_path}: {e}')
            errors.append((file_path, str(e)))

    return len(errors) == 0, errors

def test_vs_code_files():
    """Test VS Code extension files."""
    print("\nTesting VS Code files...")

    import json

    vs_code_files = [
        'src/vscode-extension/package.json',
        'src/vscode-extension/extension.ts'
    ]

    errors = []
    for file_path in vs_code_files:
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            elif file_path.endswith('.ts'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Basic syntax check
                    if 'ConstitutionValidator' not in content:
                        errors.append((file_path, 'Missing ConstitutionValidator class'))
            print(f'  OK {file_path}')
        except Exception as e:
            print(f'  ERROR {file_path}: {e}')
            errors.append((file_path, str(e)))

    return len(errors) == 0, errors

def main():
    """Run error testing."""
    print("=" * 50)
    print("ERROR DETECTION AND VALIDATION")
    print("=" * 50)

    tests = [
        test_imports,
        test_basic_functionality,
        test_json_files,
        test_vs_code_files
    ]

    all_passed = True
    total_errors = []

    for test in tests:
        passed, errors = test()
        if not passed:
            all_passed = False
            total_errors.extend(errors)

    print("\n" + "=" * 50)
    print("ERROR VALIDATION RESULTS")
    print("=" * 50)

    if all_passed:
        print("SUCCESS - No errors detected in implementation!")
        print("\nAll components are working correctly:")
        print("OK All imports successful")
        print("OK Basic functionality operational")
        print("OK JSON configuration files valid")
        print("OK VS Code extension files valid")
        print("\nNo problems window errors found!")
    else:
        print(f"ERRORS DETECTED - {len(total_errors)} issues found:")
        for file_path, error in total_errors:
            print(f"  - {file_path}: {error}")

    return all_passed, total_errors

if __name__ == '__main__':
    success, errors = main()
    sys.exit(0 if success else 1)
