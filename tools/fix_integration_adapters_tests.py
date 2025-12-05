#!/usr/bin/env python3
"""
Fix all integration_adapters test files to use correct paths.
"""
from pathlib import Path
import re

def fix_test_file(file_path: Path):
    """Fix a single test file."""
    content = file_path.read_text(encoding='utf-8')
    original = content
    
    # Fix relative path calculations
    if 'os.path.join(os.path.dirname(__file__), "../..")' in content:
        # Replace with proper module root calculation
        if 'from pathlib import Path' not in content:
            # Add Path import if not present
            if 'import sys' in content:
                content = content.replace('import sys', 'import sys\nfrom pathlib import Path')
            elif 'import os' in content:
                content = content.replace('import os', 'import os\nfrom pathlib import Path')
            else:
                # Add at top after __future__ imports
                content = re.sub(
                    r'(from __future__ import .+\n)',
                    r'\1from pathlib import Path\n',
                    content,
                    count=1
                )
        
        # Replace the path calculation
        content = re.sub(
            r'sys\.path\.insert\(0, os\.path\.join\(os\.path\.dirname\(__file__\), "\.\./\.\."\)\)',
            'module_root = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "client-services" / "integration-adapters"\nsys.path.insert(0, str(module_root))',
            content
        )
        
        content = re.sub(
            r'package_path = os\.path\.join\(os\.path\.dirname\(__file__\), "\.\./\.\."\)',
            'package_path = str(module_root)',
            content
        )
    
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

