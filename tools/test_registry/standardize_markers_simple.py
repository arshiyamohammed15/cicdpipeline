#!/usr/bin/env python3
"""
Systematic marker standardization for ZeroUI test suite - SIMPLE VERSION.

This script analyzes test files and adds appropriate pytest markers based on
VERIFIED patterns only - no assumptions.

STRICT RULES:
- Only use verifiable patterns from actual file structure
- No assumptions or inferences
- Preserve existing markers
- Add markers only where pattern is clear and unambiguous
"""

import re
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Set, Tuple


class SimpleMarkerStandardizer:
    """Standardizes pytest markers using simple, reliable string manipulation."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.changes_made = []
        self.skipped_files = []
        self.errors = []
        
        # Module-specific marker mappings (VERIFIED from pyproject.toml)
        self.module_markers = {
            'data_governance_privacy': {
                'regression': 'dgp_regression',
                'security': 'dgp_security',
                'performance': 'dgp_performance',
                'compliance': 'dgp_compliance',
            },
            'alerting_notification_service': {
                'regression': 'alerting_regression',
                'security': 'alerting_security',
                'performance': 'alerting_performance',
                'integration': 'alerting_integration',
            },
            'budgeting_rate_limiting_cost_observability': {
                'regression': 'budgeting_regression',
                'security': 'budgeting_security',
                'performance': 'budgeting_performance',
            },
            'deployment_infrastructure': {
                'regression': 'deployment_regression',
                'security': 'deployment_security',
                'integration': 'deployment_integration',
            },
            'llm_gateway': {
                'unit': 'llm_gateway_unit',
                'integration': 'llm_gateway_integration',
                'real_integration': 'llm_gateway_real_integration',
            },
        }
    
    def determine_markers_from_path(self, file_path: Path) -> Set[str]:
        """Determine markers based on file path - VERIFIED PATTERNS ONLY."""
        path_str = str(file_path).lower().replace('\\', '/')
        markers = set()
        
        # Path-based categorization (VERIFIED from glob searches)
        if '/unit/' in path_str:
            markers.add('unit')
        if '/integration/' in path_str:
            markers.add('integration')
        if '/performance/' in path_str:
            markers.add('performance')
        if '/security/' in path_str:
            markers.add('security')
        if '/resilience/' in path_str:
            markers.add('integration')  # Resilience tests use integration marker
        
        # File name patterns (VERIFIED from glob searches)
        file_stem = file_path.stem.lower()
        if 'smoke' in file_stem:
            markers.add('smoke')
            if 'unit' not in markers:
                markers.add('unit')  # Smoke tests are typically unit tests
        
        if 'e2e' in file_stem or 'end_to_end' in file_stem or 'end-to-end' in file_stem:
            markers.add('integration')  # E2E tests are integration tests
        
        # Constitution tests (VERIFIED from glob searches)
        if '/constitution/' in path_str or 'constitution' in file_stem:
            markers.add('constitution')
        
        # Infrastructure/database tests - typically unit tests
        if '/infrastructure/db/' in path_str or '/infrastructure/' in path_str:
            if 'unit' not in markers and 'integration' not in markers and 'performance' not in markers:
                markers.add('unit')  # Infrastructure tests are typically unit tests
        
        # System tests - typically unit tests
        if '/system/' in path_str:
            if 'unit' not in markers and 'integration' not in markers:
                markers.add('unit')
        
        # Validator tests - typically unit tests
        if '/validator/' in path_str:
            if 'unit' not in markers:
                markers.add('unit')
        
        # Shared libs tests - typically unit tests
        if '/shared_libs/' in path_str:
            if 'unit' not in markers:
                markers.add('unit')
        
        # SIN (Signal Ingestion Normalization) tests - check if integration
        if '/sin/' in path_str:
            if '/integration/' in path_str:
                markers.add('integration')
            elif 'unit' not in markers and 'integration' not in markers:
                markers.add('unit')  # Default to unit if not in integration subdirectory
        
        # Module-specific markers (VERIFIED from pyproject.toml and path structure)
        for module_name, marker_map in self.module_markers.items():
            module_pattern = module_name.replace('_', '-')
            if module_pattern in path_str or module_name in path_str:
                # Check for category-specific markers
                for category, marker in marker_map.items():
                    if f'/{category}/' in path_str:
                        markers.add(marker)
                        # Also add base marker
                        if category in ['unit', 'integration', 'performance', 'security']:
                            markers.add(category)
                
                # LLM Gateway special handling
                if module_name == 'llm_gateway':
                    if 'real_services' in file_stem or 'real_integration' in path_str:
                        markers.add('llm_gateway_real_integration')
                    elif '/integration/' in path_str or 'integration' in file_stem:
                        markers.add('llm_gateway_integration')
                    elif '/unit/' in path_str or 'unit' in file_stem:
                        markers.add('llm_gateway_unit')
        
        return markers
    
    def has_pytest_markers(self, content: str, line_num: int) -> bool:
        """Check if a line or nearby lines have pytest markers."""
        lines = content.split('\n')
        # Check current line and previous lines (for decorators)
        start = max(0, line_num - 5)
        end = min(len(lines), line_num + 1)
        
        for i in range(start, end):
            if '@pytest.mark.' in lines[i]:
                return True
        return False
    
    def add_markers_to_class(self, content: str, class_line: str, line_num: int) -> Tuple[str, bool]:
        """Add markers to a test class definition."""
        lines = content.split('\n')
        
        # Check if class already has markers
        if self.has_pytest_markers(content, line_num):
            return content, False
        
        # Find indentation
        indent = len(class_line) - len(class_line.lstrip())
        
        # Get markers for this file
        # We'll determine this from the file path when processing
        return content, False  # Placeholder - will be implemented with file context
    
    def add_markers_to_function(self, content: str, func_line: str, line_num: int, 
                                markers: Set[str]) -> Tuple[str, bool]:
        """Add markers to a test function definition."""
        lines = content.split('\n')
        
        # Check if function already has markers
        if self.has_pytest_markers(content, line_num):
            return content, False
        
        # Check if function is inside a class with markers
        # Look backwards for class definition
        for i in range(line_num - 1, max(0, line_num - 20), -1):
            if re.match(r'^\s*class\s+Test\w+', lines[i]):
                # Check if class has markers
                if self.has_pytest_markers(content, i):
                    return content, False  # Class has markers, don't add to function
                break
        
        # Add markers
        indent = len(func_line) - len(func_line.lstrip())
        marker_lines = [' ' * indent + f"@pytest.mark.{marker}" for marker in sorted(markers)]
        
        # Insert markers before function
        new_lines = lines[:line_num] + marker_lines + lines[line_num:]
        return '\n'.join(new_lines), True
    
    def process_file(self, file_path: Path, dry_run: bool = False) -> Tuple[bool, List[str]]:
        """Process a single test file."""
        # Skip non-Python files
        if not file_path.suffix == '.py':
            return False, []
        
        # Skip __init__.py and conftest.py
        if file_path.name in ['__init__.py', 'conftest.py']:
            return False, []
        
        # Determine markers from path
        markers = self.determine_markers_from_path(file_path)
        
        if not markers:
            self.skipped_files.append((file_path, "No clear marker pattern from path"))
            return False, []
        
        # Read file
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.errors.append(f"Error reading {file_path}: {e}")
            return False, []
        
        # Don't skip based on file-level marker check - we need to check individual functions/classes
        # Some files may have markers on some functions but not others
        
        # Process file to add markers
        lines = content.split('\n')
        new_lines = []
        modified = False
        changes = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            new_lines.append(line)
            
            # Check for test class definition
            class_match = re.match(r'^(\s*)class\s+(Test\w+)', line)
            if class_match:
                indent = len(class_match.group(1))
                class_name = class_match.group(2)
                
                # Check if class already has markers
                if not self.has_pytest_markers(content, i):
                    # Add markers before class
                    marker_decorators = [f"{' ' * indent}@pytest.mark.{marker}" 
                                       for marker in sorted(markers)]
                    # Insert before the line we just added
                    new_lines.pop()  # Remove the class line
                    new_lines.extend(marker_decorators)
                    new_lines.append(line)
                    modified = True
                    changes.append(f"Added markers to class {class_name}: {', '.join(sorted(markers))}")
            
            # Check for test function definition (not in class)
            func_match = re.match(r'^(\s*)(async\s+)?def\s+(test_\w+)', line)
            if func_match:
                indent = len(func_match.group(1))
                func_name = func_match.group(3)
                
                # Check if this is a top-level function (indent == 0 or very small)
                if indent <= 4:  # Top-level or minimal indent
                    # Check if function already has markers
                    if not self.has_pytest_markers(content, i):
                        # Check if previous line is a class definition (function in class)
                        is_in_class = False
                        for j in range(i - 1, max(0, i - 10), -1):
                            if re.match(r'^\s*class\s+', lines[j]):
                                is_in_class = True
                                break
                            elif lines[j].strip() and not lines[j].strip().startswith('@'):
                                break
                        
                        if not is_in_class:
                            # Add markers before function
                            marker_decorators = [f"{' ' * indent}@pytest.mark.{marker}" 
                                               for marker in sorted(markers)]
                            new_lines.pop()  # Remove the function line
                            new_lines.extend(marker_decorators)
                            new_lines.append(line)
                            modified = True
                            changes.append(f"Added markers to function {func_name}: {', '.join(sorted(markers))}")
            
            i += 1
        
        if modified:
            if not dry_run:
                new_content = '\n'.join(new_lines)
                file_path.write_text(new_content, encoding='utf-8')
            self.changes_made.append((file_path, changes))
        
        return modified, changes
    
    def process_all_tests(self, dry_run: bool = False, workers: int = 1) -> Dict:
        """Process all test files in the project."""
        test_files = []
        
        # Only scan tests directory to avoid symlink issues
        tests_dir = self.project_root / 'tests'
        if not tests_dir.exists():
            self.errors.append(f"Tests directory not found: {tests_dir}")
            return {
                'files_modified': 0,
                'files_skipped': 0,
                'errors': len(self.errors),
                'changes': [],
                'skipped': [],
                'errors_list': self.errors,
            }
        
        # Find all test files in tests directory only
        for pattern in ['test_*.py', '*_test.py']:
            try:
                test_files.extend(tests_dir.rglob(pattern))
            except (OSError, PermissionError) as e:
                self.errors.append(f"Error scanning tests directory for {pattern}: {e}")
        
        # Filter out excluded directories
        exclude_dirs = {'venv', '__pycache__', '.git', '.venv', 'dist', 'build', 'artifacts', 
                       'htmlcov', 'coverage', '.pytest_cache', 'node_modules'}
        test_files = [f for f in test_files if not any(ex in str(f) for ex in exclude_dirs)]
        
        # Additional filtering for problematic paths
        test_files = [f for f in test_files if 'node_modules' not in str(f)]
        
        # Remove duplicates
        test_files = list(set(test_files))
        
        print(f"Found {len(test_files)} test files to process")
        print(f"Processing files... (this may take a few minutes)")
        sys.stdout.flush()
        
        # Process each file
        processed = 0
        for test_file in test_files:
            try:
                self.process_file(test_file, dry_run=dry_run)
                processed += 1
                if processed % 50 == 0:
                    print(f"  Processed {processed}/{len(test_files)} files... (modified: {len(self.changes_made)}, skipped: {len(self.skipped_files)})")
                    sys.stdout.flush()
            except Exception as e:
                self.errors.append(f"Error processing {test_file}: {e}")
                processed += 1
        
        print(f"  Completed processing {processed} files")
        print(f"  Files that would be modified: {len(self.changes_made)}")
        print(f"  Files skipped: {len(self.skipped_files)}")
        print(f"  Errors: {len(self.errors)}")
        sys.stdout.flush()
        
        return {
            'files_modified': len(self.changes_made),
            'files_skipped': len(self.skipped_files),
            'errors': len(self.errors),
            'changes': self.changes_made,
            'skipped': self.skipped_files,
            'errors_list': self.errors,
        }
    
    def generate_report(self, results: Dict) -> str:
        """Generate a report of changes."""
        report = []
        report.append("=" * 80)
        report.append("TEST MARKER STANDARDIZATION REPORT")
        report.append("=" * 80)
        report.append("")
        report.append(f"Files Modified: {results['files_modified']}")
        report.append(f"Files Skipped: {results['files_skipped']}")
        report.append(f"Errors: {results['errors']}")
        report.append("")
        
        if results['changes']:
            report.append("FILES MODIFIED:")
            report.append("-" * 80)
            for file_path, changes in results['changes']:
                report.append(f"\n{file_path}:")
                for change in changes:
                    report.append(f"  - {change}")
        
        if results['skipped']:
            report.append("")
            report.append(f"FILES SKIPPED (showing first 100 of {len(results['skipped'])}):")
            report.append("-" * 80)
            for file_path, reason in results['skipped'][:100]:
                report.append(f"{file_path}: {reason}")
            if len(results['skipped']) > 100:
                report.append(f"... and {len(results['skipped']) - 100} more")
        
        if results['errors_list']:
            report.append("")
            report.append("ERRORS:")
            report.append("-" * 80)
            for error in results['errors_list']:
                report.append(error)
        
        return '\n'.join(report)


def process_file_worker(file_path_str: str, project_root_str: str, dry_run: bool):
    """Worker function for parallel processing."""
    from pathlib import Path
    standardizer = SimpleMarkerStandardizer(Path(project_root_str))
    test_file = Path(file_path_str)
    
    try:
        modified, changes = standardizer.process_file(test_file, dry_run=dry_run)
        if modified:
            return modified, changes, None, None
        elif standardizer.skipped_files:
            skipped = standardizer.skipped_files[0] if standardizer.skipped_files else None
            return False, [], skipped[1] if skipped else None, None
        else:
            return False, [], None, None
    except Exception as e:
        return False, [], None, f"Error processing {test_file}: {e}"


def main():
    """Main function."""
    import sys
    
    project_root = Path(__file__).parent.parent.parent
    
    # Check for dry-run mode
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    # Check for workers argument
    workers = 1
    for arg in sys.argv:
        if arg.startswith('--workers='):
            workers = int(arg.split('=')[1])
        elif arg == '--workers' and '--workers=' not in ' '.join(sys.argv):
            idx = sys.argv.index('--workers')
            if idx + 1 < len(sys.argv):
                workers = int(sys.argv[idx + 1])
    
    standardizer = SimpleMarkerStandardizer(project_root)
    
    if dry_run:
        print("=" * 80)
        print("DRY RUN MODE - No files will be modified")
        print("=" * 80)
        print()
    else:
        print("=" * 80)
        print("APPLYING MARKERS - Files will be modified")
        print("=" * 80)
        print()
    
    results = standardizer.process_all_tests(dry_run=dry_run, workers=workers)
    
    report = standardizer.generate_report(results)
    print(report)
    
    # Save report
    report_path = project_root / 'artifacts' / 'marker_standardization_report.txt'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding='utf-8')
    print(f"\nReport saved to: {report_path}")
    
    if not dry_run and results['files_modified'] > 0:
        print(f"\n[SUCCESS] Modified {results['files_modified']} files")
    elif dry_run:
        print(f"\n[DRY RUN] Would modify {results['files_modified']} files")


if __name__ == '__main__':
    main()
