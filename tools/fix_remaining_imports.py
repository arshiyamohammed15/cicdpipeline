#!/usr/bin/env python3
"""
Fix remaining import issues in test files.
"""
from pathlib import Path
import re

def fix_file(file_path: Path) -> bool:
    """Fix imports in a test file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Fix alerting_notification_service imports (hyphenated)
        content = re.sub(
            r'from alerting_notification_service\.',
            'from alerting-notification-service.',
            content
        )
        
        # Fix identity_access_management imports (hyphenated)
        if 'identity_access_management' in str(file_path) or 'identity-access-management' in str(file_path):
            content = re.sub(
                r'from identity_access_management\.main import',
                'import sys\nfrom pathlib import Path\nMODULE_ROOT = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "shared-services" / "identity-access-management"\nsys.path.insert(0, str(MODULE_ROOT))\nfrom main import',
                content
            )
        
        # Fix key_management_service imports (hyphenated)
        if 'key_management_service' in str(file_path) or 'key-management-service' in str(file_path):
            content = re.sub(
                r'from key_management_service\.main import',
                'import sys\nfrom pathlib import Path\nMODULE_ROOT = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "shared-services" / "key-management-service"\nsys.path.insert(0, str(MODULE_ROOT))\nfrom main import',
                content
            )
        
        # Fix detection_engine_core imports
        if 'detection_engine_core' in str(file_path):
            content = re.sub(r'^from main import', 'from detection_engine_core.main import', content, flags=re.MULTILINE)
            content = re.sub(r'^from routes import', 'from detection_engine_core.routes import', content, flags=re.MULTILINE)
            content = re.sub(r'^from services import', 'from detection_engine_core.services import', content, flags=re.MULTILINE)
            content = re.sub(r'^from models import', 'from detection_engine_core.models import', content, flags=re.MULTILINE)
        
        # Fix signal_ingestion_normalization PACKAGE_ROOT
        if 'signal_ingestion_normalization' in str(file_path):
            content = re.sub(
                r'PACKAGE_ROOT = Path\(__file__\)\.resolve\(\)\.parent\.parent\.parent',
                'PACKAGE_ROOT = Path(__file__).resolve().parents[4] / "src" / "cloud_services" / "product_services" / "signal-ingestion-normalization"',
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

