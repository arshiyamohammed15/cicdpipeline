#!/usr/bin/env python3
"""
ZeroUI 2.0 Rule Manager
Comprehensive rule management across all 5 sources: Markdown, Database, JSON Export, Config, and Hooks

This tool provides unified rule management capabilities to enable/disable rules
across all sources in the ZeroUI 2.0 constitution system.

Usage:
    python tools/rule_manager.py --enable-rule 150
    python tools/rule_manager.py --disable-rule 150 --reason "Too restrictive"
    python tools/rule_manager.py --enable-all
    python tools/rule_manager.py --disable-all --reason "Maintenance mode"
    python tools/rule_manager.py --status
    python tools/rule_manager.py --sync-all
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.constitution.sync_manager import get_sync_manager
from config.constitution.config_manager import get_constitution_manager

# Import hook configuration manager
try:
    from validator.hook_config_manager import HookConfigManager, HookCategory
except ImportError:
    # Fallback for testing environment
    HookConfigManager = None
    HookCategory = None


@dataclass
class RuleStatus:
    """Represents the status of a rule across all sources"""
    rule_number: int
    markdown_exists: bool
    database_enabled: Optional[bool]
    json_export_enabled: Optional[bool]
    config_enabled: Optional[bool]
    hooks_enabled: Optional[bool]  # NEW: Pre-implementation hooks status
    consistent: bool
    sources: Dict[str, Any]


class RuleManager:
    """
    Comprehensive rule manager for ZeroUI 2.0 constitution system.
    Manages rules across all 5 sources: Markdown, Database, JSON Export, Config, and Hooks.
    """

    def __init__(self):
        """Initialize the rule manager with all required components."""
        self.sync_manager = get_sync_manager()
        self.constitution_manager = get_constitution_manager()
        self.project_root = Path(__file__).parent.parent

        # Define source paths
        self.markdown_path = self.project_root / "docs" / "architecture" / "ZeroUI2.0_Master_Constitution.md"
        self.database_path = self.project_root / "config" / "constitution_rules.db"
        self.json_export_path = self.project_root / "config" / "constitution_rules.json"
        self.config_path = self.project_root / "config" / "constitution_config.json"
        self.hook_config_path = self.project_root / "config" / "hook_config.json"

        # Initialize hook configuration manager
        self.hook_manager = HookConfigManager(str(self.hook_config_path)) if HookConfigManager else None

    def _get_rule_category_for_hooks(self, rule_number: int) -> Optional[str]:
        """Map rule number to HookCategory enum value."""
        if not HookCategory:
            return None

        if 1 <= rule_number <= 75:
            return HookCategory.BASIC_WORK.value
        elif 76 <= rule_number <= 99:
            return HookCategory.CODE_REVIEW.value
        elif 100 <= rule_number <= 131:
            return HookCategory.SECURITY_PRIVACY.value
        elif 132 <= rule_number <= 149:
            return HookCategory.LOGGING.value
        elif 150 <= rule_number <= 180:
            return HookCategory.ERROR_HANDLING.value
        elif 181 <= rule_number <= 215:
            return HookCategory.TYPESCRIPT.value
        elif 216 <= rule_number <= 228:
            return HookCategory.STORAGE_GOVERNANCE.value
        elif 232 <= rule_number <= 252:
            return HookCategory.GSMD.value
        elif 253 <= rule_number <= 280:
            return HookCategory.SIMPLE_READABILITY.value
        return None

    def _get_hook_rule_status(self, rule_number: int) -> Optional[bool]:
        """Get rule status from hook configuration."""
        if not self.hook_manager:
            return None
        try:
            return self.hook_manager.is_rule_enabled(rule_number)
        except Exception as e:
            print(f"Warning: Could not get hook status for rule {rule_number}: {e}")
            return None

    def _verify_consistency_across_all_sources(self, rule_number: int) -> Dict[str, Any]:
        """
        Enhanced consistency verification for all 5 sources including hooks.

        Args:
            rule_number: Rule number to verify

        Returns:
            Dictionary with consistency information across all sources
        """
        try:
            # Get rule status from all 5 sources
            sources_status = {
                "markdown": {"exists": False, "enabled": None},
                "database": {"exists": False, "enabled": None},
                "json_export": {"exists": False, "enabled": None},
                "config": {"exists": False, "enabled": None},
                "hooks": {"exists": False, "enabled": None}
            }

            # Check markdown (read-only, always exists if rule is defined)
            try:
                all_rules = self.constitution_manager.get_all_rules()
                markdown_exists = any(rule["rule_number"] == rule_number for rule in all_rules)
                sources_status["markdown"]["exists"] = markdown_exists
                sources_status["markdown"]["enabled"] = None  # Markdown doesn't track enabled status
            except Exception as e:
                print(f"Warning: Could not check markdown for rule {rule_number}: {e}")

            # Check database
            try:
                db_rule = self.constitution_manager.get_rule_by_number(rule_number)
                if db_rule:
                    sources_status["database"]["exists"] = True
                    sources_status["database"]["enabled"] = db_rule.get("enabled", True)
            except Exception as e:
                print(f"Warning: Could not check database for rule {rule_number}: {e}")

            # Check JSON export
            try:
                if self.json_export_path.exists():
                    with open(self.json_export_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    rule_key = str(rule_number)
                    if "rules" in json_data and rule_key in json_data["rules"]:
                        sources_status["json_export"]["exists"] = True
                        sources_status["json_export"]["enabled"] = json_data["rules"][rule_key].get("enabled", True)
            except Exception as e:
                print(f"Warning: Could not check JSON export for rule {rule_number}: {e}")

            # Check config
            try:
                if self.config_path.exists():
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    rule_key = str(rule_number)
                    if "rules" in config_data and rule_key in config_data["rules"]:
                        sources_status["config"]["exists"] = True
                        enabled_value = config_data["rules"][rule_key].get("enabled", True)
                        # Convert integer 0/1 to boolean if needed
                        if isinstance(enabled_value, int):
                            sources_status["config"]["enabled"] = bool(enabled_value)
                        else:
                            sources_status["config"]["enabled"] = enabled_value
            except Exception as e:
                print(f"Warning: Could not check config for rule {rule_number}: {e}")

            # Check hooks
            try:
                if self.hook_manager:
                    hook_status = self._get_hook_rule_status(rule_number)
                    if hook_status is not None:
                        sources_status["hooks"]["exists"] = True
                        sources_status["hooks"]["enabled"] = hook_status
            except Exception as e:
                print(f"Warning: Could not check hooks for rule {rule_number}: {e}")

            # Determine consistency
            enabled_values = [s["enabled"] for s in sources_status.values() if s["enabled"] is not None]
            consistent = len(set(enabled_values)) <= 1 if enabled_values else True

            return {
                "rule_number": rule_number,
                "sources_status": sources_status,
                "consistent": consistent,
                "enabled_values": enabled_values,
                "majority_enabled": self._get_majority_enabled_status(enabled_values)
            }

        except Exception as e:
            return {
                "rule_number": rule_number,
                "error": str(e),
                "consistent": False,
                "sources_status": {},
                "enabled_values": [],
                "majority_enabled": None
            }

    def _get_majority_enabled_status(self, enabled_values: List[bool]) -> Optional[bool]:
        """Determine majority enabled status from list of boolean values."""
        if not enabled_values:
            return None

        # Normalize values to boolean (handle 0/1 integers)
        normalized_values = []
        for v in enabled_values:
            if isinstance(v, int):
                normalized_values.append(bool(v))
            elif isinstance(v, bool):
                normalized_values.append(v)
            else:
                # Skip non-boolean values
                continue

        if not normalized_values:
            return None

        true_count = sum(1 for v in normalized_values if v is True)
        false_count = sum(1 for v in normalized_values if v is False)

        if true_count > false_count:
            return True
        elif false_count > true_count:
            return False
        else:
            # Tie - return None to indicate no clear majority
            return None

    def get_rule_status(self, rule_number: int) -> RuleStatus:
        """
        Get the status of a rule across all sources including hooks.

        Args:
            rule_number: The rule number to check

        Returns:
            RuleStatus object with information about the rule across all sources
        """
        try:
            # Use enhanced consistency verification for all 5 sources
            consistency_info = self._verify_consistency_across_all_sources(rule_number)

            if "error" in consistency_info:
                return RuleStatus(
                    rule_number=rule_number,
                    markdown_exists=False,
                    database_enabled=None,
                    json_export_enabled=None,
                    config_enabled=None,
                    hooks_enabled=None,
                    consistent=False,
                    sources={"error": consistency_info["error"]}
                )

            sources_status = consistency_info["sources_status"]

            return RuleStatus(
                rule_number=rule_number,
                markdown_exists=sources_status["markdown"]["exists"],
                database_enabled=sources_status["database"]["enabled"],
                json_export_enabled=sources_status["json_export"]["enabled"],
                config_enabled=sources_status["config"]["enabled"],
                hooks_enabled=sources_status["hooks"]["enabled"],
                consistent=consistency_info["consistent"],
                sources={
                    "sources_status": sources_status,
                    "enabled_values": consistency_info["enabled_values"],
                    "majority_enabled": consistency_info["majority_enabled"]
                }
            )

        except Exception as e:
            print(f"Error getting rule status: {e}")
            return RuleStatus(
                rule_number=rule_number,
                markdown_exists=False,
                database_enabled=None,
                json_export_enabled=None,
                config_enabled=None,
                hooks_enabled=None,
                consistent=False,
                sources={"error": str(e)}
            )

    def enable_rule(self, rule_number: int, config_data: Optional[Dict[str, Any]] = None,
                   sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Enable a rule across specified sources.

        Args:
            rule_number: Rule number to enable
            config_data: Optional configuration data
            sources: List of sources to update (default: all)

        Returns:
            Dictionary with results for each source
        """
        if sources is None:
            sources = ["database", "config", "json_export", "hooks"]

        results = {}

        try:
            # Enable in database
            if "database" in sources:
                try:
                    success = self.constitution_manager.enable_rule(rule_number, config_data)
                    results["database"] = {"success": success, "message": "Enabled in database" if success else "Failed to enable in database"}
                except Exception as e:
                    results["database"] = {"success": False, "message": f"Database error: {e}"}

            # Enable in config
            if "config" in sources:
                try:
                    success = self.constitution_manager.enable_rule(rule_number, config_data)
                    results["config"] = {"success": success, "message": "Enabled in config" if success else "Failed to enable in config"}
                except Exception as e:
                    results["config"] = {"success": False, "message": f"Config error: {e}"}

            # Enable in JSON export
            if "json_export" in sources:
                try:
                    # Update JSON export file
                    if self.json_export_path.exists():
                        with open(self.json_export_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)

                        rule_key = str(rule_number)
                        if "rules" in json_data and rule_key in json_data["rules"]:
                            json_data["rules"][rule_key]["enabled"] = True
                            if config_data:
                                json_data["rules"][rule_key]["config"].update(config_data)

                            with open(self.json_export_path, 'w', encoding='utf-8') as f:
                                json.dump(json_data, f, indent=2, ensure_ascii=False)

                            results["json_export"] = {"success": True, "message": "Enabled in JSON export"}
                        else:
                            results["json_export"] = {"success": False, "message": f"Rule {rule_number} not found in JSON export"}
                    else:
                        results["json_export"] = {"success": False, "message": "JSON export file not found"}
                except Exception as e:
                    results["json_export"] = {"success": False, "message": f"JSON export error: {e}"}

            # Enable in hooks
            if "hooks" in sources:
                try:
                    if self.hook_manager:
                        reason = config_data.get('reason') if config_data else None
                        success = self.hook_manager.enable_rule(rule_number, reason)
                        results["hooks"] = {
                            "success": success,
                            "message": "Enabled in hooks" if success else "Failed to enable in hooks"
                        }
                    else:
                        results["hooks"] = {"success": False, "message": "Hook manager not available"}
                except Exception as e:
                    results["hooks"] = {"success": False, "message": f"Hooks error: {e}"}

            # Note: Markdown is read-only for rule content, but we can't change enable/disable there
            if "markdown" in sources:
                results["markdown"] = {"success": False, "message": "Markdown is read-only for rule content"}

            return results

        except Exception as e:
            return {"error": f"Failed to enable rule {rule_number}: {e}"}

    def disable_rule(self, rule_number: int, reason: str = "",
                    sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Disable a rule across specified sources.

        Args:
            rule_number: Rule number to disable
            reason: Reason for disabling
            sources: List of sources to update (default: all)

        Returns:
            Dictionary with results for each source
        """
        if sources is None:
            sources = ["database", "config", "json_export", "hooks"]

        results = {}

        try:
            # Disable in database
            if "database" in sources:
                try:
                    success = self.constitution_manager.disable_rule(rule_number, reason)
                    results["database"] = {"success": success, "message": "Disabled in database" if success else "Failed to disable in database"}
                except Exception as e:
                    results["database"] = {"success": False, "message": f"Database error: {e}"}

            # Disable in config
            if "config" in sources:
                try:
                    success = self.constitution_manager.disable_rule(rule_number, reason)
                    results["config"] = {"success": success, "message": "Disabled in config" if success else "Failed to disable in config"}
                except Exception as e:
                    results["config"] = {"success": False, "message": f"Config error: {e}"}

            # Disable in JSON export
            if "json_export" in sources:
                try:
                    # Update JSON export file
                    if self.json_export_path.exists():
                        with open(self.json_export_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)

                        rule_key = str(rule_number)
                        if "rules" in json_data and rule_key in json_data["rules"]:
                            json_data["rules"][rule_key]["enabled"] = False
                            json_data["rules"][rule_key]["config"]["disabled_reason"] = reason
                            json_data["rules"][rule_key]["config"]["disabled_at"] = datetime.now().isoformat()

                            with open(self.json_export_path, 'w', encoding='utf-8') as f:
                                json.dump(json_data, f, indent=2, ensure_ascii=False)

                            results["json_export"] = {"success": True, "message": "Disabled in JSON export"}
                        else:
                            results["json_export"] = {"success": False, "message": f"Rule {rule_number} not found in JSON export"}
                    else:
                        results["json_export"] = {"success": False, "message": "JSON export file not found"}
                except Exception as e:
                    results["json_export"] = {"success": False, "message": f"JSON export error: {e}"}

            # Disable in hooks
            if "hooks" in sources:
                try:
                    if self.hook_manager:
                        success = self.hook_manager.disable_rule(rule_number, reason)
                        results["hooks"] = {
                            "success": success,
                            "message": "Disabled in hooks" if success else "Failed to disable in hooks"
                        }
                    else:
                        results["hooks"] = {"success": False, "message": "Hook manager not available"}
                except Exception as e:
                    results["hooks"] = {"success": False, "message": f"Hooks error: {e}"}

            # Note: Markdown is read-only for rule content
            if "markdown" in sources:
                results["markdown"] = {"success": False, "message": "Markdown is read-only for rule content"}

            return results

        except Exception as e:
            return {"error": f"Failed to disable rule {rule_number}: {e}"}

    def enable_all_rules(self, config_data: Optional[Dict[str, Any]] = None,
                        sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Enable all rules across specified sources.

        Args:
            config_data: Optional configuration data
            sources: List of sources to update (default: all)

        Returns:
            Dictionary with results
        """
        try:
            # Get all rules from database
            all_rules = self.constitution_manager.get_all_rules()

            if not all_rules:
                return {"error": "No rules found"}

            results = {"total_rules": len(all_rules), "enabled": 0, "failed": 0, "details": []}

            for rule in all_rules:
                rule_number = rule["rule_number"]
                result = self.enable_rule(rule_number, config_data, sources)

                if all(r.get("success", False) for r in result.values() if isinstance(r, dict)):
                    results["enabled"] += 1
                else:
                    results["failed"] += 1

                results["details"].append({
                    "rule_number": rule_number,
                    "result": result
                })

            return results

        except Exception as e:
            return {"error": f"Failed to enable all rules: {e}"}

    def disable_all_rules(self, reason: str = "",
                        sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Disable all rules across specified sources.

        Args:
            reason: Reason for disabling
            sources: List of sources to update (default: all)

        Returns:
            Dictionary with results
        """
        try:
            # Get all rules from database
            all_rules = self.constitution_manager.get_all_rules()

            if not all_rules:
                return {"error": "No rules found"}

            results = {"total_rules": len(all_rules), "disabled": 0, "failed": 0, "details": []}

            for rule in all_rules:
                rule_number = rule["rule_number"]
                result = self.disable_rule(rule_number, reason, sources)

                if all(r.get("success", False) for r in result.values() if isinstance(r, dict)):
                    results["disabled"] += 1
                else:
                    results["failed"] += 1

                results["details"].append({
                    "rule_number": rule_number,
                    "result": result
                })

            return results

        except Exception as e:
            return {"error": f"Failed to disable all rules: {e}"}

    def sync_all_sources(self) -> Dict[str, Any]:
        """
        Synchronize all 5 sources (Markdown, Database, JSON Export, Config, Hooks) to ensure consistency.

        Returns:
            Dictionary with sync results
        """
        try:
            # Get all rules to check
            all_rules = self.constitution_manager.get_all_rules()
            if not all_rules:
                return {"error": "No rules found to sync"}

            inconsistent_rules = []
            fixed_count = 0
            sync_details = []

            # Check each rule for consistency across all 5 sources
            for rule in all_rules:
                rule_number = rule["rule_number"]
                consistency_info = self._verify_consistency_across_all_sources(rule_number)

                if not consistency_info.get("consistent", True):
                    inconsistent_rules.append(consistency_info)

                    # Attempt to fix inconsistency using majority vote
                    majority_enabled = consistency_info.get("majority_enabled")
                    if majority_enabled is not None:
                        try:
                            if majority_enabled:
                                # Enable in all sources (except markdown which is read-only)
                                result = self.enable_rule(rule_number, sources=["database", "config", "json_export", "hooks"])
                            else:
                                # Disable in all sources (except markdown which is read-only)
                                result = self.disable_rule(rule_number, "Auto-sync: Majority disabled",
                                                        sources=["database", "config", "json_export", "hooks"])

                            # Check if sync was successful
                            if all(r.get("success", False) for r in result.values() if isinstance(r, dict)):
                                fixed_count += 1
                                sync_details.append({
                                    "rule_number": rule_number,
                                    "action": "enabled" if majority_enabled else "disabled",
                                    "result": "success"
                                })
                            else:
                                sync_details.append({
                                    "rule_number": rule_number,
                                    "action": "enabled" if majority_enabled else "disabled",
                                    "result": "failed",
                                    "details": result
                                })
                        except Exception as e:
                            sync_details.append({
                                "rule_number": rule_number,
                                "action": "sync",
                                "result": "error",
                                "error": str(e)
                            })
                    else:
                        # No clear majority - log as unresolved
                        sync_details.append({
                            "rule_number": rule_number,
                            "action": "sync",
                            "result": "unresolved",
                            "reason": "No clear majority vote"
                        })

            if not inconsistent_rules:
                return {
                    "success": True,
                    "message": "All sources are already consistent",
                    "total_rules": len(all_rules),
                    "inconsistent_rules": 0,
                    "fixed_count": 0,
                    "sync_details": []
                }
            else:
                return {
                    "success": True,
                    "message": f"Sync completed: {fixed_count} rules fixed, {len(inconsistent_rules) - fixed_count} unresolved",
                    "total_rules": len(all_rules),
                    "inconsistent_rules": len(inconsistent_rules),
                    "fixed_count": fixed_count,
                    "unresolved_count": len(inconsistent_rules) - fixed_count,
                    "sync_details": sync_details,
                    "inconsistent_details": inconsistent_rules
                }

        except Exception as e:
            return {"error": f"Failed to sync sources: {e}"}

    def get_all_rule_statuses(self) -> List[RuleStatus]:
        """
        Get status of all rules across all sources.

        Returns:
            List of RuleStatus objects
        """
        try:
            all_rules = self.constitution_manager.get_all_rules()

            statuses = []
            for rule in all_rules:
                status = self.get_rule_status(rule["rule_number"])
                statuses.append(status)

            return statuses

        except Exception as e:
            print(f"Error getting all rule statuses: {e}")
            return []


def print_rule_status(status: RuleStatus):
    """Print formatted rule status."""
    print(f"\nRule {status.rule_number}:")
    print(f"  Markdown exists: {'Yes' if status.markdown_exists else 'No'}")
    print(f"  Database enabled: {status.database_enabled}")
    print(f"  JSON export enabled: {status.json_export_enabled}")
    print(f"  Config enabled: {status.config_enabled}")
    print(f"  Hooks enabled: {status.hooks_enabled}")
    print(f"  Consistent: {'Yes' if status.consistent else 'No'}")

    if status.sources:
        print(f"  Sources: {status.sources}")


def print_results(results: Dict[str, Any], operation: str):
    """Print formatted results."""
    print(f"\n{operation.upper()} RESULTS:")
    print("=" * 50)

    if "error" in results:
        print(f"Error: {results['error']}")
        return

    if "total_rules" in results:
        print(f"Total rules: {results['total_rules']}")
        print(f"Successful: {results.get('enabled', results.get('disabled', 0))}")
        print(f"Failed: {results.get('failed', 0)}")

        if results.get("details"):
            print(f"\nDetails (showing first 5):")
            for detail in results["details"][:5]:
                rule_num = detail.get("rule_number")
                result = detail.get("result", {})
                print(f"  Rule {rule_num}: {result}")

            if len(results["details"]) > 5:
                print(f"  ... and {len(results['details']) - 5} more")
    else:
        if "success" in results:
            success = results.get("success", False)
            message = results.get("message", "Unknown")
            status = "OK" if success else "FAIL"
            print(f"  Result: {status} {message}")

            if "fixed_count" in results:
                print(f"  Fixed inconsistencies: {results['fixed_count']}")
        else:
            for source, result in results.items():
                if isinstance(result, dict):
                    success = result.get("success", False)
                    message = result.get("message", "Unknown")
                    status = "OK" if success else "FAIL"
                    print(f"  {source}: {status} {message}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description='ZeroUI 2.0 Rule Manager - Manage rules across all sources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/rule_manager.py --enable-rule 150
  python tools/rule_manager.py --disable-rule 150 --reason "Too restrictive"
  python tools/rule_manager.py --enable-all
  python tools/rule_manager.py --disable-all --reason "Maintenance mode"
  python tools/rule_manager.py --status
  python tools/rule_manager.py --sync-all
  python tools/rule_manager.py --status-rule 150
        """
    )

    # Rule management commands
    parser.add_argument('--enable-rule', type=int, metavar='RULE_NUMBER',
                       help='Enable a specific rule')
    parser.add_argument('--disable-rule', type=int, metavar='RULE_NUMBER',
                       help='Disable a specific rule')
    parser.add_argument('--enable-all', action='store_true',
                       help='Enable all rules')
    parser.add_argument('--disable-all', action='store_true',
                       help='Disable all rules')
    parser.add_argument('--reason', help='Reason for disabling rules')
    parser.add_argument('--config-data', help='JSON configuration data for enabling rules')

    # Status and sync commands
    parser.add_argument('--status', action='store_true',
                       help='Show status of all rules')
    parser.add_argument('--status-rule', type=int, metavar='RULE_NUMBER',
                       help='Show status of a specific rule')
    parser.add_argument('--sync-all', action='store_true',
                       help='Synchronize all sources')

    # Source selection
    parser.add_argument('--sources', nargs='+',
                       choices=['markdown', 'database', 'json_export', 'config', 'hooks'],
                       help='Specify which sources to update (default: all except markdown)')

    args = parser.parse_args()

    # Create rule manager
    try:
        rule_manager = RuleManager()
    except Exception as e:
        print(f"Error initializing rule manager: {e}")
        return 1

    # Handle commands
    try:
        if args.enable_rule:
            config_data = None
            if args.config_data:
                try:
                    config_data = json.loads(args.config_data)
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in --config-data: {e}")
                    return 1

            results = rule_manager.enable_rule(args.enable_rule, config_data, args.sources)
            print_results(results, f"Enable Rule {args.enable_rule}")

        elif args.disable_rule:
            reason = args.reason or "Disabled via rule manager"
            results = rule_manager.disable_rule(args.disable_rule, reason, args.sources)
            print_results(results, f"Disable Rule {args.disable_rule}")

        elif args.enable_all:
            config_data = None
            if args.config_data:
                try:
                    config_data = json.loads(args.config_data)
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in --config-data: {e}")
                    return 1

            results = rule_manager.enable_all_rules(config_data, args.sources)
            print_results(results, "Enable All Rules")

        elif args.disable_all:
            reason = args.reason or "Disabled via rule manager"
            results = rule_manager.disable_all_rules(reason, args.sources)
            print_results(results, "Disable All Rules")

        elif args.status:
            statuses = rule_manager.get_all_rule_statuses()
            print(f"\nRULE STATUS SUMMARY:")
            print("=" * 50)
            print(f"Total rules: {len(statuses)}")

            consistent_count = sum(1 for s in statuses if s.consistent)
            print(f"Consistent rules: {consistent_count}")
            print(f"Inconsistent rules: {len(statuses) - consistent_count}")

            if len(statuses) - consistent_count > 0:
                print(f"\nInconsistent rules (showing first 10):")
                inconsistent = [s for s in statuses if not s.consistent][:10]
                for status in inconsistent:
                    print_rule_status(status)

        elif args.status_rule:
            status = rule_manager.get_rule_status(args.status_rule)
            print_rule_status(status)

        elif args.sync_all:
            results = rule_manager.sync_all_sources()
            print_results(results, "Sync All Sources")

        else:
            parser.print_help()

    except Exception as e:
        print(f"Error executing command: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
