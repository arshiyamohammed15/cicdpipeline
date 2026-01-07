#!/usr/bin/env python3
"""
Direct file parsing to count all test cases - fast and accurate.
"""

import re
from collections import defaultdict
from pathlib import Path


def count_python_tests_in_file(file_path: Path) -> tuple[int, dict[str, int]]:
    """Count test cases in a Python file."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        return 0, {}
    
    # Count test functions (def test_*)
    test_function_pattern = r'^\s*(?:async\s+)?def\s+test_\w+'
    test_functions = len(re.findall(test_function_pattern, content, re.MULTILINE))
    
    # Count test methods in test classes (class Test*)
    test_class_pattern = r'^\s*class\s+Test\w+'
    test_classes = re.findall(test_class_pattern, content, re.MULTILINE)
    
    # Count test methods in each class
    test_methods = 0
    for class_match in test_classes:
        # Find the class definition and count test_ methods inside it
        class_start = content.find(class_match)
        if class_start == -1:
            continue
        
        # Find the class body (simplified - look for next class or end of indented block)
        lines = content[class_start:].split('\n')
        in_class = False
        indent_level = None
        
        for i, line in enumerate(lines):
            if i == 0:
                # This is the class line
                in_class = True
                indent_level = len(line) - len(line.lstrip())
                continue
            
            if not in_class:
                continue
            
            current_indent = len(line) - len(line.lstrip())
            
            # If we hit a line with same or less indent that's not empty and not a comment, we're out of the class
            if line.strip() and not line.strip().startswith('#'):
                if current_indent <= indent_level and not line.strip().startswith('@'):
                    break
            
            # Count test methods
            if re.match(r'^\s+def\s+test_\w+', line):
                test_methods += 1
    
    total = test_functions + test_methods
    
    # Extract markers
    markers = defaultdict(int)
    
    # Look for @pytest.mark.* decorators
    marker_pattern = r'@pytest\.mark\.(\w+)'
    found_markers = re.findall(marker_pattern, content, re.IGNORECASE)
    for marker in found_markers:
        markers[marker.lower()] += 1
    
    # If no markers found, count as unmarked
    if total > 0 and not found_markers:
        markers['unmarked'] = total
    
    return total, dict(markers)


def count_typescript_tests_in_file(file_path: Path) -> int:
    """Count test cases in a TypeScript/JavaScript file."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        return 0
    
    # Count it/test blocks (actual test cases)
    it_pattern = r'(?:it|test)\s*\([\'"][^\'"]+[\'"],\s*(?:\(\)\s*=>|async\s*\(\)\s*=>|function)'
    matches = re.findall(it_pattern, content, re.MULTILINE)
    return len(matches)


def find_test_files(root: Path, patterns: list[str], exclude: set[str]) -> list[Path]:
    """Find test files safely."""
    files = []
    for pattern in patterns:
        try:
            for path in root.rglob(pattern):
                path_str = str(path)
                if any(ex in path_str for ex in exclude):
                    continue
                try:
                    if path.is_file() and path.exists():
                        files.append(path)
                except (OSError, PermissionError):
                    continue
        except (OSError, PermissionError):
            continue
    return list(set(files))  # Remove duplicates


def main():
    """Main function."""
    project_root = Path(__file__).parent.parent.parent
    exclude_dirs = {'venv', '__pycache__', 'node_modules', '.git', '.venv', 'dist', 'build', 'artifacts', 'htmlcov', 'coverage', '.pytest_cache'}
    
    print("=" * 80)
    print("COMPREHENSIVE TEST CASE COUNT - ZEROUI PROJECT")
    print("=" * 80)
    print()
    
    # Find Python test files
    print("Scanning for Python test files...")
    python_files = find_test_files(project_root, ['test_*.py', '*_test.py'], exclude_dirs)
    print(f"Found {len(python_files)} Python test files")
    
    # Count Python tests
    python_total = 0
    python_markers = defaultdict(int)
    python_by_file = {}
    
    for test_file in python_files:
        count, markers = count_python_tests_in_file(test_file)
        python_total += count
        python_by_file[str(test_file)] = count
        
        for marker, marker_count in markers.items():
            python_markers[marker] += marker_count
    
    print(f"Total Python test cases: {python_total}")
    print()
    
    # Find TypeScript test files
    print("Scanning for TypeScript/JavaScript test files...")
    ts_files = find_test_files(project_root, ['*.spec.ts', '*.spec.js', '*.test.ts', '*.test.js'], exclude_dirs)
    print(f"Found {len(ts_files)} TypeScript/JavaScript test files")
    
    # Count TypeScript tests
    ts_total = 0
    for test_file in ts_files:
        count = count_typescript_tests_in_file(test_file)
        ts_total += count
    
    print(f"Total TypeScript/JavaScript test cases: {ts_total}")
    print()
    
    # Print detailed marker breakdown
    print("=" * 80)
    print("PYTHON TEST CASES BY MARKER")
    print("=" * 80)
    for marker, count in sorted(python_markers.items(), key=lambda x: -x[1]):
        print(f"  {marker}: {count}")
    print()
    
    # Summary by test type
    print("=" * 80)
    print("SUMMARY BY TEST TYPE")
    print("=" * 80)
    
    type_summary = defaultdict(int)
    
    # Map markers to types
    type_summary['unit'] = python_markers.get('unit', 0) + python_markers.get('llm_gateway_unit', 0)
    type_summary['integration'] = python_markers.get('integration', 0) + python_markers.get('llm_gateway_integration', 0) + python_markers.get('llm_gateway_real_integration', 0)
    type_summary['e2e'] = python_markers.get('e2e', 0)
    type_summary['performance'] = (python_markers.get('performance', 0) + 
                                   python_markers.get('dgp_performance', 0) + 
                                   python_markers.get('alerting_performance', 0) + 
                                   python_markers.get('budgeting_performance', 0) +
                                   python_markers.get('kms_performance', 0))
    type_summary['security'] = (python_markers.get('security', 0) + 
                                python_markers.get('dgp_security', 0) + 
                                python_markers.get('alerting_security', 0) + 
                                python_markers.get('budgeting_security', 0) +
                                python_markers.get('deployment_security', 0))
    type_summary['smoke'] = python_markers.get('smoke', 0)
    type_summary['compliance'] = python_markers.get('compliance', 0) + python_markers.get('dgp_compliance', 0)
    type_summary['regression'] = (python_markers.get('dgp_regression', 0) + 
                                  python_markers.get('alerting_regression', 0) + 
                                  python_markers.get('budgeting_regression', 0) +
                                  python_markers.get('deployment_regression', 0))
    type_summary['constitution'] = python_markers.get('constitution', 0)
    type_summary['slow'] = python_markers.get('slow', 0)
    type_summary['unmarked'] = python_markers.get('unmarked', 0)
    
    for test_type, count in sorted(type_summary.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"  {test_type.upper()}: {count}")
    
    print()
    print("=" * 80)
    print("FINAL TOTALS")
    print("=" * 80)
    print(f"Python test cases: {python_total}")
    print(f"TypeScript/JavaScript test cases: {ts_total}")
    print(f"GRAND TOTAL: {python_total + ts_total}")
    print()
    print(f"Total test files: {len(python_files) + len(ts_files)}")
    print(f"  Python: {len(python_files)}")
    print(f"  TypeScript/JavaScript: {len(ts_files)}")


if __name__ == '__main__':
    main()
