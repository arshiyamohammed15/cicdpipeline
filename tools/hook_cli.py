#!/usr/bin/env python3
"""
Hook Management CLI for ZeroUI2.0 Pre-Implementation Hooks

This CLI provides commands to enable/disable individual pre-implementation hooks
and manage hook configurations.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validator.hook_config_manager import HookConfigManager, HookCategory, HookStatus


class HookCLI:
    """
    CLI for managing pre-implementation hooks.
    """
    
    def __init__(self):
        """Initialize the hook CLI."""
        self.config_manager = HookConfigManager()
    
    def list_hooks(self, args) -> int:
        """List all hooks with their status."""
        try:
            if args.category:
                # List hooks in a specific category
                try:
                    category = HookCategory(args.category)
                    status = self.config_manager.get_category_status(category)
                    
                    print(f"\n📋 {status['name']} ({category.value})")
                    print(f"Status: {status['status'].upper()}")
                    print(f"Description: {status.get('description', 'No description')}")
                    print(f"Rule Count: {status['rule_count']}")
                    
                    if 'enabled_at' in status:
                        print(f"Enabled: {status['enabled_at']}")
                    if 'disabled_at' in status:
                        print(f"Disabled: {status['disabled_at']}")
                    if 'enabled_reason' in status:
                        print(f"Reason: {status['enabled_reason']}")
                    if 'disabled_reason' in status:
                        print(f"Reason: {status['disabled_reason']}")
                    
                    return 0
                    
                except ValueError:
                    print(f"Error: Invalid category '{args.category}'")
                    print("Available categories:")
                    for cat in HookCategory:
                        print(f"  - {cat.value}")
                    return 1
            
            elif args.rule:
                # List specific rule
                rule_id = args.rule
                status = self.config_manager.get_rule_status(rule_id)
                category = self.config_manager._get_rule_category(rule_id)
                
                print(f"\n🔧 Rule {rule_id}")
                print(f"Status: {status.value.upper()}")
                print(f"Category: {category.value if category else 'Unknown'}")
                
                return 0
            
            else:
                # List all categories
                categories = self.config_manager.list_all_categories()
                
                print("\n📋 Hook Categories")
                print("=" * 50)
                
                for cat_name, cat_info in categories.items():
                    status_icon = "✅" if cat_info['status'] == 'enabled' else "❌"
                    print(f"{status_icon} {cat_info['name']} ({cat_name})")
                    print(f"   Status: {cat_info['status'].upper()}")
                    print(f"   Rules: {cat_info['rule_count']}")
                    if 'enabled_at' in cat_info:
                        print(f"   Enabled: {cat_info['enabled_at']}")
                    if 'disabled_at' in cat_info:
                        print(f"   Disabled: {cat_info['disabled_at']}")
                    print()
                
                return 0
                
        except Exception as e:
            print(f"Error listing hooks: {e}")
            return 1
    
    def enable_hook(self, args) -> int:
        """Enable a hook or category."""
        try:
            if args.category:
                # Enable entire category
                try:
                    category = HookCategory(args.category)
                    success = self.config_manager.enable_category(category, args.reason)
                    
                    if success:
                        print(f"✅ Enabled category '{category.value}'")
                        if args.reason:
                            print(f"   Reason: {args.reason}")
                    else:
                        print(f"❌ Failed to enable category '{category.value}'")
                        return 1
                        
                except ValueError:
                    print(f"Error: Invalid category '{args.category}'")
                    return 1
            
            elif args.rule:
                # Enable specific rule
                success = self.config_manager.enable_rule(args.rule, args.reason)
                
                if success:
                    print(f"✅ Enabled rule {args.rule}")
                    if args.reason:
                        print(f"   Reason: {args.reason}")
                else:
                    print(f"❌ Failed to enable rule {args.rule}")
                    return 1
            
            else:
                print("Error: Must specify either --category or --rule")
                return 1
            
            return 0
            
        except Exception as e:
            print(f"Error enabling hook: {e}")
            return 1
    
    def disable_hook(self, args) -> int:
        """Disable a hook or category."""
        try:
            if args.category:
                # Disable entire category
                try:
                    category = HookCategory(args.category)
                    success = self.config_manager.disable_category(category, args.reason)
                    
                    if success:
                        print(f"❌ Disabled category '{category.value}'")
                        if args.reason:
                            print(f"   Reason: {args.reason}")
                    else:
                        print(f"❌ Failed to disable category '{category.value}'")
                        return 1
                        
                except ValueError:
                    print(f"Error: Invalid category '{args.category}'")
                    return 1
            
            elif args.rule:
                # Disable specific rule
                success = self.config_manager.disable_rule(args.rule, args.reason)
                
                if success:
                    print(f"❌ Disabled rule {args.rule}")
                    if args.reason:
                        print(f"   Reason: {args.reason}")
                else:
                    print(f"❌ Failed to disable rule {args.rule}")
                    return 1
            
            else:
                print("Error: Must specify either --category or --rule")
                return 1
            
            return 0
            
        except Exception as e:
            print(f"Error disabling hook: {e}")
            return 1
    
    def show_stats(self, args) -> int:
        """Show hook statistics."""
        try:
            stats = self.config_manager.get_statistics()
            
            print("\n📊 Hook Statistics")
            print("=" * 30)
            print(f"Total Rules: {stats['total_rules']}")
            print(f"Enabled Rules: {stats['enabled_rules']} ({stats['enabled_percentage']:.1f}%)")
            print(f"Disabled Rules: {stats['disabled_rules']}")
            print()
            print("Categories:")
            print(f"  Total: {stats['categories']['total']}")
            print(f"  Enabled: {stats['categories']['enabled']}")
            print(f"  Disabled: {stats['categories']['disabled']}")
            
            return 0
            
        except Exception as e:
            print(f"Error showing statistics: {e}")
            return 1
    
    def export_config(self, args) -> int:
        """Export hook configuration."""
        try:
            config = self.config_manager.export_config(args.enabled_only)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                print(f"✅ Configuration exported to {args.output}")
            else:
                print(json.dumps(config, indent=2, ensure_ascii=False))
            
            return 0
            
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return 1
    
    def reset_config(self, args) -> int:
        """Reset configuration to defaults."""
        try:
            if not args.force:
                response = input("Are you sure you want to reset all hook configurations? (y/N): ")
                if response.lower() != 'y':
                    print("Reset cancelled.")
                    return 0
            
            success = self.config_manager.reset_to_defaults()
            
            if success:
                print("✅ Configuration reset to defaults")
            else:
                print("❌ Failed to reset configuration")
                return 1
            
            return 0
            
        except Exception as e:
            print(f"Error resetting configuration: {e}")
            return 1
    
    def run(self, args) -> int:
        """Run the CLI with given arguments."""
        if args.command == 'list':
            return self.list_hooks(args)
        elif args.command == 'enable':
            return self.enable_hook(args)
        elif args.command == 'disable':
            return self.disable_hook(args)
        elif args.command == 'stats':
            return self.show_stats(args)
        elif args.command == 'export':
            return self.export_config(args)
        elif args.command == 'reset':
            return self.reset_config(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1


def main():
    """Main entry point for the hook CLI."""
    parser = argparse.ArgumentParser(
        description="Hook Management CLI for ZeroUI2.0 Pre-Implementation Hooks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list
  %(prog)s list --category basic_work
  %(prog)s list --rule 42
  %(prog)s enable --category typescript
  %(prog)s enable --rule 42 --reason "Testing specific rule"
  %(prog)s disable --category logging --reason "Too verbose for development"
  %(prog)s stats
  %(prog)s export --output hooks.json
  %(prog)s export --enabled-only --output enabled_hooks.json
  %(prog)s reset --force
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List hooks and their status')
    list_group = list_parser.add_mutually_exclusive_group()
    list_group.add_argument('--category', help='List hooks in a specific category')
    list_group.add_argument('--rule', type=int, help='List a specific rule')
    
    # Enable command
    enable_parser = subparsers.add_parser('enable', help='Enable hooks or categories')
    enable_group = enable_parser.add_mutually_exclusive_group(required=True)
    enable_group.add_argument('--category', help='Enable entire category')
    enable_group.add_argument('--rule', type=int, help='Enable specific rule')
    enable_parser.add_argument('--reason', help='Reason for enabling')
    
    # Disable command
    disable_parser = subparsers.add_parser('disable', help='Disable hooks or categories')
    disable_group = disable_parser.add_mutually_exclusive_group(required=True)
    disable_group.add_argument('--category', help='Disable entire category')
    disable_group.add_argument('--rule', type=int, help='Disable specific rule')
    disable_parser.add_argument('--reason', help='Reason for disabling')
    
    # Stats command
    subparsers.add_parser('stats', help='Show hook statistics')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export hook configuration')
    export_parser.add_argument('--enabled-only', action='store_true', 
                              help='Export only enabled hooks')
    export_parser.add_argument('--output', help='Output file (default: stdout)')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset configuration to defaults')
    reset_parser.add_argument('--force', action='store_true', 
                             help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = HookCLI()
    return cli.run(args)


if __name__ == '__main__':
    sys.exit(main())
