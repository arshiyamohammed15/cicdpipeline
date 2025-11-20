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
import os
import codecs
import json
import uuid
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set UTF-8 encoding for Windows compatibility
if sys.platform == "win32":
    # Configure stdout to use UTF-8 encoding
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    # Set environment variable for subprocesses
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Import enhanced components
from validator.optimized_core import OptimizedConstitutionValidator
from validator.intelligent_selector import IntelligentRuleSelector
from validator.performance_monitor import PerformanceMonitor
from config.enhanced_config_manager import EnhancedConfigManager


class ErrorCode(Enum):
    """Canonical error codes for consistent error handling."""
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    DEPENDENCY_FAILED = "DEPENDENCY_FAILED"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    CONFLICT = "CONFLICT"
    INVARIANT_VIOLATION = "INVARIANT_VIOLATION"
    CANCELLED = "CANCELLED"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


def safe_print(text: str, file=None) -> None:
    """
    Safely print text with Unicode support, handling encoding issues gracefully.

    Args:
        text: Text to print
        file: Output file (default: stdout)
    """
    try:
        if file is None:
            file = sys.stdout
        print(text, file=file)
    except UnicodeEncodeError:
        # Fallback: replace problematic characters with ASCII equivalents
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text, file=file)


def sanitize_unicode(text: str) -> str:
    """
    Sanitize Unicode text for safe display in console.

    Args:
        text: Input text with potential Unicode characters

    Returns:
        Sanitized text safe for console display
    """
    if not text:
        return text

    # Replace common problematic Unicode characters with ASCII equivalents
    replacements = {
        '\u2011': '-',  # Non-breaking hyphen
        '\u2013': '-',  # En dash
        '\u2014': '--', # Em dash
        '\u2018': "'",  # Left single quotation mark
        '\u2019': "'",  # Right single quotation mark
        '\u201c': '"',  # Left double quotation mark
        '\u201d': '"',  # Right double quotation mark
        '\u2026': '...', # Horizontal ellipsis
        '\u2192': '->', # Rightwards arrow
        '\u2713': '[OK]', # Check mark
        '\u2717': '[X]',  # Ballot X
        '\u00a0': ' ',   # Non-breaking space
    }

    for unicode_char, ascii_replacement in replacements.items():
        text = text.replace(unicode_char, ascii_replacement)

    return text


