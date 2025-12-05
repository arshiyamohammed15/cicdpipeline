#!/usr/bin/env python3
"""
Fix all integration_adapters test files to use correct import paths.
"""
from pathlib import Path
import re

def fix_test_file(file_path: Path):
    """Fix imports in a test file."""
    content = file_path.read_text(encoding='utf-8')
    original = content
    
    # Add Path import if needed
    if 'from pathlib import Path' not in content and 'os.path.join' in content:
        if 'import os' in content:
            content = content.replace('import os', 'import os\nfrom pathlib import Path')
        elif 'import sys' in content:
            content = content.replace('import sys', 'import sys\nfrom pathlib import Path')
    
    # Fix path calculations
    patterns = [
        (r'sys\.path\.insert\(0, os\.path\.join\(os\.path\.dirname\(__file__\), "\.\./\.\."\)\)',
         'module_root = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "client-services" / "integration-adapters"\nsys.path.insert(0, str(module_root))'),
        (r'sys\.path\.insert\(0, os\.path\.join\(os\.path\.dirname\(__file__\), "\.\./\.\./\.\./\.\./src/cloud_services/client-services/integration-adapters"\)\)',
         'module_root = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "client-services" / "integration-adapters"\nsys.path.insert(0, str(module_root))'),
        (r'package_path = os\.path\.join\(os\.path\.dirname\(__file__\), "\.\./\.\."\)',
         'package_path = str(module_root)'),
        (r'package_path = os\.path\.join\(os\.path\.dirname\(__file__\), "\.\./\.\./\.\./\.\./src/cloud_services/client-services/integration-adapters"\)',
         'package_path = str(module_root)'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return True
    return False

def main():
    """Main entry point."""
    tests_dir = Path('tests/cloud_services/client_services/integration_adapters')
    fixed = 0
    
    for test_file in tests_dir.rglob('*.py'):
        if fix_test_file(test_file):
            fixed += 1
            print(f"Fixed: {test_file}")
    
    print(f"\nFixed {fixed} files")

if __name__ == '__main__':
    main()

