#!/usr/bin/env python3
"""Debug script to test marker standardization on a specific file."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from standardize_markers_simple import SimpleMarkerStandardizer

def main():
    project_root = Path(__file__).parent.parent.parent
    standardizer = SimpleMarkerStandardizer(project_root)
    
    # Test on constitution file
    test_file = project_root / "tests" / "config" / "constitution" / "test_constitution_rules_json.py"
    
    print("=" * 80)
    print("DEBUGGING MARKER STANDARDIZATION")
    print("=" * 80)
    print(f"\nFile: {test_file}")
    print(f"Exists: {test_file.exists()}")
    
    # Determine markers
    markers = standardizer.determine_markers_from_path(test_file)
    print(f"\nMarkers determined: {markers}")
    
    # Read file
    content = test_file.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # Check first few test functions
    print("\nChecking first 5 test functions:")
    test_func_count = 0
    for i, line in enumerate(lines):
        if re.match(r'^\s*def\s+test_\w+', line):
            test_func_count += 1
            func_name = re.match(r'^\s*def\s+(test_\w+)', line).group(1)
            indent = len(line) - len(line.lstrip())
            has_markers = standardizer.has_pytest_markers(content, i)
            
            # Check if in class
            is_in_class = False
            for j in range(i - 1, max(0, i - 10), -1):
                if re.match(r'^\s*class\s+', lines[j]):
                    is_in_class = True
                    break
                elif lines[j].strip() and not lines[j].strip().startswith('@'):
                    break
            
            print(f"  {test_func_count}. {func_name}")
            print(f"     Line {i+1}, indent: {indent}, in_class: {is_in_class}, has_markers: {has_markers}")
            if test_func_count >= 5:
                break
    
    # Process file
    print("\nProcessing file...")
    modified, changes = standardizer.process_file(test_file, dry_run=True)
    print(f"Modified: {modified}")
    print(f"Number of changes: {len(changes)}")
    if changes:
        print("\nFirst 5 changes:")
        for change in changes[:5]:
            print(f"  - {change}")
    else:
        print("\nNo changes detected - this is the problem!")

if __name__ == '__main__':
    import re
    main()
