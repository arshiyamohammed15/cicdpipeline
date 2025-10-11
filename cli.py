#!/usr/bin/env python3
"""
Command-line interface for ZEROUI 2.0 Constitution Code Validator.

This module provides a CLI for validating Python code against the
71 unique ZEROUI 2.0 Constitution rules.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional

from validator import ConstitutionValidator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ZEROUI 2.0 Constitution Code Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s file.py                    # Validate a single file
  %(prog)s src/                       # Validate all Python files in directory
  %(prog)s src/ --format json         # Output JSON report
  %(prog)s src/ --format html         # Output HTML report
  %(prog)s src/ --format markdown     # Output Markdown report
  %(prog)s src/ --output report.html  # Save report to file
  %(prog)s src/ --enterprise          # Use enterprise-grade rules only
  %(prog)s src/ --severity error      # Only show errors
        """
    )
    
    # Input arguments
    parser.add_argument(
        'path',
        help='File or directory to validate'
    )
    
    # Output format options
    parser.add_argument(
        '--format', '-f',
        choices=['console', 'json', 'html', 'markdown'],
        default='console',
        help='Output format (default: console)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: stdout)'
    )
    
    # Validation options
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        default=True,
        help='Search directories recursively (default: True)'
    )
    
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Disable recursive directory search'
    )
    
    parser.add_argument(
        '--enterprise',
        action='store_true',
        help='Use enterprise-grade rules only (52 critical/important rules)'
    )
    
    parser.add_argument(
        '--severity',
        choices=['error', 'warning', 'info'],
        help='Minimum severity level to report'
    )
    
    # Configuration options
    parser.add_argument(
        '--config',
        default='rules_config.json',
        help='Path to rules configuration file (default: rules_config.json)'
    )
    
    # Performance options
    parser.add_argument(
        '--max-files',
        type=int,
        help='Maximum number of files to process'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Timeout per file in seconds (default: 30)'
    )
    
    # Verbose options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode (minimal output)'
    )
    
    # Version
    parser.add_argument(
        '--version',
        action='version',
        version='ZEROUI 2.0 Constitution Validator v1.0.0'
    )
    
    args = parser.parse_args()
    
    # Handle recursive option
    if args.no_recursive:
        args.recursive = False
    
    try:
        # Validate input path
        input_path = Path(args.path)
        if not input_path.exists():
            print(f"Error: Path does not exist: {args.path}", file=sys.stderr)
            sys.exit(1)
        
        # Initialize validator
        if not Path(args.config).exists():
            print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
            sys.exit(1)
        
        validator = ConstitutionValidator(args.config)
        
        # Run validation
        if input_path.is_file():
            results = validate_file(validator, input_path, args)
        else:
            results = validate_directory(validator, input_path, args)
        
        if not results:
            if not args.quiet:
                print("No Python files found to validate.")
            sys.exit(0)
        
        # Generate report
        report = validator.generate_report(results, args.format)
        
        # Output report
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            if not args.quiet:
                print(f"Report saved to: {args.output}")
        else:
            print(report)
        
        # Exit with appropriate code
        total_errors = sum(
            result.violations_by_severity.get('error', 0) 
            for result in results.values()
        )
        
        if total_errors > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nValidation interrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def validate_file(validator: ConstitutionValidator, file_path: Path, args) -> dict:
    """
    Validate a single file.
    
    Args:
        validator: Constitution validator instance
        file_path: Path to the file to validate
        args: Command line arguments
        
    Returns:
        Dictionary with validation results
    """
    if not file_path.suffix == '.py':
        if not args.quiet:
            print(f"Skipping non-Python file: {file_path}", file=sys.stderr)
        return {}
    
    if args.verbose:
        print(f"Validating: {file_path}")
    
    try:
        result = validator.validate_file(str(file_path))
        return {str(file_path): result}
    except Exception as e:
        print(f"Error validating {file_path}: {e}", file=sys.stderr)
        return {}


def validate_directory(validator: ConstitutionValidator, directory_path: Path, args) -> dict:
    """
    Validate all Python files in a directory.
    
    Args:
        validator: Constitution validator instance
        directory_path: Path to the directory to validate
        args: Command line arguments
        
    Returns:
        Dictionary with validation results
    """
    if args.verbose:
        print(f"Validating directory: {directory_path}")
    
    try:
        results = validator.validate_directory(str(directory_path), args.recursive)
        
        # Apply file limit if specified
        if args.max_files and len(results) > args.max_files:
            if not args.quiet:
                print(f"Warning: Limited to first {args.max_files} files", file=sys.stderr)
            results = dict(list(results.items())[:args.max_files])
        
        return results
    except Exception as e:
        print(f"Error validating directory {directory_path}: {e}", file=sys.stderr)
        return {}


def filter_results_by_severity(results: dict, min_severity: str) -> dict:
    """
    Filter results by minimum severity level.
    
    Args:
        results: Validation results dictionary
        min_severity: Minimum severity level ('error', 'warning', 'info')
        
    Returns:
        Filtered results dictionary
    """
    severity_levels = {'error': 3, 'warning': 2, 'info': 1}
    min_level = severity_levels.get(min_severity, 1)
    
    filtered_results = {}
    
    for file_path, result in results.items():
        filtered_violations = []
        
        for violation in result.violations:
            violation_level = severity_levels.get(violation.severity.value, 1)
            if violation_level >= min_level:
                filtered_violations.append(violation)
        
        if filtered_violations:
            # Create new result with filtered violations
            from validator.core import ValidationResult, Severity
            
            violations_by_severity = {Severity.ERROR: 0, Severity.WARNING: 0, Severity.INFO: 0}
            for violation in filtered_violations:
                violations_by_severity[violation.severity] += 1
            
            filtered_result = ValidationResult(
                file_path=result.file_path,
                total_violations=len(filtered_violations),
                violations_by_severity=violations_by_severity,
                violations=filtered_violations,
                processing_time=result.processing_time,
                compliance_score=result.compliance_score
            )
            
            filtered_results[file_path] = filtered_result
    
    return filtered_results


def apply_enterprise_rules(results: dict) -> dict:
    """
    Apply enterprise-grade rules filtering.
    
    Args:
        results: Validation results dictionary
        
    Returns:
        Filtered results for enterprise rules only
    """
    # Enterprise critical rules: 3, 7, 8, 10, 11, 12, 14, 18, 19, 21, 23, 27, 28, 35, 36, 39, 40, 42, 48, 51, 59, 63, 65, 68, 74
    enterprise_rules = {
        3, 7, 8, 10, 11, 12, 14, 18, 19, 21, 23, 27, 28, 35, 36, 39, 40, 42, 48, 51, 59, 63, 65, 68, 74
    }
    
    filtered_results = {}
    
    for file_path, result in results.items():
        filtered_violations = [
            violation for violation in result.violations
            if violation.rule_number in enterprise_rules
        ]
        
        if filtered_violations:
            from validator.core import ValidationResult, Severity
            
            violations_by_severity = {Severity.ERROR: 0, Severity.WARNING: 0, Severity.INFO: 0}
            for violation in filtered_violations:
                violations_by_severity[violation.severity] += 1
            
            filtered_result = ValidationResult(
                file_path=result.file_path,
                total_violations=len(filtered_violations),
                violations_by_severity=violations_by_severity,
                violations=filtered_violations,
                processing_time=result.processing_time,
                compliance_score=result.compliance_score
            )
            
            filtered_results[file_path] = filtered_result
    
    return filtered_results


if __name__ == '__main__':
    main()
