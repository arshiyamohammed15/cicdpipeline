#!/usr/bin/env python3
"""
Quick test of marker standardization on a small sample of files.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from standardize_markers_simple import SimpleMarkerStandardizer

def main():
    project_root = Path(__file__).parent.parent.parent
    
    print("=" * 80)
    print("TESTING MARKER STANDARDIZATION - SAMPLE FILES")
    print("=" * 80)
    print()
    
    standardizer = SimpleMarkerStandardizer(project_root)
    
    # Test on a few sample files
    test_files = [
        project_root / "tests" / "config" / "constitution" / "test_constitution_rules_json.py",
        project_root / "tests" / "infrastructure" / "db" / "test_schema_pack_contract.py",
        project_root / "tests" / "platform_smoke" / "test_platform_smoke.py",
    ]
    
    print(f"Testing on {len(test_files)} sample files:")
    for f in test_files:
        print(f"  - {f}")
    print()
    
    for test_file in test_files:
        if test_file.exists():
            print(f"Processing: {test_file.name}")
            markers = standardizer.determine_markers_from_path(test_file)
            print(f"  Determined markers: {sorted(markers)}")
            modified, changes = standardizer.process_file(test_file, dry_run=True)
            if modified:
                print(f"  Would modify: YES")
                for change in changes:
                    print(f"    - {change}")
            else:
                print(f"  Would modify: NO")
            print()
        else:
            print(f"File not found: {test_file}")
            print()
    
    print("=" * 80)
    print("Sample test complete!")
    print("=" * 80)

if __name__ == '__main__':
    main()
