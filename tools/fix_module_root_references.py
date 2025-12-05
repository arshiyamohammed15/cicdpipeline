#!/usr/bin/env python3
"""
Remove all module_root/MODULE_ROOT references from test files.
Root conftest.py handles module setup now.
"""
from pathlib import Path
import re

def fix_file(file_path: Path) -> bool:
    """Remove module_root references from a test file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # Remove module_root variable definitions
        content = re.sub(r'^\s*module_root\s*=.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*MODULE_ROOT\s*=.*$', '', content, flags=re.MULTILINE)
        
        # Remove sys.path.insert calls using module_root
        content = re.sub(r'sys\.path\.insert\(0,\s*str\(module_root\)\)', 
                        '# Module setup handled by root conftest.py', content)
        content = re.sub(r'sys\.path\.insert\(0,\s*str\(MODULE_ROOT\)\)', 
                        '# Module setup handled by root conftest.py', content)
        
        # Remove standalone import statements if they're only used for module_root
        # But keep them if they're used elsewhere
        lines = content.split('\n')
        new_lines = []
        skip_next = False
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
            # Skip lines that are just module_root setup
            if re.match(r'^\s*(import sys|import os|from pathlib import Path)\s*$', line):
                # Check if next lines are module_root related
                if i + 1 < len(lines) and 'module_root' in lines[i + 1]:
                    skip_next = True
                    continue
            new_lines.append(line)
        content = '\n'.join(new_lines)
        
        # Clean up multiple blank lines
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
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
    
    # Fix integration_adapters files
    integration_adapters_dir = tests_dir / 'cloud_services' / 'client_services' / 'integration_adapters'
    if integration_adapters_dir.exists():
        for test_file in integration_adapters_dir.rglob('*.py'):
            if fix_file(test_file):
                fixed += 1
                if fixed % 10 == 0:
                    print(f"Fixed {fixed} files...")
    
    print(f"\nFixed {fixed} files total")

if __name__ == '__main__':
    main()

