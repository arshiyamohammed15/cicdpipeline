#!/usr/bin/env python3
"""
Limited version - processes first 20 test files to verify functionality.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from standardize_markers_simple import SimpleMarkerStandardizer

def main():
    project_root = Path(__file__).parent.parent.parent
    
    print("=" * 80)
    print("LIMITED MARKER STANDARDIZATION - FIRST 20 FILES")
    print("=" * 80)
    print()
    
    standardizer = SimpleMarkerStandardizer(project_root)
    
    # Find test files
    test_files = []
    for pattern in ['test_*.py', '*_test.py']:
        test_files.extend(project_root.rglob(pattern))
    
    exclude_dirs = {'venv', '__pycache__', '.git', '.venv', 'dist', 'build', 'artifacts', 
                   'htmlcov', 'coverage', '.pytest_cache', 'node_modules'}
    test_files = [f for f in test_files if not any(ex in str(f) for ex in exclude_dirs)]
    test_files = list(set(test_files))
    
    # Limit to first 20 files
    test_files = sorted(test_files)[:20]
    
    print(f"Processing first {len(test_files)} test files:")
    print()
    
    for test_file in test_files:
        markers = standardizer.determine_markers_from_path(test_file)
        if markers:
            print(f"{test_file.name}: {sorted(markers)}")
            modified, changes = standardizer.process_file(test_file, dry_run=True)
            if modified:
                print(f"  → Would modify ({len(changes)} changes)")
                for change in changes[:3]:  # Show first 3 changes
                    print(f"    - {change}")
                if len(changes) > 3:
                    print(f"    ... and {len(changes) - 3} more")
            else:
                print(f"  → No changes needed")
        else:
            print(f"{test_file.name}: [no clear pattern - would skip]")
        print()
    
    print("=" * 80)
    print(f"Summary: {len(standardizer.changes_made)} files would be modified")
    print(f"         {len(standardizer.skipped_files)} files would be skipped")
    print("=" * 80)

if __name__ == '__main__':
    main()
