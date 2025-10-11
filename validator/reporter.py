"""
Report generator for validation results.

This module provides various output formats for validation reports,
including console, JSON, HTML, and Markdown formats.
"""

import json
import html
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

from .models import ValidationResult, Violation, Severity


class ReportGenerator:
    """
    Generates validation reports in various formats.
    
    This class provides multiple output formats for validation results,
    making it easy to integrate with different tools and workflows.
    """
    
    def __init__(self):
        """Initialize the report generator."""
        self.severity_colors = {
            Severity.ERROR: "\033[91m",    # Red
            Severity.WARNING: "\033[93m",  # Yellow
            Severity.INFO: "\033[94m",     # Blue
        }
        self.reset_color = "\033[0m"
    
    def generate_report(self, results: Dict[str, ValidationResult], 
                       output_format: str = "console", 
                       config: Dict[str, Any] = None) -> str:
        """
        Generate a validation report in the specified format.
        
        Args:
            results: Dictionary of validation results
            output_format: Format of the report ("console", "json", "html", "markdown")
            config: Configuration dictionary
            
        Returns:
            Generated report as string
        """
        if output_format == "console":
            return self._generate_console_report(results)
        elif output_format == "json":
            return self._generate_json_report(results)
        elif output_format == "html":
            return self._generate_html_report(results, config)
        elif output_format == "markdown":
            return self._generate_markdown_report(results, config)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_console_report(self, results: Dict[str, ValidationResult]) -> str:
        """Generate a console-friendly report."""
        if not results:
            return "No files to validate."
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("ZEROUI 2.0 CONSTITUTION VALIDATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Files analyzed: {len(results)}")
        report_lines.append("")
        
        # Summary statistics
        total_violations = sum(result.total_violations for result in results.values())
        total_errors = sum(result.violations_by_severity.get(Severity.ERROR, 0) 
                          for result in results.values())
        total_warnings = sum(result.violations_by_severity.get(Severity.WARNING, 0) 
                            for result in results.values())
        total_info = sum(result.violations_by_severity.get(Severity.INFO, 0) 
                        for result in results.values())
        
        avg_compliance = sum(result.compliance_score for result in results.values()) / len(results)
        
        report_lines.append("SUMMARY:")
        report_lines.append(f"  Total violations: {total_violations}")
        report_lines.append(f"  Errors: {total_errors}")
        report_lines.append(f"  Warnings: {total_warnings}")
        report_lines.append(f"  Info: {total_info}")
        report_lines.append(f"  Average compliance: {avg_compliance:.1f}%")
        report_lines.append("")
        
        # File-by-file results
        for file_path, result in results.items():
            file_name = Path(file_path).name
            report_lines.append(f"FILE: {file_name}")
            report_lines.append(f"  Compliance: {result.compliance_score}%")
            report_lines.append(f"  Violations: {result.total_violations}")
            report_lines.append(f"  Processing time: {result.processing_time:.3f}s")
            
            if result.violations:
                report_lines.append("  VIOLATIONS:")
                for violation in result.violations:
                    color = self.severity_colors.get(violation.severity, "")
                    reset = self.reset_color
                    
                    report_lines.append(f"    {color}[{violation.severity.value.upper()}]{reset} "
                                      f"Rule {violation.rule_number}: {violation.rule_name}")
                    report_lines.append(f"      Line {violation.line_number}: {violation.message}")
                    if violation.fix_suggestion:
                        report_lines.append(f"      Fix: {violation.fix_suggestion}")
                    report_lines.append("")
            else:
                report_lines.append("  [OK] No violations found")
            
            report_lines.append("-" * 40)
        
        return "\n".join(report_lines)
    
    def _generate_json_report(self, results: Dict[str, ValidationResult]) -> str:
        """Generate a JSON report."""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(results),
            "summary": self._calculate_summary(results),
            "files": {}
        }
        
        for file_path, result in results.items():
            report_data["files"][file_path] = {
                "compliance_score": result.compliance_score,
                "total_violations": result.total_violations,
                "processing_time": result.processing_time,
                "violations_by_severity": {
                    severity.value: count 
                    for severity, count in result.violations_by_severity.items()
                },
                "violations": [
                    {
                        "rule_number": violation.rule_number,
                        "rule_name": violation.rule_name,
                        "severity": violation.severity.value,
                        "message": violation.message,
                        "line_number": violation.line_number,
                        "column_number": violation.column_number,
                        "code_snippet": violation.code_snippet,
                        "fix_suggestion": violation.fix_suggestion
                    }
                    for violation in result.violations
                ]
            }
        
        return json.dumps(report_data, indent=2)
    
    def _generate_html_report(self, results: Dict[str, ValidationResult], 
                            config: Dict[str, Any] = None) -> str:
        """Generate an HTML report."""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZEROUI 2.0 Constitution Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #e8f4f8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .file-section {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
        .file-header {{ background-color: #f9f9f9; padding: 10px; font-weight: bold; }}
        .violation {{ margin: 10px; padding: 10px; border-left: 4px solid #ccc; }}
        .error {{ border-left-color: #d32f2f; background-color: #ffebee; }}
        .warning {{ border-left-color: #f57c00; background-color: #fff3e0; }}
        .info {{ border-left-color: #1976d2; background-color: #e3f2fd; }}
        .code {{ background-color: #f5f5f5; padding: 5px; font-family: monospace; }}
        .compliance-good {{ color: #4caf50; }}
        .compliance-warning {{ color: #ff9800; }}
        .compliance-bad {{ color: #f44336; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ZEROUI 2.0 Constitution Validation Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""
        
        # Summary section
        summary = self._calculate_summary(results)
        compliance_class = "compliance-good" if summary["avg_compliance"] >= 80 else \
                          "compliance-warning" if summary["avg_compliance"] >= 60 else "compliance-bad"
        
        html_content += f"""
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Files analyzed:</strong> {summary["total_files"]}</p>
        <p><strong>Total violations:</strong> {summary["total_violations"]}</p>
        <p><strong>Errors:</strong> {summary["total_errors"]}</p>
        <p><strong>Warnings:</strong> {summary["total_warnings"]}</p>
        <p><strong>Info:</strong> {summary["total_info"]}</p>
        <p><strong>Average compliance:</strong> <span class="{compliance_class}">{summary["avg_compliance"]:.1f}%</span></p>
    </div>
"""
        
        # File sections
        for file_path, result in results.items():
            file_name = Path(file_path).name
            compliance_class = "compliance-good" if result.compliance_score >= 80 else \
                              "compliance-warning" if result.compliance_score >= 60 else "compliance-bad"
            
            html_content += f"""
    <div class="file-section">
        <div class="file-header">
            {html.escape(file_name)} - <span class="{compliance_class}">{result.compliance_score}% compliance</span>
        </div>
        <div style="padding: 10px;">
            <p><strong>Violations:</strong> {result.total_violations} | 
               <strong>Processing time:</strong> {result.processing_time:.3f}s</p>
"""
            
            if result.violations:
                for violation in result.violations:
                    severity_class = violation.severity.value
                    html_content += f"""
            <div class="violation {severity_class}">
                <strong>Rule {violation.rule_number}: {html.escape(violation.rule_name)}</strong><br>
                <strong>Line {violation.line_number}:</strong> {html.escape(violation.message)}<br>
                <div class="code">{html.escape(violation.code_snippet)}</div>
"""
                    if violation.fix_suggestion:
                        html_content += f"                <strong>Fix:</strong> {html.escape(violation.fix_suggestion)}<br>"
                    
                    html_content += "            </div>"
            else:
                html_content += "            <p>[OK] No violations found</p>"
            
            html_content += "        </div>    </div>"
        
        html_content += """
</body>
</html>
"""
        return html_content
    
    def _generate_markdown_report(self, results: Dict[str, ValidationResult], 
                                config: Dict[str, Any] = None) -> str:
        """Generate a Markdown report."""
        if not results:
            return "# ZEROUI 2.0 Constitution Validation Report\n\nNo files to validate."
        
        report_lines = []
        report_lines.append("# ZEROUI 2.0 Constitution Validation Report")
        report_lines.append("")
        report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary
        summary = self._calculate_summary(results)
        report_lines.append("## Summary")
        report_lines.append("")
        report_lines.append(f"- **Files analyzed:** {summary['total_files']}")
        report_lines.append(f"- **Total violations:** {summary['total_violations']}")
        report_lines.append(f"- **Errors:** {summary['total_errors']}")
        report_lines.append(f"- **Warnings:** {summary['total_warnings']}")
        report_lines.append(f"- **Info:** {summary['total_info']}")
        report_lines.append(f"- **Average compliance:** {summary['avg_compliance']:.1f}%")
        report_lines.append("")
        
        # File details
        report_lines.append("## File Details")
        report_lines.append("")
        
        for file_path, result in results.items():
            file_name = Path(file_path).name
            compliance_emoji = "✅" if result.compliance_score >= 80 else "⚠️" if result.compliance_score >= 60 else "❌"
            
            report_lines.append(f"### {compliance_emoji} {file_name}")
            report_lines.append("")
            report_lines.append(f"- **Compliance:** {result.compliance_score}%")
            report_lines.append(f"- **Violations:** {result.total_violations}")
            report_lines.append(f"- **Processing time:** {result.processing_time:.3f}s")
            report_lines.append("")
            
            if result.violations:
                report_lines.append("#### Violations")
                report_lines.append("")
                
                for violation in result.violations:
                    severity_emoji = {
                        Severity.ERROR: "🔴",
                        Severity.WARNING: "🟡", 
                        Severity.INFO: "🔵"
                    }.get(violation.severity, "⚪")
                    
                    report_lines.append(f"**{severity_emoji} Rule {violation.rule_number}: {violation.rule_name}**")
                    report_lines.append(f"- **Line {violation.line_number}:** {violation.message}")
                    report_lines.append(f"- **Code:** `{violation.code_snippet}`")
                    
                    if violation.fix_suggestion:
                        report_lines.append(f"- **Fix:** {violation.fix_suggestion}")
                    
                    report_lines.append("")
            else:
                report_lines.append("[OK] No violations found")
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def _calculate_summary(self, results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """Calculate summary statistics for the report."""
        if not results:
            return {
                "total_files": 0,
                "total_violations": 0,
                "total_errors": 0,
                "total_warnings": 0,
                "total_info": 0,
                "avg_compliance": 0.0
            }
        
        total_violations = sum(result.total_violations for result in results.values())
        total_errors = sum(result.violations_by_severity.get(Severity.ERROR, 0) 
                          for result in results.values())
        total_warnings = sum(result.violations_by_severity.get(Severity.WARNING, 0) 
                            for result in results.values())
        total_info = sum(result.violations_by_severity.get(Severity.INFO, 0) 
                        for result in results.values())
        avg_compliance = sum(result.compliance_score for result in results.values()) / len(results)
        
        return {
            "total_files": len(results),
            "total_violations": total_violations,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_info": total_info,
            "avg_compliance": avg_compliance
        }
