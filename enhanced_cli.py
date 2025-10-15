#!/usr/bin/env python3
"""
Enhanced CLI for ZeroUI2.0 Constitution Validator.

This CLI provides advanced features including:
- Intelligent rule selection
- Performance monitoring
- Context-aware validation
- Detailed reporting
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import enhanced components
from validator.optimized_core import OptimizedConstitutionValidator
from validator.intelligent_selector import IntelligentRuleSelector
from validator.performance_monitor import PerformanceMonitor
from config.enhanced_config_manager import EnhancedConfigManager


class EnhancedCLI:
    """
    Enhanced CLI with intelligent features and performance monitoring.
    """
    
    def __init__(self):
        """Initialize the enhanced CLI."""
        self.config_manager = EnhancedConfigManager()
        self.validator = OptimizedConstitutionValidator()
        self.rule_selector = IntelligentRuleSelector(self.config_manager)
        self.performance_monitor = PerformanceMonitor()
        
        # Start performance monitoring
        self.performance_monitor.start_monitoring()
    
    def validate_file(self, file_path: str, args) -> Dict[str, Any]:
        """
        Validate a single file with intelligent rule selection.
        
        Args:
            file_path: Path to the file to validate
            args: Command line arguments
            
        Returns:
            Validation results
        """
        try:
            # Read file content for context analysis
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_size = len(content.encode('utf-8'))
            line_count = len(content.split('\n'))
            
            # Analyze file context
            context = self.rule_selector.analyze_file_context(file_path, content)
            
            # Get validation strategy
            strategy = self.rule_selector.get_validation_strategy(context)
            
            # Profile the validation
            with self.performance_monitor.profile_validation(file_path, file_size, line_count) as profile:
                # Validate the file
                result = self.validator.validate_file(file_path)
                
                # Update profile with results
                profile.violations_found = result.total_violations
                profile.rules_processed = len(self.config_manager.get_all_categories())
                profile.ast_parsing_time = result.processing_time * 0.3  # Estimate
                profile.rule_processing_time = result.processing_time * 0.7  # Estimate
            
            # Record performance metrics
            self.performance_monitor.record_metric(
                "validation_duration",
                result.processing_time,
                "seconds",
                {"file_path": file_path, "file_type": context.file_type.value}
            )
            
            self.performance_monitor.record_metric(
                "violations_found",
                result.total_violations,
                "count",
                {"file_path": file_path, "severity": "total"}
            )
            
            return {
                "result": result,
                "context": context,
                "strategy": strategy,
                "performance": {
                    "duration": result.processing_time,
                    "compliance_score": result.compliance_score
                }
            }
        
        except Exception as e:
            print(f"Error validating {file_path}: {e}")
            return {"error": str(e)}
    
    def validate_directory(self, directory_path: str, args) -> Dict[str, Any]:
        """
        Validate a directory with intelligent rule selection.
        
        Args:
            directory_path: Path to the directory to validate
            args: Command line arguments
            
        Returns:
            Validation results
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Find Python files
        pattern = "**/*.py" if args.recursive else "*.py"
        python_files = list(directory.glob(pattern))
        
        if not python_files:
            print(f"No Python files found in {directory_path}")
            return {"files": [], "summary": {}}
        
        print(f"Validating {len(python_files)} Python files...")
        
        results = {}
        total_violations = 0
        total_files = 0
        
        for file_path in python_files:
            try:
                file_result = self.validate_file(str(file_path), args)
                if "result" in file_result:
                    results[str(file_path)] = file_result
                    total_violations += file_result["result"].total_violations
                    total_files += 1
                    
                    # Print progress
                    compliance = file_result["result"].compliance_score
                    print(f"[{compliance:5.1f}%] {file_path.name}: {file_result['result'].total_violations} violations")
            
            except Exception as e:
                print(f"[ERROR] {file_path}: {e}")
        
        # Generate summary
        summary = {
            "total_files": total_files,
            "total_violations": total_violations,
            "average_compliance": sum(r["result"].compliance_score for r in results.values()) / len(results) if results else 0,
            "performance_summary": self.performance_monitor.get_performance_summary()
        }
        
        return {
            "files": results,
            "summary": summary
        }
    
    def generate_enhanced_report(self, results: Dict[str, Any], 
                               output_format: str = "console") -> str:
        """
        Generate an enhanced report with context and performance information.
        
        Args:
            results: Validation results
            output_format: Report format
            
        Returns:
            Generated report
        """
        if output_format == "console":
            return self._generate_console_report(results)
        elif output_format == "json":
            return self._generate_json_report(results)
        elif output_format == "html":
            return self._generate_html_report(results)
        else:
            return self._generate_markdown_report(results)
    
    def _generate_console_report(self, results: Dict[str, Any]) -> str:
        """Generate console report."""
        report = []
        report.append("=" * 80)
        report.append("ZEROUI 2.0 CONSTITUTION VALIDATION REPORT (ENHANCED)")
        report.append("=" * 80)
        report.append("")
        
        if "summary" in results:
            summary = results["summary"]
            report.append("SUMMARY:")
            report.append(f"  Total Files: {summary.get('total_files', 0)}")
            report.append(f"  Total Violations: {summary.get('total_violations', 0)}")
            report.append(f"  Average Compliance: {summary.get('average_compliance', 0):.1f}%")
            report.append("")
        
        # Performance summary
        if "summary" in results and "performance_summary" in results["summary"]:
            perf_summary = results["summary"]["performance_summary"]
            report.append("PERFORMANCE SUMMARY:")
            report.append(f"  Total Validations: {perf_summary.get('total_validations', 0)}")
            report.append(f"  Cache Hit Rate: {perf_summary.get('recent_performance', {}).get('cache_hit_rate', 0):.1%}")
            report.append(f"  Files/Second: {perf_summary.get('recent_performance', {}).get('files_per_second', 0):.2f}")
            report.append("")
        
        # File results
        if "files" in results:
            report.append("FILE RESULTS:")
            for file_path, file_result in results["files"].items():
                if "result" in file_result:
                    result = file_result["result"]
                    context = file_result.get("context", {})
                    strategy = file_result.get("strategy", {})
                    
                    report.append(f"  {Path(file_path).name}:")
                    report.append(f"    Compliance: {result.compliance_score:.1f}%")
                    report.append(f"    Violations: {result.total_violations}")
                    report.append(f"    File Type: {context.file_type.value}")
                    report.append(f"    Project Type: {context.project_type.value}")
                    report.append(f"    Processing Time: {result.processing_time:.3f}s")
                    report.append("")
        
        # Performance recommendations
        recommendations = self.performance_monitor.get_performance_recommendations()
        if recommendations:
            report.append("PERFORMANCE RECOMMENDATIONS:")
            for rec in recommendations:
                report.append(f"  • {rec}")
            report.append("")
        
        return "\n".join(report)
    
    def _generate_json_report(self, results: Dict[str, Any]) -> str:
        """Generate JSON report."""
        import json
        
        # Add performance data to results
        enhanced_results = results.copy()
        enhanced_results["performance_metrics"] = self.performance_monitor.get_performance_summary()
        enhanced_results["recommendations"] = self.performance_monitor.get_performance_recommendations()
        
        return json.dumps(enhanced_results, indent=2, default=str)
    
    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML report."""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html><head><title>ZEROUI 2.0 Validation Report</title></head><body>")
        html.append("<h1>ZEROUI 2.0 CONSTITUTION VALIDATION REPORT</h1>")
        
        if "summary" in results:
            summary = results["summary"]
            html.append("<h2>Summary</h2>")
            html.append(f"<p>Total Files: {summary.get('total_files', 0)}</p>")
            html.append(f"<p>Total Violations: {summary.get('total_violations', 0)}</p>")
            html.append(f"<p>Average Compliance: {summary.get('average_compliance', 0):.1f}%</p>")
        
        html.append("</body></html>")
        return "\n".join(html)
    
    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate Markdown report."""
        md = []
        md.append("# ZEROUI 2.0 Constitution Validation Report")
        md.append("")
        
        if "summary" in results:
            summary = results["summary"]
            md.append("## Summary")
            md.append("")
            md.append(f"- **Total Files**: {summary.get('total_files', 0)}")
            md.append(f"- **Total Violations**: {summary.get('total_violations', 0)}")
            md.append(f"- **Average Compliance**: {summary.get('average_compliance', 0):.1f}%")
            md.append("")
        
        return "\n".join(md)
    
    def run(self, args):
        """Run the CLI with given arguments."""
        try:
            if args.file:
                # Validate single file
                result = self.validate_file(args.file, args)
                if "error" not in result:
                    report = self.generate_enhanced_report({"files": {args.file: result}}, args.format)
                    print(report)
                else:
                    print(f"Error: {result['error']}")
                    return 1
            
            elif args.directory:
                # Validate directory
                results = self.validate_directory(args.directory, args)
                report = self.generate_enhanced_report(results, args.format)
                print(report)
                
                # Save report if requested
                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(report)
                    print(f"Report saved to {args.output}")
            
            else:
                print("Please specify either --file or --directory")
                return 1
            
            return 0
        
        except KeyboardInterrupt:
            print("\nValidation interrupted by user")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1
        finally:
            # Stop performance monitoring
            self.performance_monitor.stop_monitoring()


def main():
    """Main entry point for the enhanced CLI."""
    parser = argparse.ArgumentParser(
        description="Enhanced ZEROUI 2.0 Constitution Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --file script.py
  %(prog)s --directory src/ --recursive
  %(prog)s --directory src/ --format html --output report.html
  %(prog)s --file script.py --format json
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--file", "-f",
        help="Validate a single Python file"
    )
    input_group.add_argument(
        "--directory", "-d",
        help="Validate all Python files in a directory"
    )
    
    # Output options
    parser.add_argument(
        "--format", "-fmt",
        choices=["console", "json", "html", "markdown"],
        default="console",
        help="Output format for the report"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for the report"
    )
    
    # Processing options
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Search directories recursively"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    # Performance options
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Show detailed performance metrics"
    )
    
    args = parser.parse_args()
    
    # Create and run CLI
    cli = EnhancedCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
