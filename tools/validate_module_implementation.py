#!/usr/bin/env python3
"""
Triple Validation: Module Implementation & Test Coverage

Validates:
1. Module implementation files exist (main.py, routes.py, services.py, models.py, dependencies.py)
2. Test files exist for each module
3. Test coverage analysis
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict

# Expected modules
EXPECTED_MODULES = {
    'shared-services': [
        'alerting-notification-service',
        'budgeting-rate-limiting-cost-observability',
        'configuration-policy-management',
        'contracts-schema-registry',
        'data-governance-privacy',
        'deployment-infrastructure',
        'evidence-receipt-indexing-service',
        'health-reliability-monitoring',
        'identity-access-management',
        'key-management-service',
        'ollama-ai-agent'
    ],
    'client-services': [
        'integration-adapters'
    ],
    'product-services': [
        'detection-engine-core',
        'mmm_engine',
        'signal-ingestion-normalization',
        'user_behaviour_intelligence'
    ],
    'other': [
        'llm_gateway'
    ]
}

REQUIRED_IMPLEMENTATION_FILES = ['main.py', 'routes.py', 'services.py', 'models.py', 'dependencies.py']


def check_module_implementation(module_path: Path) -> Dict[str, Any]:
    """Check if module has required implementation files."""
    result = {
        'exists': module_path.exists(),
        'files': {},
        'implementation_complete': False,
        'missing_files': []
    }
    
    if not result['exists']:
        return result
    
    for file_name in REQUIRED_IMPLEMENTATION_FILES:
        file_path = module_path / file_name
        # Also check routes/ directory for routes.py
        if file_name == 'routes.py':
            routes_dir = module_path / 'routes'
            if routes_dir.exists():
                route_files = list(routes_dir.glob('*.py'))
                result['files'][file_name] = len(route_files) > 0
            else:
                result['files'][file_name] = file_path.exists()
        # Also check services/ directory for services.py
        elif file_name == 'services.py':
            services_dir = module_path / 'services'
            if services_dir.exists():
                service_files = list(services_dir.glob('*.py'))
                result['files'][file_name] = len(service_files) > 0
            else:
                result['files'][file_name] = file_path.exists()
        else:
            result['files'][file_name] = file_path.exists()
        
        if not result['files'][file_name]:
            result['missing_files'].append(file_name)
    
    # Implementation is complete if main.py exists (minimum requirement)
    # and at least routes.py or services.py exists
    result['implementation_complete'] = (
        result['files'].get('main.py', False) and
        (result['files'].get('routes.py', False) or result['files'].get('services.py', False))
    )
    
    return result


def count_test_files(module_name: str, category: str) -> Dict[str, Any]:
    """Count test files for a module."""
    # Check new centralized structure
    test_base = Path('tests') / 'cloud_services'
    
    # Map category names (test directories use underscores)
    category_map = {
        'shared-services': 'shared_services',
        'client-services': 'client_services',
        'product-services': 'product_services'  # Note: test dir uses underscore
    }
    
    test_category = category_map.get(category, category.replace('-', '_'))
    module_test_name = module_name.replace('-', '_')
    
    test_path = test_base / test_category / module_test_name
    
    result = {
        'test_path': str(test_path),
        'exists': test_path.exists(),
        'test_files': {},
        'total_test_files': 0,
        'total_test_cases': 0
    }
    
    if not result['exists']:
        # Check old structure
        old_paths = [
            Path('tests') / module_name,
            Path('tests') / module_name.replace('-', '_'),
            Path('tests') / category / module_name,
        ]
        for old_path in old_paths:
            if old_path.exists():
                result['test_path'] = str(old_path)
                result['exists'] = True
                test_path = old_path
                break
    
    if result['exists']:
        test_types = ['unit', 'integration', 'security', 'performance', 'resilience']
        for test_type in test_types:
            type_path = test_path / test_type
            if type_path.exists():
                test_files = list(type_path.glob('test_*.py'))
                result['test_files'][test_type] = len(test_files)
                result['total_test_files'] += len(test_files)
        
        # Also check root of test directory
        root_test_files = list(test_path.glob('test_*.py'))
        if root_test_files:
            result['test_files']['root'] = len(root_test_files)
            result['total_test_files'] += len(root_test_files)
    
    # Count test cases from manifest if available
    try:
        manifest_path = Path('artifacts') / 'test_manifest.json'
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            module_test_cases = 0
            for test_file in manifest.get('test_files', []):
                file_path = test_file.get('path', '')
                if module_name.replace('-', '_') in file_path.replace('\\', '/').replace('-', '_'):
                    module_test_cases += len(test_file.get('test_functions', []))
                    module_test_cases += len(test_file.get('test_classes', []))
            
            result['total_test_cases'] = module_test_cases
    except Exception:
        pass
    
    return result


def validate_all_modules() -> Dict[str, Any]:
    """Validate all expected modules."""
    project_root = Path('.')
    results = {
        'modules': {},
        'summary': {
            'total_expected': 0,
            'total_implemented': 0,
            'total_with_tests': 0,
            'total_test_files': 0,
            'total_test_cases': 0
        }
    }
    
    for category, modules in EXPECTED_MODULES.items():
        for module_name in modules:
            results['summary']['total_expected'] += 1
            
            # Check implementation
            if category == 'other':
                module_path = project_root / 'src' / 'cloud_services' / module_name
            else:
                # Try both product-services and product_services (underscore vs hyphen)
                if category == 'product-services':
                    # Check underscore version first (actual directory name)
                    module_path = project_root / 'src' / 'cloud_services' / 'product_services' / module_name
                    if not module_path.exists():
                        module_path = project_root / 'src' / 'cloud_services' / 'product-services' / module_name
                else:
                    module_path = project_root / 'src' / 'cloud_services' / category / module_name
            
            impl_result = check_module_implementation(module_path)
            test_result = count_test_files(module_name, category)
            
            module_result = {
                'category': category,
                'module_name': module_name,
                'module_path': str(module_path),
                'implementation': impl_result,
                'tests': test_result,
                'status': 'unknown'
            }
            
            # Determine status
            if impl_result['implementation_complete']:
                results['summary']['total_implemented'] += 1
                if test_result['total_test_files'] > 0:
                    results['summary']['total_with_tests'] += 1
                    results['summary']['total_test_files'] += test_result['total_test_files']
                    results['summary']['total_test_cases'] += test_result['total_test_cases']
                    module_result['status'] = 'implemented_with_tests'
                else:
                    module_result['status'] = 'implemented_no_tests'
            else:
                module_result['status'] = 'not_implemented'
            
            results['modules'][module_name] = module_result
    
    return results


def print_validation_report(results: Dict[str, Any]):
    """Print comprehensive validation report."""
    print("=" * 80)
    print("TRIPLE VALIDATION REPORT: Module Implementation & Test Coverage")
    print("=" * 80)
    
    print(f"\nSUMMARY")
    print(f"  Expected Modules: {results['summary']['total_expected']}")
    print(f"  Implemented Modules: {results['summary']['total_implemented']}")
    print(f"  Modules with Tests: {results['summary']['total_with_tests']}")
    print(f"  Total Test Files: {results['summary']['total_test_files']}")
    print(f"  Total Test Cases: {results['summary']['total_test_cases']}")
    
    print(f"\nDETAILED MODULE VALIDATION")
    print("-" * 80)
    
    for category in ['shared-services', 'client-services', 'product-services', 'other']:
        category_modules = [m for m, r in results['modules'].items() if r['category'] == category]
        if category_modules:
            print(f"\n{category.upper().replace('-', ' ')}:")
            for module_name in category_modules:
                module = results['modules'][module_name]
                impl = module['implementation']
                tests = module['tests']
                
                impl_status = "✅" if impl['implementation_complete'] else "❌"
                test_status = "✅" if tests['total_test_files'] > 0 else "❌"
                
                print(f"  {impl_status} {test_status} {module_name}")
                print(f"     Implementation: {impl['implementation_complete']}")
                print(f"     Files: {sum(impl['files'].values())}/{len(REQUIRED_IMPLEMENTATION_FILES)}")
                if impl['missing_files']:
                    print(f"     Missing: {', '.join(impl['missing_files'])}")
                print(f"     Test Files: {tests['total_test_files']}")
                print(f"     Test Cases: {tests['total_test_cases']}")
                print(f"     Status: {module['status']}")
    
    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    results = validate_all_modules()
    print_validation_report(results)
    
    # Save to JSON
    output_path = Path('artifacts') / 'module_validation_report.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nReport saved to: {output_path}")


if __name__ == '__main__':
    main()

