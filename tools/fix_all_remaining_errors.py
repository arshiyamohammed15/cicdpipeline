#!/usr/bin/env python3
"""
Comprehensive fix for all remaining test collection errors.
"""
from pathlib import Path
import re
import sys
import importlib.util
import types

def setup_integration_adapters_package():
    """Set up integration_adapters package structure."""
    MODULE_ROOT = Path(__file__).resolve().parents[1] / "src" / "cloud_services" / "client-services" / "integration-adapters"
    
    if "integration_adapters" not in sys.modules:
        pkg = types.ModuleType("integration_adapters")
        pkg.__path__ = [str(MODULE_ROOT)]
        sys.modules["integration_adapters"] = pkg
        
        # Create all subpackages
        subpackages = {
            "services": MODULE_ROOT / "services",
            "database": MODULE_ROOT / "database",
            "adapters": MODULE_ROOT / "adapters",
            "reliability": MODULE_ROOT / "reliability",
            "observability": MODULE_ROOT / "observability",
            "models": MODULE_ROOT,
            "integrations": MODULE_ROOT / "integrations",
        }
        
        for name, path in subpackages.items():
            pkg_name = f"integration_adapters.{name}"
            if pkg_name not in sys.modules:
                subpkg = types.ModuleType(pkg_name)
                if path.exists():
                    subpkg.__path__ = [str(path)]
                else:
                    subpkg.__path__ = [str(MODULE_ROOT)]
                sys.modules[pkg_name] = subpkg

def fix_file(file_path: Path) -> bool:
    """Fix imports in a test file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix integration_adapters imports - ensure they use proper paths
        if 'integration_adapters' in str(file_path):
            # These imports should work if conftest is set up properly
            # But we can ensure the imports are correct
            pass
        
        # Fix detection_engine_core imports
        if 'detection_engine_core' in str(file_path):
            content = re.sub(
                r'from integration_adapters\.models import',
                'from detection_engine_core.models import',
                content
            )
        
        # Fix identity-access-management imports
        if 'identity_access_management' in str(file_path) or 'identity-access-management' in str(file_path):
            content = re.sub(
                r'from identity-access-management\.main import app app',
                'from main import app',
                content
            )
            content = re.sub(
                r'from identity_access_management\.main import',
                'from main import',
                content
            )
        
        # Fix key-management-service imports
        if 'key_management_service' in str(file_path) or 'key-management-service' in str(file_path):
            content = re.sub(
                r'from key_management_service\.main import',
                'from main import',
                content
            )
        
        # Fix alerting-notification-service imports
        content = re.sub(
            r'from alerting_notification_service\.',
            'from alerting-notification-service.',
            content
        )
        
        # Fix budgeting database imports
        content = re.sub(
            r'from \.\.database\.models import',
            'from budgeting_rate_limiting_cost_observability.database.models import',
            content
        )
        
        # Fix ollama_ai_agent PACKAGE_ROOT
        if 'ollama_ai_agent' in str(file_path):
            content = re.sub(
                r'PACKAGE_ROOT = Path\(__file__\)\.resolve\(\)\.parent\.parent\.parent',
                'PACKAGE_ROOT = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "shared-services" / "ollama-ai-agent"',
                content
            )
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Main entry point."""
    # Set up integration_adapters package
    setup_integration_adapters_package()
    
    tests_dir = Path('tests')
    fixed = 0
    
    for test_file in tests_dir.rglob('*.py'):
        if fix_file(test_file):
            fixed += 1
            if fixed % 10 == 0:
                print(f"Fixed {fixed} files...")
    
    print(f"\nFixed {fixed} files total")

if __name__ == '__main__':
    main()

