#!/usr/bin/env python3
"""
Comprehensive fix for all test import and path issues.
"""
from pathlib import Path
import re
import sys

def fix_imports(content: str, file_path: Path) -> str:
    """Fix all import issues in content."""
    original = content
    
    # Fix evidence_receipt_indexing_service imports
    content = re.sub(r'from \.\.services import', 'from evidence_receipt_indexing_service.services import', content)
    
    # Fix budgeting database imports
    content = re.sub(
        r'from tests\.cloud_services\.shared_services\.budgeting_rate_limiting_cost_observability\.database import',
        'from budgeting_rate_limiting_cost_observability.database import',
        content
    )
    content = re.sub(
        r'from \.\.database import',
        'from budgeting_rate_limiting_cost_observability.database import',
        content
    )
    
    # Fix detection_engine_core imports
    if 'detection_engine_core' in str(file_path):
        content = re.sub(r'^from main import', 'from detection_engine_core.main import', content, flags=re.MULTILINE)
        content = re.sub(r'^from routes import', 'from detection_engine_core.routes import', content, flags=re.MULTILINE)
        content = re.sub(r'^from services import', 'from detection_engine_core.services import', content, flags=re.MULTILINE)
        content = re.sub(r'^from models import', 'from detection_engine_core.models import', content, flags=re.MULTILINE)
    
    # Fix identity_access_management imports (hyphenated module name)
    content = re.sub(
        r'from identity_access_management\.main import',
        'from identity-access-management.main import app',
        content
    )
    content = re.sub(
        r'identity_access_management\.main',
        'identity-access-management.main',
        content
    )
    
    # Fix key_management_service imports (hyphenated module name)
    content = re.sub(
        r'from key_management_service\.main import',
        'from key-management-service.main import app',
        content
    )
    content = re.sub(
        r'key_management_service\.main',
        'key-management-service.main',
        content
    )
    
    # Fix alerting_notification_service imports (hyphenated module name)
    content = re.sub(
        r'from alerting_notification_service import',
        'from alerting-notification-service import',
        content
    )
    
    # Fix models imports in wrong locations
    content = re.sub(
        r'from tests\.cloud_services\.shared_services\.models import',
        '# Models should be imported from module',
        content
    )
    content = re.sub(
        r'from tests\.cloud_services\.product_services\.models import',
        '# Models should be imported from module',
        content
    )
    
    # Fix service_registry imports
    content = re.sub(
        r'from service_registry import',
        'from integration_adapters.service_registry import',
        content
    )
    
    # Fix integrations imports
    content = re.sub(
        r'from integrations\.',
        'from integration_adapters.integrations.',
        content
    )
    
    return content

def fix_file(file_path: Path) -> bool:
    """Fix a single test file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        content = fix_imports(content, file_path)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Main entry point."""
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

