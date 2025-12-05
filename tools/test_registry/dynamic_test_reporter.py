#!/usr/bin/env python3
"""
Dynamic Test Reporter for Constitution Rules

This script generates accurate test coverage reports that dynamically
adapt as rules are added. It provides both pytest-compatible output
and detailed coverage metrics.

Usage:
    python tools/test_registry/dynamic_test_reporter.py
    python tools/test_registry/dynamic_test_reporter.py --json
    python tools/test_registry/dynamic_test_reporter.py --pytest-integration
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Import the counter
import sys
from pathlib import Path
# Add tools/test_registry to path
sys.path.insert(0, str(Path(__file__).parent))
from constitution_test_counter import ConstitutionTestCounter


class DynamicTestReporter:
    """
    Dynamic test reporter that adapts to rule changes automatically.
    """
    
    def __init__(self, project_root: Path = None):
        """Initialize reporter."""
        if project_root is None:
            project_root = Path(__file__).resolve().parents[2]
        self.project_root = Path(project_root)
        self.counter = ConstitutionTestCounter(project_root=self.project_root)
    
    def run_pytest_and_analyze(self) -> Dict[str, Any]:
        """
        Run pytest and analyze results with dynamic rule counting.
        
        Returns:
            Combined report with pytest results and rule analysis
        """
        # Get rule counts (dynamic)
        rule_counts = self.counter.count_rules()
        
        # Run pytest to get test execution results
        pytest_result = self._run_pytest()
        
        # Analyze test files (dynamic)
        test_analysis = self.counter.analyze_all_tests()
        
        # Combine results
        return {
            'timestamp': datetime.now().isoformat(),
            'rules': rule_counts,
            'pytest': pytest_result,
            'tests': test_analysis,
            'coverage': self._calculate_coverage(rule_counts, test_analysis)
        }
    
    def _run_pytest(self) -> Dict[str, Any]:
        """Run pytest and capture results."""
        try:
            result = subprocess.run(
                [
                    sys.executable, '-m', 'pytest',
                    'tests/test_constitution*.py',
                    '--collect-only', '-q'
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=30
            )
            
            # Parse output
            output = result.stdout + result.stderr
            test_count = 0
            
            # Extract test count from output
            for line in output.split('\n'):
                if 'collected' in line.lower():
                    # Try to extract number
                    import re
                    match = re.search(r'(\d+)\s+test', line)
                    if match:
                        test_count = int(match.group(1))
            
            return {
                'test_count': test_count,
                'exit_code': result.returncode,
                'output': output
            }
        except Exception as e:
            return {
                'test_count': 0,
                'exit_code': -1,
                'error': str(e)
            }
    
    def _calculate_coverage(self, rule_counts: Dict, test_analysis: Dict) -> Dict[str, Any]:
        """Calculate coverage metrics."""
        total_rules = rule_counts.get('total', 0)
        estimated_validations = test_analysis.get('total_rule_validations', 0)
        pytest_count = test_analysis.get('total_test_functions', 0)
        
        coverage_percentage = 0.0
        if total_rules > 0:
            actual_coverage = min(estimated_validations, total_rules)
            coverage_percentage = (actual_coverage / total_rules) * 100
        
        return {
            'total_rules': total_rules,
            'pytest_test_count': pytest_count,
            'estimated_rule_validations': estimated_validations,
            'coverage_percentage': coverage_percentage,
            'discrepancy': {
                'rules_vs_pytest': total_rules - pytest_count,
                'reason': 'Pytest counts test functions, not subTest iterations'
            }
        }
    
    def generate_report(self, format: str = 'text') -> str:
        """
        Generate test coverage report.
        
        Args:
            format: 'text', 'json', or 'markdown'
            
        Returns:
            Report as string
        """
        report_data = self.run_pytest_and_analyze()
        
        if format == 'json':
            return json.dumps(report_data, indent=2)
        elif format == 'markdown':
            return self._format_markdown(report_data)
        else:
            return self._format_text(report_data)
    
    def _format_text(self, report: Dict[str, Any]) -> str:
        """Format report as text."""
        lines = []
        lines.append("=" * 70)
        lines.append("DYNAMIC CONSTITUTION TEST COVERAGE REPORT")
        lines.append("=" * 70)
        lines.append(f"Generated: {report['timestamp']}")
        lines.append("")
        
        # Rules section
        rules = report['rules']
        lines.append("📊 RULES (Dynamically Counted from JSON Files)")
        lines.append(f"  Total: {rules['total']}")
        lines.append(f"  Enabled: {rules['enabled']}")
        lines.append(f"  Disabled: {rules['disabled']}")
        lines.append("")
        lines.append("  By File:")
        for filename, count in sorted(rules['by_file'].items()):
            lines.append(f"    {filename}: {count} rules")
        lines.append("")
        
        # Tests section
        tests = report['tests']
        lines.append("🧪 TESTS (Dynamically Analyzed)")
        lines.append(f"  Test Functions: {tests['total_test_functions']}")
        lines.append(f"  Estimated subTest Iterations: {tests['total_subtest_iterations']}")
        lines.append(f"  Estimated Rule Validations: {tests['total_rule_validations']}")
        lines.append("")
        
        # Coverage section
        coverage = report['coverage']
        lines.append("📈 COVERAGE METRICS")
        lines.append(f"  Total Rules: {coverage['total_rules']}")
        lines.append(f"  Pytest Reports: {coverage['pytest_test_count']} tests")
        lines.append(f"  Estimated Validations: {coverage['estimated_rule_validations']}")
        lines.append(f"  Coverage: {coverage['coverage_percentage']:.1f}%")
        lines.append("")
        lines.append("  ⚠️  Note: Pytest counts test functions, not subTest iterations")
        lines.append(f"  📊 Discrepancy: {coverage['discrepancy']['rules_vs_pytest']} rules")
        lines.append(f"     Reason: {coverage['discrepancy']['reason']}")
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def _format_markdown(self, report: Dict[str, Any]) -> str:
        """Format report as markdown."""
        lines = []
        lines.append("# Dynamic Constitution Test Coverage Report")
        lines.append("")
        lines.append(f"**Generated**: {report['timestamp']}")
        lines.append("")
        
        # Rules section
        rules = report['rules']
        lines.append("## Rules (Dynamically Counted)")
        lines.append("")
        lines.append(f"- **Total**: {rules['total']}")
        lines.append(f"- **Enabled**: {rules['enabled']}")
        lines.append(f"- **Disabled**: {rules['disabled']}")
        lines.append("")
        lines.append("### By File")
        lines.append("")
        for filename, count in sorted(rules['by_file'].items()):
            lines.append(f"- `{filename}`: {count} rules")
        lines.append("")
        
        # Coverage section
        coverage = report['coverage']
        lines.append("## Coverage Metrics")
        lines.append("")
        lines.append(f"- **Total Rules**: {coverage['total_rules']}")
        lines.append(f"- **Pytest Test Count**: {coverage['pytest_test_count']}")
        lines.append(f"- **Estimated Validations**: {coverage['estimated_rule_validations']}")
        lines.append(f"- **Coverage**: {coverage['coverage_percentage']:.1f}%")
        lines.append("")
        lines.append("> **Note**: Pytest counts test functions, not subTest iterations")
        lines.append("")
        
        return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Dynamic Test Reporter for Constitution Rules'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'markdown'],
        default='text',
        help='Output format'
    )
    parser.add_argument(
        '--project-root',
        type=str,
        default=None,
        help='Project root directory'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file (default: stdout)'
    )
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root) if args.project_root else None
    reporter = DynamicTestReporter(project_root=project_root)
    
    report = reporter.generate_report(format=args.format)
    
    if args.output:
        Path(args.output).write_text(report, encoding='utf-8')
        print(f"Report saved to: {args.output}")
    else:
        # Handle Unicode encoding for Windows console
        import sys
        if sys.platform == 'win32':
            sys.stdout.reconfigure(encoding='utf-8')
        print(report)


if __name__ == '__main__':
    main()

