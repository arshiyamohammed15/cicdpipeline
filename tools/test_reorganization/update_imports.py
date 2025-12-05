#!/usr/bin/env python3
"""
Update imports in migrated test files.

Fixes import paths after test migration to new structure.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Import pattern mappings
IMPORT_PATTERNS = [
    # Module-specific imports
    (r"from identity_access_management\.", r"from identity_access_management."),
    (r"from key_management_service\.", r"from key_management_service."),
    (r"from data_governance_privacy\.", r"from data_governance_privacy."),
    # Path-based imports
    (r"sys\.path\.insert\(0, str\(.*?\)\)", ""),  # Remove path manipulations
]


def update_imports_in_file(file_path: Path) -> bool:
    """Update imports in a test file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content
        
        # Update import paths
        # Remove old path manipulations
        content = re.sub(
            r"PACKAGE_ROOT = Path\(__file__\)\.resolve\(\)\.parents\[\d+\]",
            "PACKAGE_ROOT = Path(__file__).resolve().parents[5]  # Updated for new structure",
            content,
        )
        
        content = re.sub(
            r"project_root = Path\(__file__\)\.resolve\(\)\.parents\[\d+\]",
            "project_root = Path(__file__).resolve().parents[5]  # Updated for new structure",
            content,
        )
        
        # Update sys.path.insert statements
        content = re.sub(
            r"sys\.path\.insert\(0, str\(PACKAGE_ROOT\)\)",
            "# Path setup handled by conftest.py",
            content,
        )
        
        content = re.sub(
            r"sys\.path\.insert\(0, str\(project_root\)\)",
            "# Path setup handled by conftest.py",
            content,
        )
        
        # Add import for conftest if needed
        if "from conftest import" not in content and "import conftest" not in content:
            # Add after existing imports
            import_section = re.search(r"(^import .+?$|^from .+?$)", content, re.MULTILINE)
            if import_section:
                insert_pos = content.rfind("\n", 0, import_section.end()) + 1
                content = (
                    content[:insert_pos]
                    + "\n# Imports handled by conftest.py\n"
                    + content[insert_pos:]
                )
        
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            return True
        
        return False
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def update_imports_in_directory(directory: Path, dry_run: bool = False) -> Tuple[int, int]:
    """Update imports in all test files in a directory."""
    updated = 0
    errors = 0
    
    for test_file in directory.rglob("test_*.py"):
        if dry_run:
            print(f"Would update: {test_file}")
            updated += 1
        else:
            if update_imports_in_file(test_file):
                updated += 1
                print(f"Updated: {test_file}")
            else:
                errors += 1
    
    return updated, errors


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update imports in migrated tests")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without updating",
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=PROJECT_ROOT / "tests" / "cloud_services",
        help="Directory to update (default: tests/cloud_services)",
    )
    args = parser.parse_args()
    
    updated, errors = update_imports_in_directory(args.directory, args.dry_run)
    
    print(f"\nUpdate Summary:")
    print(f"  Updated: {updated}")
    print(f"  Errors: {errors}")


if __name__ == "__main__":
    main()

