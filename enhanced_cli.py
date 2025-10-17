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
from pathlib import Path
from typing import Dict, List, Any, Optional

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
            safe_print(f"Error validating {file_path}: {e}")
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
            safe_print(f"No Python files found in {directory_path}")
            return {"files": [], "summary": {}}
        
        safe_print(f"Validating {len(python_files)} Python files...")
        
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
                    safe_print(f"[{compliance:5.1f}%] {file_path.name}: {file_result['result'].total_violations} violations")
            
            except Exception as e:
                safe_print(f"[ERROR] {file_path}: {e}")
        
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
                safe_print(f"Error: Constitution rule manager not available: {e}")
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
            safe_print(f"Error handling constitution command: {e}")
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
            
        except Exception as e:
            safe_print(f"Error handling backend command: {e}")
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
    
    def run(self, args):
        """Run the CLI with given arguments."""
        try:
            # Handle constitution rule management commands first
            if self._handle_constitution_commands(args):
                return 0
            
            # Handle backend management commands
            if self._handle_backend_commands(args):
                return 0
            
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
            safe_print("\nValidation interrupted by user")
            return 1
        except Exception as e:
            safe_print(f"Error: {e}")
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
    input_group = parser.add_mutually_exclusive_group(required=False)
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
    
    args = parser.parse_args()
    
    # Create and run CLI
    cli = EnhancedCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
