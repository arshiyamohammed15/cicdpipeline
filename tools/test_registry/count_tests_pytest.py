#!/usr/bin/env python3
"""
Use pytest's collection mechanism to count all test cases accurately.
"""

import subprocess
import sys
import re
from collections import defaultdict
from pathlib import Path


def collect_pytest_tests():
    """Use pytest to collect all tests."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', '--collect-only', '-q'],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=Path(__file__).parent.parent.parent
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"


def parse_pytest_collection(output: str) -> dict:
    """Parse pytest collection output."""
    stats = {
        'total': 0,
        'by_marker': defaultdict(int),
        'by_file': defaultdict(int),
        'test_items': []
    }
    
    # Count test items
    # Pattern: <Module test_file.py>
    # Pattern: <Function test_something>
    # Pattern: <Class TestSomething>
    module_pattern = r'<Module\s+([^>]+)>'
    function_pattern = r'<Function\s+([^>]+)>'
    class_pattern = r'<Class\s+([^>]+)>'
    
    modules = re.findall(module_pattern, output)
    functions = re.findall(function_pattern, output)
    classes = re.findall(class_pattern, output)
    
    stats['total'] = len(functions)
    stats['modules'] = len(modules)
    stats['classes'] = len(classes)
    
    # Extract markers from output
    marker_pattern = r'PytestCollectionWarning|markers|@pytest\.mark\.(\w+)'
    markers = re.findall(marker_pattern, output, re.IGNORECASE)
    
    for marker in markers:
        stats['by_marker'][marker.lower()] += 1
    
    return stats


def count_typescript_tests():
    """Count TypeScript test cases using direct file parsing."""
    project_root = Path(__file__).parent.parent.parent
    exclude_dirs = {'node_modules', '.git', 'dist', 'build', 'artifacts'}
    
    ts_files = []
    for pattern in ['*.spec.ts', '*.spec.js', '*.test.ts', '*.test.js']:
        for path in project_root.rglob(pattern):
            path_str = str(path)
            if any(exclude in path_str for exclude in exclude_dirs):
                continue
            try:
                if path.is_file():
                    ts_files.append(path)
            except (OSError, PermissionError):
                continue
    
    total_tests = 0
    for ts_file in ts_files:
        try:
            content = ts_file.read_text(encoding='utf-8')
            # Count it/test blocks
            it_pattern = r'(?:it|test)\s*\([^,]+,\s*(?:\(\)\s*=>|async\s*\(\)\s*=>|function)'
            matches = re.findall(it_pattern, content, re.MULTILINE)
            total_tests += len(matches)
        except Exception:
            continue
    
    return total_tests, len(ts_files)


def main():
    """Main function."""
    print("=" * 80)
    print("COMPREHENSIVE TEST CASE COUNT - ZEROUI PROJECT")
    print("=" * 80)
    print()
    print("Collecting Python tests using pytest...")
    
    pytest_output = collect_pytest_tests()
    pytest_stats = parse_pytest_collection(pytest_output)
    
    print(f"Python Test Collection Results:")
    print(f"  Total test cases: {pytest_stats['total']}")
    print(f"  Test modules: {pytest_stats['modules']}")
    print(f"  Test classes: {pytest_stats['classes']}")
    print()
    
    # Count by markers using pytest
    print("Collecting tests by marker...")
    markers_to_check = [
        'unit', 'integration', 'e2e', 'performance', 'security', 
        'smoke', 'compliance', 'slow', 'constitution',
        'dgp_regression', 'dgp_security', 'dgp_performance',
        'alerting_regression', 'alerting_security', 'alerting_performance',
        'budgeting_regression', 'budgeting_security', 'budgeting_performance',
        'llm_gateway_unit', 'llm_gateway_integration'
    ]
    
    marker_counts = {}
    for marker in markers_to_check:
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', '--collect-only', '-q', '-m', marker],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=Path(__file__).parent.parent.parent
            )
            # Count test items in output
            count = len(re.findall(r'<Function\s+', result.stdout))
            if count > 0:
                marker_counts[marker] = count
        except Exception:
            continue
    
    print("Python Test Cases by Marker:")
    for marker, count in sorted(marker_counts.items(), key=lambda x: -x[1]):
        print(f"  {marker}: {count}")
    print()
    
    # Count TypeScript tests
    print("Counting TypeScript/JavaScript tests...")
    ts_total, ts_files = count_typescript_tests()
    print(f"TypeScript/JavaScript Test Results:")
    print(f"  Test files: {ts_files}")
    print(f"  Total test cases: {ts_total}")
    print()
    
    # Final summary
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Total Python test cases: {pytest_stats['total']}")
    print(f"Total TypeScript/JavaScript test cases: {ts_total}")
    print(f"GRAND TOTAL: {pytest_stats['total'] + ts_total}")
    print()
    
    print("Summary by Test Type:")
    type_summary = defaultdict(int)
    type_summary['unit'] = marker_counts.get('unit', 0)
    type_summary['integration'] = marker_counts.get('integration', 0) + marker_counts.get('llm_gateway_integration', 0)
    type_summary['performance'] = marker_counts.get('performance', 0) + marker_counts.get('dgp_performance', 0) + marker_counts.get('alerting_performance', 0) + marker_counts.get('budgeting_performance', 0)
    type_summary['security'] = marker_counts.get('security', 0) + marker_counts.get('dgp_security', 0) + marker_counts.get('alerting_security', 0) + marker_counts.get('budgeting_security', 0)
    type_summary['smoke'] = marker_counts.get('smoke', 0)
    type_summary['compliance'] = marker_counts.get('compliance', 0)
    type_summary['constitution'] = marker_counts.get('constitution', 0)
    type_summary['regression'] = marker_counts.get('dgp_regression', 0) + marker_counts.get('alerting_regression', 0) + marker_counts.get('budgeting_regression', 0)
    
    for test_type, count in sorted(type_summary.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"  {test_type.upper()}: {count}")


if __name__ == '__main__':
    main()
