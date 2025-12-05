#!/usr/bin/env python3
"""
Fix import paths in test files.
"""
import re
from pathlib import Path
from typing import Dict, List

# Import path mappings
IMPORT_FIXES = {
    # Integration adapters
    r'^from services\.': 'from integration_adapters.services.',
    r'^from database\.': 'from integration_adapters.database.',
    r'^from adapters\.': 'from integration_adapters.adapters.',
    r'^from reliability\.': 'from integration_adapters.reliability.',
    r'^from observability\.': 'from integration_adapters.observability.',
    r'^from models import': 'from integration_adapters.models import',
    r'^from config import': 'from integration_adapters.config import',
    
    # Deployment infrastructure
    r'^from \.\.services import': 'from deployment_infrastructure.services import',
    
    # Data governance privacy
    r'from data_governance_privacy\.tests\.harness': 'from tests.cloud_services.shared_services.data_governance_privacy.test_harness',
}

# File path fixes
FILE_PATH_FIXES = [
    (r'src\\cloud-services\\', 'src/cloud_services/'),
    (r'src/cloud-services/', 'src/cloud_services/'),
]


def fix_imports_in_file(file_path: Path) -> bool:
    """Fix imports in a single file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Apply import fixes
        for pattern, replacement in IMPORT_FIXES.items():
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Apply file path fixes
        for pattern, replacement in FILE_PATH_FIXES:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Main entry point."""
    tests_dir = Path('tests')
    fixed_count = 0
    
    for test_file in tests_dir.rglob('*.py'):
        if fix_imports_in_file(test_file):
            fixed_count += 1
            print(f"Fixed: {test_file}")
    
    print(f"\nFixed {fixed_count} files")


if __name__ == '__main__':
    main()

