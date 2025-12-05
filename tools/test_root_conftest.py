#!/usr/bin/env python3
"""
Test script to verify root conftest.py works correctly.
"""
import sys
from pathlib import Path

# Simulate pytest's conftest loading
sys.path.insert(0, str(Path('tests').resolve()))

# Import root conftest (this should set up all modules)
print("Before import - checking paths...")
PROJECT_ROOT = Path('tests').resolve().parent
SRC_ROOT = PROJECT_ROOT / 'src' / 'cloud_services'
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"SRC_ROOT: {SRC_ROOT}")
print(f"SRC_ROOT exists: {SRC_ROOT.exists()}")

# Manually call setup to see what happens
print("\nManually testing setup_module_package...")
import types
import importlib.util

for category in ["shared-services", "client-services", "product-services"]:
    category_path = SRC_ROOT / category.replace("-", "_")
    print(f"\nCategory: {category}, path: {category_path}, exists: {category_path.exists()}")
    if category_path.exists():
        items = list(category_path.iterdir())
        dirs = [i for i in items if i.is_dir() and not i.name.startswith("_")]
        print(f"  Found {len(dirs)} directories")
        for item in dirs[:3]:  # Just first 3
            print(f"    Setting up: {item.name}")
            python_pkg_name = conftest.MODULE_MAPPINGS.get(item.name, item.name.replace("-", "_"))
            module_path = SRC_ROOT / category.replace("-", "_") / item.name
            print(f"      Python pkg: {python_pkg_name}, module_path: {module_path}, exists: {module_path.exists()}")
            if module_path.exists():
                pkg = types.ModuleType(python_pkg_name)
                pkg.__path__ = [str(module_path)]
                sys.modules[python_pkg_name] = pkg
                print(f"      ✓ Created package: {python_pkg_name}")

import conftest

print(f"\nAfter import:")
print(f"conftest.PROJECT_ROOT: {conftest.PROJECT_ROOT}")
print(f"conftest.SRC_ROOT: {conftest.SRC_ROOT}")
print(f"conftest.SRC_ROOT.exists(): {conftest.SRC_ROOT.exists()}")

# Check if modules were set up
print("\nChecking module setup...")
print(f"integration_adapters in sys.modules: {'integration_adapters' in sys.modules}")
print(f"identity_access_management in sys.modules: {'identity_access_management' in sys.modules}")
print(f"key_management_service in sys.modules: {'key_management_service' in sys.modules}")

# Try importing
try:
    import integration_adapters
    print(f"✓ Can import integration_adapters: {integration_adapters}")
    print(f"  Has __path__: {hasattr(integration_adapters, '__path__')}")
    if hasattr(integration_adapters, '__path__'):
        print(f"  __path__: {integration_adapters.__path__}")
    
    if hasattr(integration_adapters, 'services'):
        print(f"✓ Has services subpackage")
    else:
        print("✗ Missing services subpackage")
        # Try to import it
        try:
            from integration_adapters.services import signal_mapper
            print("  But can import from integration_adapters.services")
        except Exception as e:
            print(f"  Cannot import: {e}")
            
except Exception as e:
    print(f"✗ Cannot import integration_adapters: {e}")

# List all integration_adapters modules
print("\nAll integration_adapters modules:")
for key in sorted(sys.modules.keys()):
    if 'integration_adapters' in key:
        print(f"  {key}")