class EnhancedCLI:
    """
    Enhanced CLI with intelligent features and performance monitoring.
    """

    def __init__(self):
        """Initialize the enhanced CLI."""
        # Initialize structured logging early
        try:
            from config.constitution.logging_config import setup_logging
            setup_logging("config", "INFO")
        except Exception:
            # Fallback: continue without constitution logging setup
            pass
        self.config_manager = EnhancedConfigManager()
        self.validator = OptimizedConstitutionValidator()
        self.rule_selector = IntelligentRuleSelector(self.config_manager)
        self.performance_monitor = PerformanceMonitor()

        # Initialize constitution rule manager
        try:
            self.constitution_manager = self.config_manager.get_constitution_manager()
        except ImportError:
            self.constitution_manager = None
            safe_print("Warning: Constitution rule manager not available")

        # Start performance monitoring
        self.performance_monitor.start_monitoring()

        # Initialize error handling
        self._error_codes = self._load_error_codes()
        self._message_catalog = self._load_message_catalog()
        self._correlation_id = str(uuid.uuid4())

        # AI feature placeholders
        self._ai_confidence_field = None
        self._ai_reasoning_field = None
        self._ai_version_field = None
        self._high_confidence_threshold = 0.9
        self._medium_confidence_threshold = 0.7
        self._low_confidence_threshold = 0.0

    def validate_file(self, file_path: str, args) -> Dict[str, Any]:
        """
        Validate a single file with intelligent rule selection.

        Args:
            file_path: Path to the file to validate
            args: Command line arguments

        Returns:
            Validation results
        """
        # Add correlation logging for request tracking
        request_id = str(uuid.uuid4())
        self._log_correlation_event("request.start", {
            "request_id": request_id,
            "operation": "validate_file",
            "file_path": file_path,
            "correlation_id": self._correlation_id
        })

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
            return self.handle_error(e, context={"file_path": file_path, "operation": "validate_file"})
        finally:
            # Add correlation logging for request completion
            self._log_correlation_event("request.end", {
                "request_id": request_id,
                "operation": "validate_file",
                "file_path": file_path,
                "correlation_id": self._correlation_id
            })

    def validate_directory(self, directory_path: str, args) -> Dict[str, Any]:
        """
        Validate a directory by delegating to the optimized validator, then
        enrich results with context and performance summaries.
        """
        # Use engine's parallel directory validation for performance
        engine_results = self.validator.validate_directory(directory_path, recursive=args.recursive)

        # Wrap engine results to include context/strategy per file
        wrapped_results: Dict[str, Any] = {}
        total_violations = 0

        for file_path, result in engine_results.items():
            try:
                # Reuse lightweight context analysis (no re-parse; use file content read by selector)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                context = self.rule_selector.analyze_file_context(file_path, content)
                strategy = self.rule_selector.get_validation_strategy(context)
            except Exception:
                # If context analysis fails, proceed without it
                context = None
                strategy = None

            wrapped_results[file_path] = {
                "result": result,
                "context": context,
                "strategy": strategy
            }
            total_violations += result.total_violations

        summary = {
            "total_files": len(engine_results),
            "total_violations": total_violations,
            "average_compliance": sum(r.compliance_score for r in engine_results.values()) / len(engine_results) if engine_results else 0,
            "performance_summary": self.performance_monitor.get_performance_summary()
        }

        return {
            "files": wrapped_results,
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
        from datetime import datetime
        from pathlib import Path
        from validator.models import Severity
        
        md = []
        md.append("# ZEROUI 2.0 Constitution Validation Report")
        md.append("")
        md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append("")

        if "summary" in results:
            summary = results["summary"]
            md.append("## Summary")
            md.append("")
            md.append(f"- **Total Files**: {summary.get('total_files', 0)}")
            md.append(f"- **Total Violations**: {summary.get('total_violations', 0)}")
            md.append(f"- **Average Compliance**: {summary.get('average_compliance', 0):.1f}%")
            md.append("")
            
            # Calculate severity breakdown
            if "files" in results:
                total_errors = 0
                total_warnings = 0
                total_info = 0
                for file_data in results["files"].values():
                    result = file_data.get("result")
                    if result and hasattr(result, 'violations_by_severity'):
                        total_errors += result.violations_by_severity.get(Severity.ERROR, 0)
                        total_warnings += result.violations_by_severity.get(Severity.WARNING, 0)
                        total_info += result.violations_by_severity.get(Severity.INFO, 0)
                
                md.append("### Violations by Severity")
                md.append("")
                md.append(f"- **Errors**: {total_errors}")
                md.append(f"- **Warnings**: {total_warnings}")
                md.append(f"- **Info**: {total_info}")
                md.append("")
            
            # Performance summary
            if "performance_summary" in summary and summary["performance_summary"]:
                perf = summary["performance_summary"]
                md.append("### Performance Summary")
                md.append("")
                if "total_time" in perf:
                    md.append(f"- **Total Processing Time**: {perf.get('total_time', 0):.3f}s")
                if "average_time_per_file" in perf:
                    md.append(f"- **Average Time per File**: {perf.get('average_time_per_file', 0):.3f}s")
                md.append("")

        # File details
        if "files" in results and results["files"]:
            md.append("## File Details")
            md.append("")
            
            # Sort files by compliance score (lowest first to highlight issues)
            sorted_files = sorted(
                results["files"].items(),
                key=lambda x: x[1].get("result", type('obj', (object,), {"compliance_score": 0})()).compliance_score
            )
            
            for file_path, file_data in sorted_files:
                result = file_data.get("result")
                if not result:
                    continue
                    
                file_name = Path(file_path).name
                compliance_score = result.compliance_score
                
                # Emoji based on compliance
                if compliance_score >= 80:
                    emoji = "✅"
                elif compliance_score >= 60:
                    emoji = "⚠️"
                else:
                    emoji = "❌"
                
                md.append(f"### {emoji} {file_name}")
                md.append("")
                md.append(f"- **Path**: `{file_path}`")
                md.append(f"- **Compliance**: {compliance_score:.1f}%")
                md.append(f"- **Total Violations**: {result.total_violations}")
                md.append(f"- **Processing Time**: {result.processing_time:.3f}s")
                md.append("")
                
                # Violations breakdown
                if hasattr(result, 'violations_by_severity') and result.violations_by_severity:
                    md.append("#### Violations by Severity")
                    md.append("")
                    md.append(f"- **Errors**: {result.violations_by_severity.get(Severity.ERROR, 0)}")
                    md.append(f"- **Warnings**: {result.violations_by_severity.get(Severity.WARNING, 0)}")
                    md.append(f"- **Info**: {result.violations_by_severity.get(Severity.INFO, 0)}")
                    md.append("")
                
                # List violations (limit to first 10 to keep report manageable)
                if result.violations:
                    md.append("#### Violations")
                    md.append("")
                    for i, violation in enumerate(result.violations[:10]):
                        severity_emoji = {
                            Severity.ERROR: "🔴",
                            Severity.WARNING: "🟡",
                            Severity.INFO: "🔵"
                        }.get(violation.severity, "⚪")
                        
                        md.append(f"**{severity_emoji} Rule {violation.rule_number}: {violation.rule_name}**")
                        md.append(f"- **Line {violation.line_number}**: {violation.message}")
                        if violation.code_snippet:
                            md.append(f"- **Code**: `{violation.code_snippet[:100]}`")
                        if violation.fix_suggestion:
                            md.append(f"- **Fix**: {violation.fix_suggestion}")
                        md.append("")
                    
                    if len(result.violations) > 10:
                        md.append(f"*... and {len(result.violations) - 10} more violations*")
                        md.append("")
                else:
                    md.append("✅ No violations found")
                    md.append("")
                
                md.append("---")
                md.append("")

        return "\n".join(md)

    def _handle_constitution_commands(self, args) -> bool:
        """
        Handle constitution rule management commands.

        Args:
            args: Command line arguments

        Returns:
            True if a constitution command was handled, False otherwise
        """
        # Get constitution manager with specified backend
        backend = getattr(args, 'backend', 'auto')
        try:
            constitution_manager = self.config_manager.get_constitution_manager(backend)
        except Exception as e:
            if any([args.list_rules, args.enable_rule, args.disable_rule,
                   args.rule_stats, args.export_rules, args.rules_by_category, args.search_rules]):
                error_result = self.handle_error(e, context={"operation": "constitution_command"})
                safe_print(f"Error handling constitution command: {error_result.get('user_message', str(e))}")
                return True
            return False

        try:
            if args.list_rules:
                self._list_all_rules(constitution_manager)
                return True

            elif args.enable_rule:
                self._enable_rule(constitution_manager, args.enable_rule)
                return True

            elif args.disable_rule:
                reason = args.disable_reason or "Disabled via CLI"
                self._disable_rule(constitution_manager, args.disable_rule, reason)
                return True

            elif args.rule_stats:
                self._show_rule_statistics(constitution_manager)
                return True

            elif args.export_rules:
                self._export_rules(constitution_manager, args.export_enabled_only, args.output)
                return True

            elif args.rules_by_category:
                self._list_rules_by_category(constitution_manager, args.rules_by_category)
                return True

            elif args.search_rules:
                self._search_rules(constitution_manager, args.search_rules)
                return True

        except Exception as e:
            error_result = self.handle_error(e, context={"operation": "constitution_command"})
            safe_print(f"Error handling constitution command: {error_result.get('user_message', str(e))}")
            return True

        return False

    def _handle_backend_commands(self, args) -> bool:
        """Handle backend management commands."""
        try:
            if args.switch_backend:
                self._switch_backend(args.switch_backend)
                return True

            elif args.sync_backends:
                self._sync_backends()
                return True

            elif args.migrate:
                self._migrate_backends(args.migrate)
                return True

            elif args.verify_sync:
                self._verify_sync()
                return True

            elif getattr(args, 'verify_consistency', False):
                self._verify_consistency()
                return True

            elif args.backend_status:
                self._show_backend_status()
                return True

            elif args.repair_sync:
                self._repair_sync()
                return True

            elif args.migrate_config:
                self._migrate_config()
                return True

            elif args.validate_config:
                self._validate_config()
                return True

            elif args.config_info:
                self._show_config_info()
                return True

            elif getattr(args, 'rebuild_from_markdown', False):
                self._rebuild_from_markdown()
                return True

        except Exception as e:
            error_result = self.handle_error(e, context={"operation": "backend_command"})
            safe_print(f"Error handling backend command: {error_result.get('user_message', str(e))}")
            return True

        return False

    def _switch_backend(self, new_backend: str):
        """Switch the default backend."""
        try:
            success = self.config_manager.switch_constitution_backend(new_backend)
            if success:
                safe_print(f"[OK] Switched default backend to {new_backend}")
            else:
                safe_print(f"[FAIL] Failed to switch backend to {new_backend}")
        except Exception as e:
            safe_print(f"[FAIL] Error switching backend: {e}")

    def _sync_backends(self):
        """Synchronize backends."""
        try:
            safe_print("Synchronizing backends...")
            result = self.config_manager.sync_constitution_backends()

            if result.get("success", False):
                safe_print("[OK] Backend synchronization completed successfully")
                if "syncs" in result:
                    for sync_type, sync_result in result["syncs"].items():
                        if sync_result.get("success", False):
                            changes = sync_result.get("changes_made", 0)
                            safe_print(f"  {sync_type}: {changes} changes made")
            else:
                safe_print(f"[FAIL] Backend synchronization failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            safe_print(f"[FAIL] Error synchronizing backends: {e}")

    def _migrate_backends(self, migration_type: str):
        """Migrate data between backends."""
        try:
            safe_print(f"Starting migration: {migration_type}")

            if migration_type == "sqlite-to-json":
                from config.constitution.migration import migrate_sqlite_to_json
                result = migrate_sqlite_to_json()
            elif migration_type == "json-to-sqlite":
                from config.constitution.migration import migrate_json_to_sqlite
                result = migrate_json_to_sqlite()
            else:
                safe_print(f"[FAIL] Unknown migration type: {migration_type}")
                return

            if result.get("success", False):
                rules_migrated = result.get("rules_migrated", 0)
                safe_print(f"[OK] Migration completed successfully. Migrated {rules_migrated} rules.")

                if result.get("backup_created", False):
                    safe_print(f"  Backup created: {result.get('backup_path', 'Unknown')}")
            else:
                safe_print(f"[FAIL] Migration failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            safe_print(f"[FAIL] Error during migration: {e}")

    def _verify_sync(self):
        """Verify backend synchronization."""
        try:
            from config.constitution.sync_manager import verify_sync
            result = verify_sync()

            if result.get("synchronized", False):
                safe_print("[OK] Backends are synchronized")
                safe_print(f"  Total rules: {result.get('total_rules', 0)}")
                safe_print(f"  SQLite rules: {result.get('sqlite_rules', 0)}")
                safe_print(f"  JSON rules: {result.get('json_rules', 0)}")
            else:
                safe_print("[FAIL] Backends are not synchronized")
                differences = result.get("differences", [])
                safe_print(f"  Differences found: {len(differences)}")

                for diff in differences[:5]:  # Show first 5 differences
                    safe_print(f"    Rule {diff.get('rule_number', 'Unknown')}: {diff.get('issue', 'Unknown issue')}")

                if len(differences) > 5:
                    safe_print(f"    ... and {len(differences) - 5} more differences")
        except Exception as e:
            safe_print(f"[FAIL] Error verifying sync: {e}")

    def _verify_consistency(self):
        """Verify consistency across Markdown, DB, JSON export, and config."""
        try:
            from config.constitution.sync_manager import get_sync_manager
            mgr = get_sync_manager()
            result = mgr.verify_consistency_across_sources()

            consistent = result.get("consistent", False)
            if consistent:
                safe_print("[OK] All sources are consistent")
            else:
                safe_print("[FAIL] Inconsistencies detected across sources")

            summary = result.get("summary", {})
            if summary:
                safe_print(f"\nSummary:")
                safe_print(f"  Total rules observed: {summary.get('total_rules_observed', 0)}")
                missing = summary.get('missing', {})
                safe_print(f"  Missing -> markdown: {missing.get('markdown', 0)}, db: {missing.get('database', 0)}, json: {missing.get('json_export', 0)}, config: {missing.get('config', 0)}")
                safe_print(f"  Field mismatch rules: {summary.get('field_mismatch_rules', 0)}")
                safe_print(f"  Enabled mismatch rules: {summary.get('enabled_mismatch_rules', 0)}")
                safe_print(f"  Total differences: {summary.get('differences_count', 0)}")

            warnings = result.get("warnings", [])
            if warnings:
                safe_print(f"\nWarnings:")
                for w in warnings:
                    safe_print(f"  - {w}")

            # Print all differences with detailed per-rule information
            diffs = result.get("differences", [])
            if diffs:
                safe_print(f"\nDetailed Differences ({len(diffs)} rules):")
                safe_print("=" * 80)
                for d in diffs:
                    rn = d.get('rule_number')
                    missing = d.get('missing', {})
                    fields = d.get('field_mismatches', [])
                    enabled = d.get('enabled', {})
                    details = d.get('field_details', {})

                    safe_print(f"\nRule {rn}:")

                    # Show missing sources
                    missing_sources = [k for k, v in missing.items() if v]
                    if missing_sources:
                        safe_print(f"  Missing from: {', '.join(missing_sources)}")

                    # Show field mismatches with actual values
                    if fields:
                        safe_print(f"  Field mismatches:")
                        for field in fields:
                            field_vals = details.get(field, {})
                            if field_vals:
                                safe_print(f"    {field}:")
                                for src, val in field_vals.items():
                                    val_display = (val[:60] + "...") if val and len(val) > 60 else val
                                    safe_print(f"      {src}: {val_display}")

                    # Show enabled mismatches
                    enabled_vals = {k: v for k, v in enabled.items() if v is not None}
                    if enabled_vals and len(set(enabled_vals.values())) > 1:
                        safe_print(f"  Enabled status mismatch:")
                        for src, val in enabled_vals.items():
                            safe_print(f"    {src}: {val}")

            # Error details
            error = result.get("error")
            if error:
                safe_print(f"\nError during validation: {error}")

        except Exception as e:
            safe_print(f"[FAIL] Error verifying consistency: {e}")
            import traceback
            safe_print(traceback.format_exc())

    def _show_backend_status(self):
        """Show status of all backends."""
        try:
            status = self.config_manager.get_constitution_backend_status()

            safe_print("Backend Status:")
            safe_print("=" * 50)

            current_backend = status.get("current_backend", "Unknown")
            fallback_backend = status.get("fallback_backend", "Unknown")
            auto_fallback = status.get("auto_fallback", False)
            auto_sync = status.get("auto_sync", False)

            safe_print(f"Current backend: {current_backend}")
            safe_print(f"Fallback backend: {fallback_backend}")
            safe_print(f"Auto-fallback: {'Enabled' if auto_fallback else 'Disabled'}")
            safe_print(f"Auto-sync: {'Enabled' if auto_sync else 'Disabled'}")
            safe_print("")

            backends = status.get("backends", {})
            for backend_name, backend_info in backends.items():
                available = backend_info.get("available", False)
                healthy = backend_info.get("healthy", False)
                status_text = "Available & Healthy" if (available and healthy) else "Available" if available else "Unavailable"

                safe_print(f"{backend_name.upper()} Backend:")
                safe_print(f"  Status: {status_text}")

                if available:
                    config = backend_info.get("config", {})
                    path = config.get("path", "Unknown")
                    safe_print(f"  Path: {path}")

                    health = backend_info.get("health", {})
                    if health:
                        safe_print(f"  Last updated: {health.get('last_updated', 'Unknown')}")
                else:
                    error = backend_info.get("error", "Unknown error")
                    safe_print(f"  Error: {error}")
                safe_print("")
        except Exception as e:
            safe_print(f"[FAIL] Error getting backend status: {e}")

    def _repair_sync(self):
        """Repair backend synchronization."""
        try:
            safe_print("Repairing backend synchronization...")
            from config.constitution.migration import repair_sync
            result = repair_sync()

            if result.get("success", False):
                conflicts_found = result.get("conflicts_found", 0)
                conflicts_resolved = result.get("conflicts_resolved", 0)
                safe_print(f"[OK] Sync repair completed successfully")
                safe_print(f"  Conflicts found: {conflicts_found}")
                safe_print(f"  Conflicts resolved: {conflicts_resolved}")
            else:
                safe_print(f"[FAIL] Sync repair failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            safe_print(f"[FAIL] Error repairing sync: {e}")

    def _migrate_config(self):
        """Migrate configuration from v1.0 to v2.0."""
        try:
            safe_print("Migrating configuration from v1.0 to v2.0...")
            from config.constitution import migrate_configuration

            success = migrate_configuration(create_backup=True)
            if success:
                safe_print("[OK] Configuration successfully migrated to v2.0")
                safe_print("Backup created in config/backups/ directory")
            else:
                safe_print("[FAIL] Configuration migration failed")
        except Exception as e:
            safe_print(f"[FAIL] Error migrating configuration: {e}")

    def _validate_config(self):
        """Validate v2.0 configuration."""
        try:
            safe_print("Validating configuration...")
            from config.constitution import validate_configuration

            is_valid = validate_configuration()
            if is_valid:
                safe_print("[OK] Configuration is valid")
            else:
                safe_print("[FAIL] Configuration validation failed")
        except Exception as e:
            safe_print(f"[FAIL] Error validating configuration: {e}")

    def _show_config_info(self):
        """Show configuration information and migration status."""
        try:
            safe_print("Configuration Information")
            safe_print("=" * 50)

            from config.constitution import get_migration_info, get_active_backend_config

            # Get migration info
            migration_info = get_migration_info()
            safe_print(f"Config exists: {migration_info.get('config_exists', False)}")
            safe_print(f"Current version: {migration_info.get('current_version', 'Unknown')}")
            safe_print(f"Migration needed: {migration_info.get('migration_needed', False)}")

            backups = migration_info.get('backups_available', [])
            if backups:
                safe_print(f"Available backups: {len(backups)}")
                for backup in backups[-3:]:  # Show last 3 backups
                    safe_print(f"  - {backup}")
            else:
                safe_print("No backups available")

            safe_print("")

            # Get active backend config
            try:
                backend_config = get_active_backend_config()
                safe_print("Active Backend Configuration:")
                safe_print(f"  Backend: {backend_config.get('backend', 'Unknown')}")
                safe_print(f"  Version: {backend_config.get('version', 'Unknown')}")

                config = backend_config.get('config', {})
                if config:
                    safe_print("  Configuration:")
                    for key, value in config.items():
                        safe_print(f"    {key}: {value}")
            except Exception as e:
                safe_print(f"Error getting backend config: {e}")

        except Exception as e:
            safe_print(f"[FAIL] Error getting configuration info: {e}")

    def _rebuild_from_markdown(self):
        """
        Rebuild SQLite and JSON databases from Markdown (single source of truth).

        This command:
        1. Extracts all rules from ZeroUI2.0_Master_Constitution.md
        2. Preserves current enabled/disabled states from config
        3. Drops and recreates SQLite database
        4. Drops and recreates JSON database
        5. Restores preserved enabled/disabled states
        6. Validates consistency across all sources
        """
        from config.constitution.rule_extractor import ConstitutionRuleExtractor
        from config.constitution.database import ConstitutionRulesDB
        import json
        from pathlib import Path
        from datetime import datetime

        safe_print("\n" + "="*70)
        safe_print("REBUILDING FROM MARKDOWN (Single Source of Truth)")
        safe_print("="*70)

        # Step 1: Extract rules from Markdown
        safe_print("\n[1/6] Extracting rules from Markdown...")
        extractor = ConstitutionRuleExtractor("docs/architecture/ZeroUI2.0_Master_Constitution.md")
        try:
            rules = extractor.extract_all_rules()
            safe_print(f"✓ Found {len(rules)} rules in Markdown")
        except Exception as e:
            safe_print(f"✗ Failed to extract rules: {e}")
            return

        # Step 2: Preserve current enabled/disabled states
        safe_print("\n[2/6] Preserving enabled/disabled states...")
        preserved_states = {}
        try:
            config_path = Path("config/constitution_config.json")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    rules_config = config_data.get("rules", {})
                    for rule_num_str, rule_state in rules_config.items():
                        rule_num = int(rule_num_str)
                        preserved_states[rule_num] = {
                            "enabled": rule_state.get("enabled", True),
                            "disabled_reason": rule_state.get("disabled_reason"),
                            "disabled_at": rule_state.get("disabled_at")
                        }
            safe_print(f"✓ Preserved states for {len(preserved_states)} rules")
        except Exception as e:
            safe_print(f"⚠ Warning: Could not preserve states: {e}")
            preserved_states = {}

        # Step 3: Rebuild SQLite database
        safe_print("\n[3/6] Rebuilding SQLite database...")
        try:
            db_path = Path("config/constitution_rules.db")
            db = ConstitutionRulesDB(str(db_path))

            # Clear all existing data
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM constitution_rules")
                cursor.execute("DELETE FROM rule_configuration")
                cursor.execute("DELETE FROM rule_categories")
                conn.commit()

            # Insert all rules from Markdown
            import json
            with db.get_connection() as conn:
                cursor = conn.cursor()

                for rule in rules:
                    # Insert rule
                    cursor.execute("""
                        INSERT OR REPLACE INTO constitution_rules (rule_number, title, category, priority, content, json_metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        rule['rule_number'],
                        rule['title'],
                        rule['category'],
                        rule['priority'],
                        rule['content'],
                        json.dumps(rule)
                    ))

                    # Insert configuration with preserved enabled/disabled state
                    enabled = 1 if preserved_states.get(rule['rule_number'], {}).get("enabled", True) else 0
                    disabled_reason = preserved_states.get(rule['rule_number'], {}).get("disabled_reason")
                    disabled_at = preserved_states.get(rule['rule_number'], {}).get("disabled_at")

                    cursor.execute("""
                        INSERT OR REPLACE INTO rule_configuration (rule_number, enabled, config_data, disabled_reason, disabled_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        rule['rule_number'],
                        enabled,
                        json.dumps({"default_enabled": True, "notes": ""}),
                        disabled_reason,
                        disabled_at
                    ))

                # Insert categories
                for category_name, category_info in extractor.categories.items():
                    rule_count = len([r for r in rules if r['category'] == category_name])
                    cursor.execute("""
                        INSERT OR REPLACE INTO rule_categories (name, description, priority, rule_count)
                        VALUES (?, ?, ?, ?)
                    """, (
                        category_name,
                        category_info['description'],
                        category_info['priority'],
                        rule_count
                    ))

                conn.commit()

            db.close()
            safe_print(f"✓ Rebuilt SQLite database with {len(rules)} rules")
        except Exception as e:
            safe_print(f"✗ Failed to rebuild SQLite: {e}")
            import traceback
            safe_print(traceback.format_exc())
            return

        # Step 4: Rebuild JSON database
        safe_print("\n[4/6] Rebuilding JSON database...")
        try:
            json_path = Path("config/constitution_rules.json")

            # Create new JSON structure
            json_data = {
                "version": "2.0",
                "database": "constitution_rules",
                "last_updated": None,
                "statistics": {
                    "total_rules": len(rules),
                    "enabled_rules": 0,
                    "disabled_rules": 0,
                    "categories": {}
                },
                "categories": {},
                "rules": {}
            }

            # Add categories
            for category_name, category_info in extractor.categories.items():
                json_data["categories"][category_name] = {
                    "name": category_name,
                    "description": category_info["description"],
                    "priority": category_info["priority"],
                    "rule_count": 0
                }

            # Add rules
            for rule in rules:
                rule_num_str = str(rule["rule_number"])
                enabled = preserved_states.get(rule["rule_number"], {}).get("enabled", True)

                json_data["rules"][rule_num_str] = {
                    "rule_number": rule["rule_number"],
                    "title": rule["title"],
                    "category": rule["category"],
                    "priority": rule["priority"],
                    "content": rule["content"],
                    "enabled": enabled,
                    "config": {
                        "default_enabled": True,
                        "notes": "",
                        "disabled_reason": preserved_states.get(rule["rule_number"], {}).get("disabled_reason"),
                        "disabled_at": preserved_states.get(rule["rule_number"], {}).get("disabled_at")
                    },
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                        "usage_count": 0,
                        "last_used": None,
                        "source": "markdown_rebuild"
                    }
                }

                # Update category counts
                if rule["category"] in json_data["categories"]:
                    json_data["categories"][rule["category"]]["rule_count"] += 1

                # Update statistics
                if enabled:
                    json_data["statistics"]["enabled_rules"] += 1
                else:
                    json_data["statistics"]["disabled_rules"] += 1

            json_data["last_updated"] = datetime.now().isoformat()

            # Write JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            safe_print(f"✓ Rebuilt JSON database with {len(rules)} rules")
        except Exception as e:
            safe_print(f"✗ Failed to rebuild JSON: {e}")
            return

        # Step 5: Update config file to remove duplicated rule content
        safe_print("\n[5/6] Updating config file (runtime state only)...")
        try:
            config_path = Path("config/constitution_config.json")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # Keep only enabled/disabled states in config
                # Remove any duplicated rule content that shouldn't be there
                if "rules" in config_data:
                    for rule_num_str, rule_state in config_data["rules"].items():
                        # Keep only: enabled, disabled_reason, disabled_at, updated_at
                        # Remove: title, content, category, priority (those belong in Markdown)
                        keys_to_keep = ["enabled", "disabled_reason", "disabled_at", "updated_at", "config"]
                        keys_to_remove = [k for k in list(rule_state.keys()) if k not in keys_to_keep]
                        for key in keys_to_remove:
                            del rule_state[key]

                config_data["last_updated"] = datetime.now().isoformat()
                config_data["total_rules"] = len(rules)

                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)

            safe_print("✓ Config file updated (runtime state only)")
        except Exception as e:
            safe_print(f"⚠ Warning: Could not update config: {e}")

        # Step 6: Verify consistency
        safe_print("\n[6/6] Verifying consistency across all sources...")
        try:
            from config.constitution.sync_manager import ConstitutionSyncManager
            sync_mgr = ConstitutionSyncManager()
            result = sync_mgr.verify_consistency_across_sources()

            if result["consistent"]:
                safe_print("✓ All sources are consistent")
            else:
                safe_print("⚠ Warning: Inconsistencies detected:")
                safe_print(f"  Total differences: {result['summary'].get('differences_count', 0)}")
        except Exception as e:
            safe_print(f"⚠ Warning: Could not verify consistency: {e}")

        safe_print("\n" + "="*70)
        safe_print("✓ REBUILD COMPLETE")
        safe_print("="*70)
        safe_print("\nMarkdown is now the single source of truth.")
        safe_print("To modify rules:")
        safe_print("  1. Edit ZeroUI2.0_Master_Constitution.md")
        safe_print("  2. Run: python enhanced_cli.py --rebuild-from-markdown")
        safe_print("  3. Commit changes to Git\n")

    def _list_all_rules(self, constitution_manager):
        """List all constitution rules with their status."""
        safe_print("Constitution Rules Status:")
        safe_print("=" * 50)

        all_rules = constitution_manager.get_all_rules()

        for rule in all_rules:
            status = "[ENABLED]" if rule['enabled'] else "[DISABLED]"
            title = sanitize_unicode(rule['title'][:50])
            safe_print(f"Rule {rule['rule_number']:3d}: {title:<50} {status}")

        safe_print(f"\nTotal: {len(all_rules)} rules")

    def _enable_rule(self, constitution_manager, rule_number: int):
        """Enable a specific rule."""
        rule = constitution_manager.get_rule_by_number(rule_number)
        if not rule:
            safe_print(f"Error: Rule {rule_number} not found")
            return

        if rule['enabled']:
            safe_print(f"Rule {rule_number} is already enabled")
            return

        success = constitution_manager.enable_rule(rule_number, {"enabled_via": "CLI"})
        if success:
            safe_print(f"[OK] Rule {rule_number} enabled successfully")
        else:
            safe_print(f"[FAIL] Failed to enable rule {rule_number}")

    def _disable_rule(self, constitution_manager, rule_number: int, reason: str):
        """Disable a specific rule."""
        rule = constitution_manager.get_rule_by_number(rule_number)
        if not rule:
            safe_print(f"Error: Rule {rule_number} not found")
            return

        if not rule['enabled']:
            safe_print(f"Rule {rule_number} is already disabled")
            return

        success = constitution_manager.disable_rule(rule_number, reason)
        if success:
            safe_print(f"[OK] Rule {rule_number} disabled successfully")
            safe_print(f"  Reason: {reason}")
        else:
            safe_print(f"[FAIL] Failed to disable rule {rule_number}")

    def _show_rule_statistics(self, constitution_manager):
        """Show constitution rule statistics."""
        stats = constitution_manager.get_rule_statistics()

        safe_print("Constitution Rules Statistics:")
        safe_print("=" * 40)
        safe_print(f"Total rules: {stats['total_rules']}")
        safe_print(f"Enabled rules: {stats['enabled_rules']}")
        safe_print(f"Disabled rules: {stats['disabled_rules']}")
        safe_print(f"Enabled percentage: {stats['enabled_percentage']:.1f}%")

        safe_print(f"\nRules by category:")
        for category, count in stats['category_counts'].items():
            safe_print(f"  {category}: {count} rules")

        safe_print(f"\nRules by priority:")
        for priority, count in stats['priority_counts'].items():
            safe_print(f"  {priority}: {count} rules")

    def _export_rules(self, constitution_manager, enabled_only: bool, output_file: Optional[str]):
        """Export rules to JSON."""
        json_data = constitution_manager.export_rules_to_json(enabled_only)

        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                safe_print(f"Rules exported to {output_file}")
            except UnicodeEncodeError:
                # Fallback: sanitize Unicode characters before writing
                safe_json_data = sanitize_unicode(json_data)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(safe_json_data)
                safe_print(f"Rules exported to {output_file} (Unicode characters sanitized)")
        else:
            safe_print(json_data)

    def _list_rules_by_category(self, constitution_manager, category: str):
        """List rules by category."""
        rules = constitution_manager.get_rules_by_category(category)

        if not rules:
            safe_print(f"No rules found in category '{category}'")
            return

        safe_print(f"Rules in category '{category}':")
        safe_print("=" * 50)

        for rule in rules:
            status = "[ENABLED]" if rule['enabled'] else "[DISABLED]"
            title = sanitize_unicode(rule['title'][:50])
            safe_print(f"Rule {rule['rule_number']:3d}: {title:<50} {status}")

        safe_print(f"\nTotal: {len(rules)} rules in category '{category}'")

    def _search_rules(self, constitution_manager, search_term: str):
        """Search rules by title or content."""
        results = constitution_manager.search_rules(search_term)

        if not results:
            safe_print(f"No rules found matching '{search_term}'")
            return

        safe_print(f"Rules matching '{search_term}':")
        safe_print("=" * 50)

        for rule in results:
            status = "[ENABLED]" if rule['enabled'] else "[DISABLED]"
            title = sanitize_unicode(rule['title'][:50])
            safe_print(f"Rule {rule['rule_number']:3d}: {title:<50} {status}")

        safe_print(f"\nTotal: {len(results)} rules found")

    def handle_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Central error handler with code mapping, structured logging, and user-friendly messages.

        Args:
            exception: The exception to handle
            context: Additional context information

        Returns:
            Error handling result with user message, error code, and structured data
        """
        try:
            # Map exception to canonical error code
            error_code = self._map_exception_to_code(exception)

            # Get user-friendly message from catalog
            user_message = self._get_user_message_from_catalog(error_code, context)

            # Create structured log entry
            log_entry = self._create_log_entry(exception, error_code, context)

            # Log the error
            self._log_error(log_entry)

            # Determine if operation should be retried
            should_retry = self._should_retry(error_code, exception)

            # Get recovery guidance
            recovery_guidance = self._get_recovery_guidance(error_code, context)

            return {
                "error_code": error_code.value,
                "user_message": user_message,
                "should_retry": should_retry,
                "recovery_guidance": recovery_guidance,
                "correlation_id": self._correlation_id,
                "timestamp": time.time(),
                "context": context or {}
            }

        except Exception as e:
            # Fallback error handling
            return {
                "error_code": ErrorCode.INTERNAL_ERROR.value,
                "user_message": "An unexpected error occurred while handling an error",
                "should_retry": False,
                "recovery_guidance": "Please contact support if this persists",
                "correlation_id": self._correlation_id,
                "timestamp": time.time(),
                "context": context or {},
                "fallback_error": str(e)
            }

    def _load_error_codes(self) -> Dict[str, Dict[str, Any]]:
        """Load canonical error codes with severity levels."""
        return {
            ErrorCode.INTERNAL_ERROR.value: {"severity": ErrorSeverity.HIGH.value, "retriable": False},
            ErrorCode.VALIDATION_ERROR.value: {"severity": ErrorSeverity.MEDIUM.value, "retriable": False},
            ErrorCode.AUTH_FORBIDDEN.value: {"severity": ErrorSeverity.HIGH.value, "retriable": False},
            ErrorCode.RESOURCE_NOT_FOUND.value: {"severity": ErrorSeverity.MEDIUM.value, "retriable": False},
            ErrorCode.DEPENDENCY_FAILED.value: {"severity": ErrorSeverity.HIGH.value, "retriable": True},
            ErrorCode.TIMEOUT.value: {"severity": ErrorSeverity.MEDIUM.value, "retriable": True},
            ErrorCode.RATE_LIMITED.value: {"severity": ErrorSeverity.MEDIUM.value, "retriable": True},
            ErrorCode.CONFLICT.value: {"severity": ErrorSeverity.MEDIUM.value, "retriable": False},
            ErrorCode.INVARIANT_VIOLATION.value: {"severity": ErrorSeverity.HIGH.value, "retriable": False},
            ErrorCode.CANCELLED.value: {"severity": ErrorSeverity.LOW.value, "retriable": False}
        }

    def _load_message_catalog(self) -> Dict[str, str]:
        """Load user-friendly error messages."""
        return {
            ErrorCode.INTERNAL_ERROR.value: "An internal error occurred. Please try again or contact support.",
            ErrorCode.VALIDATION_ERROR.value: "Validation failed. Please check your input and try again.",
            ErrorCode.AUTH_FORBIDDEN.value: "Access denied. You don't have permission to perform this action.",
            ErrorCode.RESOURCE_NOT_FOUND.value: "The requested resource was not found.",
            ErrorCode.DEPENDENCY_FAILED.value: "A required service is temporarily unavailable. Please try again later.",
            ErrorCode.TIMEOUT.value: "The operation timed out. Please try again.",
            ErrorCode.RATE_LIMITED.value: "Too many requests. Please wait a moment and try again.",
            ErrorCode.CONFLICT.value: "A conflict occurred. Please resolve the conflict and try again.",
            ErrorCode.INVARIANT_VIOLATION.value: "An unexpected state was detected. Please contact support.",
            ErrorCode.CANCELLED.value: "The operation was cancelled."
        }

    def _map_exception_to_code(self, exception: Exception) -> ErrorCode:
        """Map Python exceptions to canonical error codes."""
        exception_type = type(exception).__name__

        if isinstance(exception, (ValueError, TypeError, AttributeError)):
            return ErrorCode.VALIDATION_ERROR
        elif isinstance(exception, (FileNotFoundError, OSError)):
            return ErrorCode.RESOURCE_NOT_FOUND
        elif isinstance(exception, (ConnectionError, TimeoutError)):
            return ErrorCode.DEPENDENCY_FAILED
        elif isinstance(exception, KeyboardInterrupt):
            return ErrorCode.CANCELLED
        elif isinstance(exception, PermissionError):
            return ErrorCode.AUTH_FORBIDDEN
        else:
            return ErrorCode.INTERNAL_ERROR

    def _get_user_message_from_catalog(self, error_code: ErrorCode, context: Optional[Dict[str, Any]] = None) -> str:
        """Get user-friendly message from catalog with context."""
        base_message = self._message_catalog.get(error_code.value, "An unexpected error occurred.")

        # Add context-specific information if available
        if context and "file_path" in context:
            base_message += f" (File: {context['file_path']})"

        return base_message

    def _create_log_entry(self, exception: Exception, error_code: ErrorCode, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create structured log entry with correlation ID."""
        log_entry = {
            "timestamp": time.time(),
            "level": "ERROR",
            "traceId": self._correlation_id,
            "error.code": error_code.value,
            "error.message": str(exception),
            "error.type": type(exception).__name__,
            "error.severity": self._error_codes.get(error_code.value, {}).get("severity", "UNKNOWN"),
            "context": self._redact_secrets(context or {})
        }

        # Add AI-specific fields if available
        if self._ai_confidence_field:
            log_entry["ai.confidence"] = self._ai_confidence_field
        if self._ai_reasoning_field:
            log_entry["ai.reasoning"] = self._ai_reasoning_field
        if self._ai_version_field:
            log_entry["ai.version"] = self._ai_version_field

        return log_entry

    def _redact_secrets(self, data: Any) -> Any:
        """Recursively redact secrets and PII from data."""
        if isinstance(data, dict):
            redacted = {}
            for key, value in data.items():
                if any(secret in key.lower() for secret in ['password', 'token', 'key', 'secret', 'auth']):
                    redacted[key] = "[REDACTED]"
                else:
                    redacted[key] = self._redact_secrets(value)
            return redacted
        elif isinstance(data, list):
            return [self._redact_secrets(item) for item in data]
        else:
            return data

    def _log_error(self, log_entry: Dict[str, Any]) -> None:
        """Log error with structured format."""
        if self._is_structured_logging_enabled():
            # Log as JSONL format
            print(json.dumps(log_entry), file=sys.stderr)
        else:
            # Fallback to simple format
            print(f"ERROR [{log_entry['traceId']}]: {log_entry['error.message']}", file=sys.stderr)

    def _log_correlation_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log correlation events for request tracking."""
        if self._is_structured_logging_enabled():
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "event_type": event_type,
                "traceId": self._correlation_id,
                **data
            }
            print(json.dumps(log_entry), file=sys.stderr)

    def _is_structured_logging_enabled(self) -> bool:
        """Check if structured logging is enabled in configuration."""
        try:
            return self.config_manager.get_config().get("error_handling", {}).get("enable_structured_logging", True)
        except Exception:
            return True

    def _should_retry(self, error_code: ErrorCode, exception: Exception) -> bool:
        """Determine if operation should be retried based on error type."""
        return self._error_codes.get(error_code.value, {}).get("retriable", False)

    def _get_recovery_guidance(self, error_code: ErrorCode, context: Optional[Dict[str, Any]] = None) -> str:
        """Get recovery guidance for the error."""
        guidance_map = {
            ErrorCode.INTERNAL_ERROR.value: "Please try again. If the problem persists, contact support.",
            ErrorCode.VALIDATION_ERROR.value: "Please check your input and try again.",
            ErrorCode.AUTH_FORBIDDEN.value: "Check your permissions and try again.",
            ErrorCode.RESOURCE_NOT_FOUND.value: "Verify the resource exists and try again.",
            ErrorCode.DEPENDENCY_FAILED.value: "The service will retry automatically. Please wait.",
            ErrorCode.TIMEOUT.value: "The operation will be retried automatically.",
            ErrorCode.RATE_LIMITED.value: "Please wait a moment before trying again.",
            ErrorCode.CONFLICT.value: "Resolve the conflict and try again.",
            ErrorCode.INVARIANT_VIOLATION.value: "This indicates a system issue. Please contact support.",
            ErrorCode.CANCELLED.value: "Operation was cancelled by user."
        }

        return guidance_map.get(error_code.value, "Please try again.")

    def _wrap_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Exception:
        """Wrap exception with additional context."""
        if context:
            context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
            return Exception(f"{str(exception)} (Context: {context_str})")
        return exception

    # AI feature placeholder methods
    def _record_error_feedback(self, error_code: str, user_feedback: str) -> None:
        """Record user feedback for AI learning."""
        # Placeholder for AI learning from user feedback
        pass

    def _get_error_patterns(self) -> Dict[str, Any]:
        """Get error patterns for AI analysis."""
        # Placeholder for AI pattern analysis
        return {}

    def _update_ai_model(self, feedback_data: Dict[str, Any]) -> None:
        """Update AI model based on feedback."""
        # Placeholder for AI model updates
        pass

    def _get_action_for_confidence(self, confidence: float) -> str:
        """Get recommended action based on AI confidence level."""
        if confidence >= self._high_confidence_threshold:
            return "auto_apply"
        elif confidence >= self._medium_confidence_threshold:
            return "suggest_with_review"
        else:
            return "manual_review_required"

    # Recovery and state management placeholder methods
    def _get_recovery_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Get recovery checkpoint for long-running operations."""
        # Placeholder for recovery checkpoints
        return None

    def _create_checkpoint(self, state: Dict[str, Any]) -> None:
        """Create checkpoint for recovery."""
        # Placeholder for checkpoint creation
        pass

    def _get_current_state(self) -> Dict[str, Any]:
        """Get current system state."""
        # Placeholder for state tracking
        return {}

    def _is_long_running_operation(self, operation: str) -> bool:
        """Check if operation is long-running."""
        long_running_ops = ["validate_directory", "batch_validation", "sync_operation"]
        return operation in long_running_ops

    # Graceful degradation placeholder methods
    def _handle_backend_failure(self, backend: str) -> None:
        """Handle backend failure gracefully."""
        # Placeholder for backend failure handling
        pass

    def _check_dependencies(self) -> Dict[str, bool]:
        """Check system dependencies."""
        # Placeholder for dependency checking
        return {}

    def _get_available_features(self) -> List[str]:
        """Get list of available features."""
        # Placeholder for feature availability
        return []

    def _check_backend_health(self) -> Dict[str, Any]:
        """Check backend health status."""
        # Placeholder for health checking
        return {"status": "healthy"}

    def _get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        # Placeholder for system status
        return {"status": "operational"}

    # Feature flag placeholder methods
    def _is_feature_enabled(self, feature: str) -> bool:
        """Check if feature is enabled."""
        # Placeholder for feature flag checking
        return True

    def _detect_feature_error(self, feature: str, error: Exception) -> bool:
        """Detect if error is related to feature flag."""
        # Placeholder for feature error detection
        return False

    def _handle_feature_error(self, feature: str, error: Exception) -> None:
        """Handle feature-specific errors."""
        # Placeholder for feature error handling
        pass

    def _get_error_rate_by_flag(self, feature: str) -> float:
        """Get error rate for specific feature flag."""
        # Placeholder for error rate tracking
        return 0.0

    def _monitor_flag_performance(self, feature: str) -> Dict[str, Any]:
        """Monitor performance of feature flag."""
        # Placeholder for performance monitoring
        return {}

    def run(self, args):
        """Run the CLI with given arguments."""
        try:
            # Handle constitution rule management commands first
            if self._handle_constitution_commands(args):
                return 0

            # Handle backend management commands
            if self._handle_backend_commands(args):
                return 0

            # Handle validation service startup
            if args.start_validation_service:
                return self._handle_start_validation_service(args)

            # Handle prompt validation
            if args.validate_prompt:
                return self._handle_prompt_validation(args)

            if args.file:
                # Validate single file
                result = self.validate_file(args.file, args)
                if "error" not in result:
                    report = self.generate_enhanced_report({"files": {args.file: result}}, args.format)
                    safe_print(report)
                else:
                    safe_print(f"Error: {result['error']}")
                    return 1

            elif args.directory:
                # Validate directory
                results = self.validate_directory(args.directory, args)
                report = self.generate_enhanced_report(results, args.format)
                safe_print(report)

                # Save report if requested
                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(report)
                    safe_print(f"Report saved to {args.output}")

            else:
                # Check if any constitution commands were used
                constitution_commands = [args.list_rules, args.enable_rule, args.disable_rule,
                                       args.rule_stats, args.export_rules, args.rules_by_category, args.search_rules]
                if any(constitution_commands):
                    safe_print("Constitution rule management commands completed.")
                    return 0
                else:
                    safe_print("Please specify either --file or --directory, or use a constitution rule command")
                    return 1

            return 0

        except KeyboardInterrupt:
            error_result = self.handle_error(KeyboardInterrupt("User interrupted operation"),
                                           context={"operation": "main_validation"})
            safe_print(f"\n{error_result.get('user_message', 'Validation interrupted by user')}")
            return 1
        except Exception as e:
            error_result = self.handle_error(e, context={"operation": "main_validation"})
            safe_print(f"Error: {error_result.get('user_message', str(e))}")
            return 1
        finally:
            # Stop performance monitoring
            self.performance_monitor.stop_monitoring()

    def _handle_prompt_validation(self, args):
        """Handle prompt validation using the API service."""
        try:
            import requests

            # Use API service instead of direct hooks
            validation_url = "http://localhost:5000/validate"

            payload = {
                'prompt': args.validate_prompt,
                'file_type': args.prompt_file_type or 'python',
                'task_type': args.prompt_task_type or 'general'
            }

            safe_print(f"Validating prompt against {validation_url}...")
            response = requests.post(validation_url, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()

                if result['valid']:
                    safe_print(f"✅ Prompt validated against {result['total_rules_checked']} constitution rules")
                    if result['recommendations']:
                        safe_print("Recommendations:")
                        for rec in result['recommendations']:
                            safe_print(f"  • {rec}")
                    return 0
                else:
                    safe_print(f"❌ Prompt validation failed ({len(result['violations'])} violations)")
                    for violation in result['violations']:
                        rule_id = violation.get('rule_id', 'Unknown')
                        message = violation.get('message', 'No message')
                        safe_print(f"  {rule_id}: {message}")
                    return 1
            else:
                safe_print(f"❌ Validation service error: {response.status_code}")
                safe_print(f"Response: {response.text}")
                return 1

        except requests.exceptions.ConnectionError:
            safe_print("❌ Validation service not running. Start with: python tools/start_validation_service.py")
            return 1
        except Exception as e:
            safe_print(f"Error during prompt validation: {e}")
            return 1

    def _handle_start_validation_service(self, args):
        """Start the constitution validation service."""
        try:
            import subprocess
            import os
            from pathlib import Path

            safe_print(f"Starting Constitution Validation Service on port {args.service_port}...")
            safe_print("This service enforces all 293 ZeroUI constitution rules before AI code generation.")
            safe_print("Press Ctrl+C to stop the service.")

            # Start the service in a subprocess
            service_script = Path(__file__).parent / "start_validation_service.py"

            env = os.environ.copy()
            env['VALIDATION_SERVICE_PORT'] = str(args.service_port)

            process = subprocess.Popen(
                [sys.executable, str(service_script)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for service to start
            import time
            time.sleep(2)

            # Check if service started successfully
            import requests
            try:
                response = requests.get(f"http://localhost:{args.service_port}/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    safe_print(f"✅ Service started successfully!")
                    safe_print(f"Available integrations: {', '.join(health_data.get('integrations', []))}")
                    safe_print(f"Status: {health_data.get('status', 'unknown')}")
                    safe_print(f"Service URL: http://localhost:{args.service_port}")
                    safe_print("Use Ctrl+C to stop the service.")

                    # Keep the service running
                    try:
                        process.wait()
                    except KeyboardInterrupt:
                        safe_print("\nStopping validation service...")
                        process.terminate()
                        process.wait()
                        safe_print("Service stopped.")
                        return 0
                else:
                    safe_print(f"❌ Service health check failed: {response.status_code}")
                    return 1
            except requests.exceptions.ConnectionError:
                safe_print("❌ Service failed to start or is not responding")
                stdout, stderr = process.communicate(timeout=5)
                if stdout:
                    safe_print(f"Service output: {stdout}")
                if stderr:
                    safe_print(f"Service errors: {stderr}")
                return 1

        except Exception as e:
            safe_print(f"Error starting validation service: {e}")
            return 1


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
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument(
        "--file", "-f",
        help="Validate a single Python file"
    )
    input_group.add_argument(
        "--directory", "-d",
        help="Validate all Python files in a directory"
    )

    # Pre-implementation validation options
    prompt_group = parser.add_argument_group('Pre-Implementation Validation')
    prompt_group.add_argument(
        "--validate-prompt",
        help="Validate prompt before code generation"
    )
    prompt_group.add_argument(
        "--prompt-file-type",
        choices=['python', 'typescript'],
        help="Target file type for prompt validation"
    )
    prompt_group.add_argument(
        "--prompt-task-type",
        help="Task type for prompt validation (storage, logging, api, etc.)"
    )
    prompt_group.add_argument(
        "--start-validation-service",
        action="store_true",
        help="Start the constitution validation service"
    )
    prompt_group.add_argument(
        "--service-port",
        type=int,
        default=5000,
        help="Port for validation service (default: 5000)"
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
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors in console output"
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

    # Constitution rule management options
    constitution_group = parser.add_argument_group('Constitution Rule Management')
    constitution_group.add_argument(
        "--list-rules",
        action="store_true",
        help="List all constitution rules with their status"
    )
    constitution_group.add_argument(
        "--enable-rule",
        type=int,
        metavar="RULE_NUMBER",
        help="Enable a specific constitution rule"
    )
    constitution_group.add_argument(
        "--disable-rule",
        type=int,
        metavar="RULE_NUMBER",
        help="Disable a specific constitution rule"
    )
    constitution_group.add_argument(
        "--disable-reason",
        help="Reason for disabling a rule (use with --disable-rule)"
    )
    constitution_group.add_argument(
        "--rule-stats",
        action="store_true",
        help="Show constitution rule statistics"
    )
    constitution_group.add_argument(
        "--export-rules",
        action="store_true",
        help="Export all constitution rules to JSON"
    )
    constitution_group.add_argument(
        "--export-enabled-only",
        action="store_true",
        help="Export only enabled rules (use with --export-rules)"
    )
    constitution_group.add_argument(
        "--rules-by-category",
        metavar="CATEGORY",
        help="List rules by category (basic_work, system_design, etc.)"
    )
    constitution_group.add_argument(
        "--search-rules",
        metavar="SEARCH_TERM",
        help="Search rules by title or content"
    )

    # Backend management options
    backend_group = parser.add_argument_group('Backend Management')
    backend_group.add_argument(
        "--backend",
        choices=["sqlite", "json", "auto"],
        default="auto",
        help="Select backend for operation (default: auto)"
    )
    backend_group.add_argument(
        "--switch-backend",
        choices=["sqlite", "json"],
        metavar="BACKEND",
        help="Switch default backend"
    )
    backend_group.add_argument(
        "--sync-backends",
        action="store_true",
        help="Manually trigger backend synchronization"
    )
    backend_group.add_argument(
        "--migrate",
        choices=["sqlite-to-json", "json-to-sqlite"],
        metavar="MIGRATION",
        help="Migrate data between backends"
    )
    backend_group.add_argument(
        "--verify-sync",
        action="store_true",
        help="Verify that backends are synchronized"
    )
    backend_group.add_argument(
        "--verify-consistency",
        action="store_true",
        help="Verify rules consistency across Markdown, DB, JSON export, and config"
    )
    backend_group.add_argument(
        "--backend-status",
        action="store_true",
        help="Show status of all backends"
    )
    backend_group.add_argument(
        "--repair-sync",
        action="store_true",
        help="Repair synchronization between backends"
    )
    backend_group.add_argument(
        "--migrate-config",
        action="store_true",
        help="Migrate configuration from v1.0 to v2.0 format"
    )
    backend_group.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate v2.0 configuration format"
    )
    backend_group.add_argument(
        "--config-info",
        action="store_true",
        help="Show configuration information and migration status"
    )
    backend_group.add_argument(
        "--rebuild-from-markdown",
        action="store_true",
        help="Rebuild SQLite and JSON databases from Markdown (single source of truth)"
    )

    args = parser.parse_args()

    # Apply color setting to reporter and console outputs
    try:
        from validator.reporter import set_use_color
        set_use_color(not args.no_color)
    except Exception:
        pass

    # Create and run CLI
    cli = EnhancedCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
