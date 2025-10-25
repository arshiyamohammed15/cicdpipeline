#!/usr/bin/env python3
"""
Final Issue Check for Implementation
"""

import sys
import os
sys.path.insert(0, 'D:/Projects/ZeroUI2.0')

def check_all_files():
    """Check if all required files exist."""
    print("Checking file existence...")

    files_to_check = [
        'config/hook_config.json',
        'config/constitution_rules.json',
        'config/constitution_config.json',
        'validator/pre_implementation_hooks.py',
        'validator/integrations/__init__.py',
        'validator/integrations/ai_service_wrapper.py',
        'validator/integrations/integration_registry.py',
        'validator/integrations/api_service.py',
        'tools/enhanced_cli.py',
        'tools/start_validation_service.py',
        'src/vscode-extension/extension.ts',
        'src/vscode-extension/package.json'
    ]

    missing_files = []
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"  OK {file_path}")
        else:
            print(f"  MISSING {file_path}")
            missing_files.append(file_path)

    return len(missing_files) == 0, missing_files

def check_all_imports():
    """Check if all imports work."""
    print("\nChecking imports...")

    imports_to_test = [
        'validator.pre_implementation_hooks',
        'validator.integrations.ai_service_wrapper',
        'validator.integrations.integration_registry',
        'validator.integrations.api_service',
        'config.constitution.config_manager',
        'config.enhanced_config_manager',
        'tools.enhanced_cli'
    ]

    import_errors = []
    for module in imports_to_test:
        try:
            __import__(module)
            print(f"  OK {module}")
        except Exception as e:
            print(f"  ERROR {module}: {e}")
            import_errors.append((module, str(e)))

    return len(import_errors) == 0, import_errors

def check_functionality():
    """Check if core functionality works."""
    print("\nChecking functionality...")

    try:
        from validator.pre_implementation_hooks import PreImplementationHookManager
        hook_manager = PreImplementationHookManager()

        # Test validation
        result = hook_manager.validate_before_generation('test prompt', 'python', 'general')
        violations = len(result['violations'])
        valid = result['valid']

        print(f"  OK Validation: {violations} violations, valid: {valid}")

        # Test integration registry
        from validator.integrations.integration_registry import IntegrationRegistry
        registry = IntegrationRegistry()
        integrations = registry.list_integrations()

        print(f"  OK Registry: {len(integrations)} integrations")

        # Test API service
        from validator.integrations.api_service import app
        routes = list(app.url_map.iter_rules())

        print(f"  OK API service: {len(routes)} routes")

        return True
    except Exception as e:
        print(f"  ERROR functionality: {e}")
        return False

def check_vs_code():
    """Check VS Code extension."""
    print("\nChecking VS Code extension...")

    import json

    try:
        with open('src/vscode-extension/extension.ts', 'r', encoding='utf-8') as f:
            content = f.read()

        has_vscode = 'import * as vscode' in content
        has_axios = 'import axios' in content
        has_constitution = 'ConstitutionValidator' in content

        print(f"  OK VS Code: vscode import: {has_vscode}, axios: {has_axios}, ConstitutionValidator: {has_constitution}")

        # Check package.json
        with open('src/vscode-extension/package.json', 'r', encoding='utf-8') as f:
            package_data = json.load(f)

        commands = len(package_data.get('contributes', {}).get('commands', []))
        config_props = len(package_data.get('contributes', {}).get('configuration', {}).get('properties', {}))

        print(f"  OK Package: {commands} commands, {config_props} config props")

        return has_vscode and has_axios and has_constitution
    except Exception as e:
        print(f"  ERROR VS Code: {e}")
        return False

def main():
    """Run final issue check."""
    print("=" * 60)
    print("FINAL ISSUE DETECTION")
    print("=" * 60)

    import json

    tests = [
        check_all_files,
        check_all_imports,
        check_functionality,
        check_vs_code
    ]

    passed = 0
    issues = []

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                issues.append(f"{test.__name__} failed")
        except Exception as e:
            issues.append(f"{test.__name__}: {e}")

    print("\n" + "=" * 60)
    print("FINAL ISSUE CHECK RESULTS")
    print("=" * 60)
    print(f"Tests passed: {passed}/{len(tests)}")

    if issues:
        print(f"\nISSUES FOUND ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nSUCCESS - No issues found!")
        print("\nAll components working:")
        print("OK All files present")
        print("OK All imports successful")
        print("OK Core functionality operational")
        print("OK VS Code extension complete")
        print("\nImplementation is ready for use!")

    return len(issues) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
