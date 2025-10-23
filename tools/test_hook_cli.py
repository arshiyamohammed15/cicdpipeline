#!/usr/bin/env python3
"""
Test script for Hook CLI functionality

This script demonstrates how to use the hook enable/disable CLI commands.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validator.hook_config_manager import HookConfigManager, HookCategory
from validator.pre_implementation_hooks import PreImplementationHookManager


def test_hook_configuration():
    """Test hook configuration management."""
    print("🧪 Testing Hook Configuration Management")
    print("=" * 50)
    
    # Initialize hook config manager
    config_manager = HookConfigManager()
    
    # Show initial statistics
    print("\n📊 Initial Statistics:")
    stats = config_manager.get_statistics()
    print(f"Total Rules: {stats['total_rules']}")
    print(f"Enabled Rules: {stats['enabled_rules']}")
    print(f"Disabled Rules: {stats['disabled_rules']}")
    
    # Test enabling/disabling categories
    print("\n🔧 Testing Category Management:")
    
    # Disable TypeScript category
    print("Disabling TypeScript category...")
    success = config_manager.disable_category(HookCategory.TYPESCRIPT, "Testing purposes")
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Disable specific rule
    print("Disabling rule 42...")
    success = config_manager.disable_rule(42, "Testing specific rule")
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Show updated statistics
    print("\n📊 Updated Statistics:")
    stats = config_manager.get_statistics()
    print(f"Total Rules: {stats['total_rules']}")
    print(f"Enabled Rules: {stats['enabled_rules']}")
    print(f"Disabled Rules: {stats['disabled_rules']}")
    
    # Test rule status checking
    print("\n🔍 Testing Rule Status:")
    print(f"Rule 42 enabled: {config_manager.is_rule_enabled(42)}")
    print(f"Rule 1 enabled: {config_manager.is_rule_enabled(1)}")
    
    # Test category status
    print("\n📋 Category Status:")
    ts_status = config_manager.get_category_status(HookCategory.TYPESCRIPT)
    print(f"TypeScript category: {ts_status['status']}")
    
    return True


def test_pre_implementation_validation():
    """Test pre-implementation validation with disabled hooks."""
    print("\n🧪 Testing Pre-Implementation Validation")
    print("=" * 50)
    
    # Initialize hook manager
    hook_manager = PreImplementationHookManager()
    
    # Test prompt that would normally trigger violations
    test_prompt = "Create a TypeScript function using 'any' type and store passwords in code"
    
    print(f"\n📝 Test Prompt: {test_prompt}")
    
    # Validate the prompt
    result = hook_manager.validate_before_generation(test_prompt, file_type="typescript")
    
    print(f"\n📊 Validation Results:")
    print(f"Valid: {result['valid']}")
    print(f"Total Rules Checked: {result['total_rules_checked']}")
    print(f"Violations Found: {len(result['violations'])}")
    
    if result['violations']:
        print("\n❌ Violations:")
        for violation in result['violations']:
            print(f"  - {violation.rule_id}: {violation.message}")
    else:
        print("\n✅ No violations found (some rules may be disabled)")
    
    if result['recommendations']:
        print("\n💡 Recommendations:")
        for rec in result['recommendations']:
            print(f"  - {rec}")
    
    return True


def test_cli_commands():
    """Test CLI command functionality."""
    print("\n🧪 Testing CLI Commands")
    print("=" * 50)
    
    # Simulate CLI commands
    print("\n📋 Available CLI Commands:")
    print("python tools/hook_cli.py list")
    print("python tools/hook_cli.py list --category typescript")
    print("python tools/hook_cli.py list --rule 42")
    print("python tools/hook_cli.py enable --category typescript")
    print("python tools/hook_cli.py disable --rule 42 --reason 'Testing'")
    print("python tools/hook_cli.py stats")
    print("python tools/hook_cli.py export --output hooks.json")
    print("python tools/hook_cli.py reset --force")
    
    return True


def main():
    """Run all tests."""
    print("🚀 Hook CLI Test Suite")
    print("=" * 60)
    
    try:
        # Test hook configuration
        test_hook_configuration()
        
        # Test pre-implementation validation
        test_pre_implementation_validation()
        
        # Test CLI commands
        test_cli_commands()
        
        print("\n✅ All tests completed successfully!")
        print("\n📚 Usage Examples:")
        print("1. List all hooks: python tools/hook_cli.py list")
        print("2. Disable TypeScript rules: python tools/hook_cli.py disable --category typescript")
        print("3. Enable specific rule: python tools/hook_cli.py enable --rule 42")
        print("4. Show statistics: python tools/hook_cli.py stats")
        print("5. Export config: python tools/hook_cli.py export --output my_hooks.json")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
