"""
Test Coverage Reporter for Dynamic Test Discovery System

This module provides comprehensive coverage analysis and reporting for the
dynamic test discovery system, ensuring 100% rule coverage and identifying gaps.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Set
from dataclasses import dataclass
from datetime import datetime

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.dynamic_test_factory import DynamicTestFactory, TestCase


@dataclass
class CoverageStats:
    """Statistics for test coverage analysis."""
    total_rules: int
    tested_rules: int
    untested_rules: int
    coverage_percentage: float
    categories: Dict[str, int]
    severities: Dict[str, int]
    validators: Dict[str, int]
    constitutions: Dict[str, int]


@dataclass
class CoverageReport:
    """Comprehensive coverage report."""
    stats: CoverageStats
    tested_rules: List[str]
    untested_rules: List[str]
    category_breakdown: Dict[str, Dict[str, Any]]
    validator_breakdown: Dict[str, Dict[str, Any]]
    constitution_breakdown: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    generated_at: str


class TestCoverageReporter:
    """
    Reporter for analyzing and reporting test coverage of the dynamic test system.
    """

    def __init__(self, rules_file: str = "tools/validator/rules.json"):
        """Initialize the coverage reporter."""
        self.rules_file = Path(rules_file)
        self.test_factory = DynamicTestFactory(rules_file)
        self.all_rules = self.test_factory.get_all_rules()

    def analyze_coverage(self, test_cases: List[TestCase] = None) -> CoverageReport:
        """
        Analyze test coverage and generate a comprehensive report.

        Args:
            test_cases: Optional list of test cases to analyze. If None, generates all test cases.

        Returns:
            CoverageReport object with detailed analysis
        """
        if test_cases is None:
            test_cases = self.test_factory.create_test_cases()

        # Get tested and untested rules
        tested_rule_ids = {tc.rule_id for tc in test_cases}
        all_rule_ids = {rule['id'] for rule in self.all_rules}
        untested_rule_ids = all_rule_ids - tested_rule_ids

        # Calculate statistics
        stats = self._calculate_stats(tested_rule_ids, untested_rule_ids)

        # Generate breakdowns
        category_breakdown = self._analyze_category_coverage(tested_rule_ids, untested_rule_ids)
        validator_breakdown = self._analyze_validator_coverage(tested_rule_ids, untested_rule_ids)
        constitution_breakdown = self._analyze_constitution_coverage(tested_rule_ids, untested_rule_ids)

        # Generate recommendations
        recommendations = self._generate_recommendations(stats, untested_rule_ids, category_breakdown, validator_breakdown, constitution_breakdown)

        return CoverageReport(
            stats=stats,
            tested_rules=sorted(list(tested_rule_ids)),
            untested_rules=sorted(list(untested_rule_ids)),
            category_breakdown=category_breakdown,
            validator_breakdown=validator_breakdown,
            constitution_breakdown=constitution_breakdown,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat()
        )

    def _calculate_stats(self, tested_rule_ids: Set[str], untested_rule_ids: Set[str]) -> CoverageStats:
        """Calculate coverage statistics."""
        total_rules = len(self.all_rules)
        tested_rules = len(tested_rule_ids)
        untested_rules = len(untested_rule_ids)
        coverage_percentage = (tested_rules / total_rules * 100) if total_rules > 0 else 0

        # Count by category
        categories = {}
        for rule in self.all_rules:
            category = rule.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1

        # Count by severity
        severities = {}
        for rule in self.all_rules:
            severity = rule.get('severity', 'unknown')
            severities[severity] = severities.get(severity, 0) + 1

        # Count by validator
        validators = {}
        for rule in self.all_rules:
            validator = rule.get('validator', '').split('.')[0] if rule.get('validator') else 'unknown'
            validators[validator] = validators.get(validator, 0) + 1

        # Count by constitution
        constitutions = {}
        for rule in self.all_rules:
            constitution = rule.get('constitution', 'unknown')
            constitutions[constitution] = constitutions.get(constitution, 0) + 1

        return CoverageStats(
            total_rules=total_rules,
            tested_rules=tested_rules,
            untested_rules=untested_rules,
            coverage_percentage=coverage_percentage,
            categories=categories,
            severities=severities,
            validators=validators,
            constitutions=constitutions
        )

    def _analyze_category_coverage(self, tested_rule_ids: Set[str], untested_rule_ids: Set[str]) -> Dict[str, Dict[str, Any]]:
        """Analyze coverage by category."""
        breakdown = {}

        for rule in self.all_rules:
            category = rule.get('category', 'unknown')
            rule_id = rule['id']

            if category not in breakdown:
                breakdown[category] = {
                    'total_rules': 0,
                    'tested_rules': 0,
                    'untested_rules': 0,
                    'coverage_percentage': 0,
                    'tested_rule_ids': [],
                    'untested_rule_ids': []
                }

            breakdown[category]['total_rules'] += 1

            if rule_id in tested_rule_ids:
                breakdown[category]['tested_rules'] += 1
                breakdown[category]['tested_rule_ids'].append(rule_id)
            else:
                breakdown[category]['untested_rules'] += 1
                breakdown[category]['untested_rule_ids'].append(rule_id)

        # Calculate coverage percentages
        for category_data in breakdown.values():
            if category_data['total_rules'] > 0:
                category_data['coverage_percentage'] = (category_data['tested_rules'] / category_data['total_rules'] * 100)

        return breakdown

    def _analyze_validator_coverage(self, tested_rule_ids: Set[str], untested_rule_ids: Set[str]) -> Dict[str, Dict[str, Any]]:
        """Analyze coverage by validator."""
        breakdown = {}

        for rule in self.all_rules:
            validator = rule.get('validator', '').split('.')[0] if rule.get('validator') else 'unknown'
            rule_id = rule['id']

            if validator not in breakdown:
                breakdown[validator] = {
                    'total_rules': 0,
                    'tested_rules': 0,
                    'untested_rules': 0,
                    'coverage_percentage': 0,
                    'tested_rule_ids': [],
                    'untested_rule_ids': []
                }

            breakdown[validator]['total_rules'] += 1

            if rule_id in tested_rule_ids:
                breakdown[validator]['tested_rules'] += 1
                breakdown[validator]['tested_rule_ids'].append(rule_id)
            else:
                breakdown[validator]['untested_rules'] += 1
                breakdown[validator]['untested_rule_ids'].append(rule_id)

        # Calculate coverage percentages
        for validator_data in breakdown.values():
            if validator_data['total_rules'] > 0:
                validator_data['coverage_percentage'] = (validator_data['tested_rules'] / validator_data['total_rules'] * 100)

        return breakdown

    def _analyze_constitution_coverage(self, tested_rule_ids: Set[str], untested_rule_ids: Set[str]) -> Dict[str, Dict[str, Any]]:
        """Analyze coverage by constitution."""
        breakdown = {}

        for rule in self.all_rules:
            constitution = rule.get('constitution', 'unknown')
            rule_id = rule['id']

            if constitution not in breakdown:
                breakdown[constitution] = {
                    'total_rules': 0,
                    'tested_rules': 0,
                    'untested_rules': 0,
                    'coverage_percentage': 0,
                    'tested_rule_ids': [],
                    'untested_rule_ids': []
                }

            breakdown[constitution]['total_rules'] += 1

            if rule_id in tested_rule_ids:
                breakdown[constitution]['tested_rules'] += 1
                breakdown[constitution]['tested_rule_ids'].append(rule_id)
            else:
                breakdown[constitution]['untested_rules'] += 1
                breakdown[constitution]['untested_rule_ids'].append(rule_id)

        # Calculate coverage percentages
        for constitution_data in breakdown.values():
            if constitution_data['total_rules'] > 0:
                constitution_data['coverage_percentage'] = (constitution_data['tested_rules'] / constitution_data['total_rules'] * 100)

        return breakdown

    def _generate_recommendations(self, stats: CoverageStats, untested_rule_ids: Set[str],
                                category_breakdown: Dict[str, Dict[str, Any]],
                                validator_breakdown: Dict[str, Dict[str, Any]],
                                constitution_breakdown: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on coverage analysis."""
        recommendations = []

        # Overall coverage recommendations
        if stats.coverage_percentage < 100:
            recommendations.append(f"Coverage is {stats.coverage_percentage:.1f}%. Aim for 100% coverage.")
            recommendations.append(f"Add tests for {len(untested_rule_ids)} untested rules: {', '.join(sorted(untested_rule_ids))}")

        # Category-specific recommendations
        for category, data in category_breakdown.items():
            if data['coverage_percentage'] < 100:
                recommendations.append(f"Category '{category}' has {data['coverage_percentage']:.1f}% coverage. Add tests for: {', '.join(data['untested_rule_ids'])}")

        # Validator-specific recommendations
        for validator, data in validator_breakdown.items():
            if data['coverage_percentage'] < 100:
                recommendations.append(f"Validator '{validator}' has {data['coverage_percentage']:.1f}% coverage. Add tests for: {', '.join(data['untested_rule_ids'])}")

        # Constitution-specific recommendations
        for constitution, data in constitution_breakdown.items():
            if data['coverage_percentage'] < 100:
                recommendations.append(f"Constitution '{constitution}' has {data['coverage_percentage']:.1f}% coverage. Add tests for: {', '.join(data['untested_rule_ids'])}")

        # Performance recommendations
        if stats.coverage_percentage == 100:
            recommendations.append("Excellent! 100% rule coverage achieved.")
            recommendations.append("Consider adding integration tests and performance tests.")
            recommendations.append("Consider adding edge case tests for complex rules.")

        return recommendations

    def generate_json_report(self, report: CoverageReport, output_file: str = "test_coverage_report.json") -> str:
        """Generate JSON coverage report."""
        output_path = Path(output_file)

        report_data = {
            'summary': {
                'total_rules': report.stats.total_rules,
                'tested_rules': report.stats.tested_rules,
                'untested_rules': report.stats.untested_rules,
                'coverage_percentage': report.stats.coverage_percentage,
                'generated_at': report.generated_at
            },
            'categories': report.category_breakdown,
            'validators': report.validator_breakdown,
            'constitutions': report.constitution_breakdown,
            'tested_rules': report.tested_rules,
            'untested_rules': report.untested_rules,
            'recommendations': report.recommendations
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        return str(output_path)

    def generate_markdown_report(self, report: CoverageReport, output_file: str = "test_coverage_report.md") -> str:
        """Generate Markdown coverage report."""
        output_path = Path(output_file)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Test Coverage Report\n\n")
            f.write(f"Generated at: {report.generated_at}\n\n")

            # Summary
            f.write(f"## Summary\n\n")
            f.write(f"- **Total Rules**: {report.stats.total_rules}\n")
            f.write(f"- **Tested Rules**: {report.stats.tested_rules}\n")
            f.write(f"- **Untested Rules**: {report.stats.untested_rules}\n")
            f.write(f"- **Coverage**: {report.stats.coverage_percentage:.1f}%\n\n")

            # Coverage by category
            f.write(f"## Coverage by Category\n\n")
            f.write(f"| Category | Total | Tested | Untested | Coverage |\n")
            f.write(f"|----------|-------|--------|----------|----------|\n")
            for category, data in report.category_breakdown.items():
                f.write(f"| {category} | {data['total_rules']} | {data['tested_rules']} | {data['untested_rules']} | {data['coverage_percentage']:.1f}% |\n")
            f.write(f"\n")

            # Coverage by validator
            f.write(f"## Coverage by Validator\n\n")
            f.write(f"| Validator | Total | Tested | Untested | Coverage |\n")
            f.write(f"|-----------|-------|--------|----------|----------|\n")
            for validator, data in report.validator_breakdown.items():
                f.write(f"| {validator} | {data['total_rules']} | {data['tested_rules']} | {data['untested_rules']} | {data['coverage_percentage']:.1f}% |\n")
            f.write(f"\n")

            # Coverage by constitution
            f.write(f"## Coverage by Constitution\n\n")
            f.write(f"| Constitution | Total | Tested | Untested | Coverage |\n")
            f.write(f"|--------------|-------|--------|----------|----------|\n")
            for constitution, data in report.constitution_breakdown.items():
                f.write(f"| {constitution} | {data['total_rules']} | {data['tested_rules']} | {data['untested_rules']} | {data['coverage_percentage']:.1f}% |\n")
            f.write(f"\n")

            # Untested rules
            if report.untested_rules:
                f.write(f"## Untested Rules\n\n")
                for rule_id in report.untested_rules:
                    rule = next((r for r in self.all_rules if r['id'] == rule_id), None)
                    if rule:
                        f.write(f"- **{rule_id}**: {rule.get('name', 'Unknown')} ({rule.get('category', 'unknown')})\n")
                f.write(f"\n")

            # Recommendations
            f.write(f"## Recommendations\n\n")
            for i, recommendation in enumerate(report.recommendations, 1):
                f.write(f"{i}. {recommendation}\n")
            f.write(f"\n")

        return str(output_path)

    def generate_html_report(self, report: CoverageReport, output_file: str = "test_coverage_report.html") -> str:
        """Generate HTML coverage report."""
        output_path = Path(output_file)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Coverage Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .summary {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .coverage-100 {{ color: green; font-weight: bold; }}
        .coverage-warning {{ color: orange; font-weight: bold; }}
        .coverage-error {{ color: red; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .recommendations {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Test Coverage Report</h1>
    <p>Generated at: {report.generated_at}</p>

    <div class="summary">
        <h2>Summary</h2>
        <ul>
            <li><strong>Total Rules</strong>: {report.stats.total_rules}</li>
            <li><strong>Tested Rules</strong>: {report.stats.tested_rules}</li>
            <li><strong>Untested Rules</strong>: {report.stats.untested_rules}</li>
            <li><strong>Coverage</strong>: <span class="{'coverage-100' if report.stats.coverage_percentage == 100 else 'coverage-warning' if report.stats.coverage_percentage >= 90 else 'coverage-error'}">{report.stats.coverage_percentage:.1f}%</span></li>
        </ul>
    </div>

    <h2>Coverage by Category</h2>
    <table>
        <tr><th>Category</th><th>Total</th><th>Tested</th><th>Untested</th><th>Coverage</th></tr>""")

            for category, data in report.category_breakdown.items():
                coverage_class = 'coverage-100' if data['coverage_percentage'] == 100 else 'coverage-warning' if data['coverage_percentage'] >= 90 else 'coverage-error'
                f.write(f"<tr><td>{category}</td><td>{data['total_rules']}</td><td>{data['tested_rules']}</td><td>{data['untested_rules']}</td><td class='{coverage_class}'>{data['coverage_percentage']:.1f}%</td></tr>")

            f.write(f"""
    </table>

    <h2>Coverage by Validator</h2>
    <table>
        <tr><th>Validator</th><th>Total</th><th>Tested</th><th>Untested</th><th>Coverage</th></tr>""")

            for validator, data in report.validator_breakdown.items():
                coverage_class = 'coverage-100' if data['coverage_percentage'] == 100 else 'coverage-warning' if data['coverage_percentage'] >= 90 else 'coverage-error'
                f.write(f"<tr><td>{validator}</td><td>{data['total_rules']}</td><td>{data['tested_rules']}</td><td>{data['untested_rules']}</td><td class='{coverage_class}'>{data['coverage_percentage']:.1f}%</td></tr>")

            f.write(f"""
    </table>

    <h2>Coverage by Constitution</h2>
    <table>
        <tr><th>Constitution</th><th>Total</th><th>Tested</th><th>Untested</th><th>Coverage</th></tr>""")

            for constitution, data in report.constitution_breakdown.items():
                coverage_class = 'coverage-100' if data['coverage_percentage'] == 100 else 'coverage-warning' if data['coverage_percentage'] >= 90 else 'coverage-error'
                f.write(f"<tr><td>{constitution}</td><td>{data['total_rules']}</td><td>{data['tested_rules']}</td><td>{data['untested_rules']}</td><td class='{coverage_class}'>{data['coverage_percentage']:.1f}%</td></tr>")

            f.write(f"""
    </table>""")

            if report.untested_rules:
                f.write(f"""
    <h2>Untested Rules</h2>
    <ul>""")
                for rule_id in report.untested_rules:
                    rule = next((r for r in self.all_rules if r['id'] == rule_id), None)
                    if rule:
                        f.write(f"<li><strong>{rule_id}</strong>: {rule.get('name', 'Unknown')} ({rule.get('category', 'unknown')})</li>")
                f.write(f"""
    </ul>""")

            f.write(f"""
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ol>""")
            for recommendation in report.recommendations:
                f.write(f"<li>{recommendation}</li>")
            f.write(f"""
        </ol>
    </div>
</body>
</html>""")

        return str(output_path)

    def print_summary(self, report: CoverageReport) -> None:
        """Print a summary of the coverage report to console."""
        print(f"\n{'='*60}")
        print(f"TEST COVERAGE REPORT")
        print(f"{'='*60}")
        print(f"Generated at: {report.generated_at}")
        print(f"Total Rules: {report.stats.total_rules}")
        print(f"Tested Rules: {report.stats.tested_rules}")
        print(f"Untested Rules: {report.stats.untested_rules}")
        print(f"Coverage: {report.stats.coverage_percentage:.1f}%")

        if report.stats.coverage_percentage == 100:
            print(f"\n🎉 EXCELLENT! 100% rule coverage achieved!")
        elif report.stats.coverage_percentage >= 90:
            print(f"\n⚠️  Good coverage, but aim for 100%")
        else:
            print(f"\n❌ Coverage needs improvement")

        if report.untested_rules:
            print(f"\nUntested Rules:")
            for rule_id in report.untested_rules:
                rule = next((r for r in self.all_rules if r['id'] == rule_id), None)
                if rule:
                    print(f"  - {rule_id}: {rule.get('name', 'Unknown')}")

        print(f"\nRecommendations:")
        for i, recommendation in enumerate(report.recommendations, 1):
            print(f"  {i}. {recommendation}")

        print(f"\n{'='*60}")


# Global reporter instance
coverage_reporter = TestCoverageReporter()


def get_coverage_reporter() -> TestCoverageReporter:
    """Get the global coverage reporter instance."""
    return coverage_reporter


if __name__ == "__main__":
    # Example usage
    reporter = TestCoverageReporter()

    # Analyze coverage
    print("Analyzing test coverage...")
    report = reporter.analyze_coverage()

    # Print summary
    reporter.print_summary(report)

    # Generate reports
    json_file = reporter.generate_json_report(report)
    md_file = reporter.generate_markdown_report(report)
    html_file = reporter.generate_html_report(report)

    print(f"\nReports generated:")
    print(f"  - JSON: {json_file}")
    print(f"  - Markdown: {md_file}")
    print(f"  - HTML: {html_file}")
