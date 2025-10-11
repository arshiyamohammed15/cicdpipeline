#!/usr/bin/env python3
"""
Configuration Integrity Validator - Validates rules_config.json for consistency

This test ensures the configuration file is properly structured and
all rules are correctly defined without conflicts.
"""

import json
import os
from typing import Dict, List, Set, Tuple

def load_configuration() -> Dict:
    """Load and parse the rules configuration."""
    try:
        with open('rules_config.json', 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("[ERROR] rules_config.json not found!")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in rules_config.json: {e}")
        return None

def validate_basic_structure(config: Dict) -> List[str]:
    """Validate the basic structure of the configuration."""
    issues = []
    
    # Check required top-level keys
    required_keys = ['constitution_version', 'total_rules', 'categories', 'validation_patterns']
    for key in required_keys:
        if key not in config:
            issues.append(f"Missing required key: {key}")
    
    # Check constitution version
    if 'constitution_version' in config:
        version = config['constitution_version']
        if version != "2.0":
            issues.append(f"Unexpected constitution version: {version} (expected 2.0)")
    
    return issues

def validate_categories(config: Dict) -> Tuple[List[str], Dict]:
    """Validate the categories section."""
    issues = []
    all_rules = []
    rules_by_category = {}
    
    if 'categories' not in config:
        issues.append("Missing 'categories' section")
        return issues, {}
    
    categories = config['categories']
    
    # Check each category
    for category_name, category_data in categories.items():
        # Check required category keys
        required_keys = ['rules', 'priority', 'description']
        for key in required_keys:
            if key not in category_data:
                issues.append(f"Category '{category_name}' missing key: {key}")
        
        # Validate rules list
        if 'rules' in category_data:
            rules = category_data['rules']
            if not isinstance(rules, list):
                issues.append(f"Category '{category_name}' rules must be a list")
            else:
                # Check for non-integer rules
                for rule in rules:
                    if not isinstance(rule, int):
                        issues.append(f"Category '{category_name}' contains non-integer rule: {rule}")
                    elif rule < 1 or rule > 77:
                        issues.append(f"Category '{category_name}' contains invalid rule number: {rule}")
                
                all_rules.extend(rules)
                rules_by_category[category_name] = rules
        
        # Validate priority
        if 'priority' in category_data:
            priority = category_data['priority']
            valid_priorities = ['critical', 'important', 'recommended']
            if priority not in valid_priorities:
                issues.append(f"Category '{category_name}' has invalid priority: {priority}")
    
    return issues, rules_by_category

def validate_rule_consistency(all_rules: List[int], expected_total: int) -> List[str]:
    """Validate rule consistency and numbering."""
    issues = []
    
    # Check for duplicates
    duplicates = [r for r in all_rules if all_rules.count(r) > 1]
    if duplicates:
        issues.append(f"Duplicate rules found: {duplicates}")
    
    # Check total count
    actual_total = len(all_rules)
    if actual_total != expected_total:
        issues.append(f"Expected {expected_total} rules, found {actual_total}")
    
    # Check for gaps in numbering
    if all_rules:
        min_rule = min(all_rules)
        max_rule = max(all_rules)
        expected_range = set(range(min_rule, max_rule + 1))
        actual_rules = set(all_rules)
        gaps = expected_range - actual_rules
        
        if gaps:
            issues.append(f"Gaps in rule numbering: {sorted(gaps)}")
        
        # Check for rules outside expected range (1-77)
        invalid_rules = [r for r in all_rules if r < 1 or r > 77]
        if invalid_rules:
            issues.append(f"Rules outside valid range (1-77): {invalid_rules}")
    
    return issues

def validate_validation_patterns(config: Dict, rules_by_category: Dict) -> List[str]:
    """Validate the validation patterns section."""
    issues = []
    
    if 'validation_patterns' not in config:
        issues.append("Missing 'validation_patterns' section")
        return issues
    
    patterns = config['validation_patterns']
    
    # Check that each category with rules has patterns
    for category_name, rules in rules_by_category.items():
        if category_name not in patterns:
            issues.append(f"Category '{category_name}' has rules but no validation patterns")
        else:
            category_patterns = patterns[category_name]
            
            # Check for rules list in patterns
            if 'rules' not in category_patterns:
                issues.append(f"Category '{category_name}' patterns missing 'rules' list")
            else:
                pattern_rules = category_patterns['rules']
                if not isinstance(pattern_rules, list):
                    issues.append(f"Category '{category_name}' pattern rules must be a list")
                else:
                    # Check that pattern rules match category rules
                    if set(pattern_rules) != set(rules):
                        issues.append(f"Category '{category_name}' pattern rules don't match category rules")
            
            # Check for patterns object
            if 'patterns' not in category_patterns:
                issues.append(f"Category '{category_name}' missing 'patterns' object")
            else:
                pattern_definitions = category_patterns['patterns']
                if not isinstance(pattern_definitions, dict):
                    issues.append(f"Category '{category_name}' patterns must be a dictionary")
                else:
                    # Check each pattern has required keys
                    for pattern_name, pattern_data in pattern_definitions.items():
                        required_keys = ['keywords', 'severity', 'message']
                        for key in required_keys:
                            if key not in pattern_data:
                                issues.append(f"Category '{category_name}' pattern '{pattern_name}' missing key: {key}")
    
    return issues

def validate_enterprise_rules(config: Dict) -> List[str]:
    """Validate enterprise rule definitions."""
    issues = []
    
    # Check if enterprise rules are defined
    if 'enterprise_rules' not in config:
        issues.append("Missing 'enterprise_rules' section")
        return issues
    
    enterprise_rules = config['enterprise_rules']
    
    # Validate enterprise rule structure
    if not isinstance(enterprise_rules, dict):
        issues.append("Enterprise rules must be a dictionary")
        return issues
    
    # Check each priority level
    for priority, rules in enterprise_rules.items():
        if not isinstance(rules, list):
            issues.append(f"Enterprise rules for '{priority}' must be a list")
        else:
            # Check for non-integer rules
            for rule in rules:
                if not isinstance(rule, int):
                    issues.append(f"Enterprise rules for '{priority}' contains non-integer rule: {rule}")
    
    return issues

def generate_configuration_report(config: Dict) -> Dict:
    """Generate a comprehensive configuration report."""
    report = {
        'valid': True,
        'issues': [],
        'statistics': {},
        'categories': {},
        'rules': {}
    }
    
    # Basic structure validation
    structure_issues = validate_basic_structure(config)
    report['issues'].extend(structure_issues)
    
    # Categories validation
    category_issues, rules_by_category = validate_categories(config)
    report['issues'].extend(category_issues)
    
    # Rule consistency validation
    all_rules = []
    for rules in rules_by_category.values():
        all_rules.extend(rules)
    
    expected_total = config.get('total_rules', 0)
    consistency_issues = validate_rule_consistency(all_rules, expected_total)
    report['issues'].extend(consistency_issues)
    
    # Validation patterns validation
    pattern_issues = validate_validation_patterns(config, rules_by_category)
    report['issues'].extend(pattern_issues)
    
    # Enterprise rules validation
    enterprise_issues = validate_enterprise_rules(config)
    report['issues'].extend(enterprise_issues)
    
    # Set validity
    report['valid'] = len(report['issues']) == 0
    
    # Generate statistics
    report['statistics'] = {
        'total_rules': len(all_rules),
        'expected_rules': expected_total,
        'categories_count': len(rules_by_category),
        'rule_range': f"{min(all_rules)}-{max(all_rules)}" if all_rules else "N/A",
        'duplicates': len([r for r in all_rules if all_rules.count(r) > 1])
    }
    
    # Category breakdown
    for category_name, rules in rules_by_category.items():
        category_data = config['categories'][category_name]
        report['categories'][category_name] = {
            'rule_count': len(rules),
            'priority': category_data.get('priority', 'unknown'),
            'rules': sorted(rules)
        }
    
    # Rule analysis
    report['rules'] = {
        'all_rules': sorted(all_rules),
        'duplicates': [r for r in all_rules if all_rules.count(r) > 1],
        'gaps': []
    }
    
    if all_rules:
        min_rule = min(all_rules)
        max_rule = max(all_rules)
        expected_range = set(range(min_rule, max_rule + 1))
        actual_rules = set(all_rules)
        report['rules']['gaps'] = sorted(expected_range - actual_rules)
    
    return report

def run_configuration_integrity_test():
    """Run the comprehensive configuration integrity test."""
    print("=" * 80)
    print("CONFIGURATION INTEGRITY VALIDATOR")
    print("=" * 80)
    
    # Load configuration
    print("\n1. Loading configuration...")
    config = load_configuration()
    if config is None:
        return False
    
    print("   [OK] Configuration loaded successfully")
    
    # Generate report
    print("\n2. Validating configuration...")
    report = generate_configuration_report(config)
    
    # Display results
    print(f"\n3. Validation Results:")
    if report['valid']:
        print("   [OK] Configuration is VALID")
    else:
        print("   [ERROR] Configuration has ISSUES:")
        for issue in report['issues']:
            print(f"      - {issue}")
    
    # Display statistics
    print(f"\n4. Configuration Statistics:")
    stats = report['statistics']
    print(f"   Total rules: {stats['total_rules']}")
    print(f"   Expected rules: {stats['expected_rules']}")
    print(f"   Categories: {stats['categories_count']}")
    print(f"   Rule range: {stats['rule_range']}")
    print(f"   Duplicates: {stats['duplicates']}")
    
    # Display categories
    print(f"\n5. Categories Breakdown:")
    for category_name, data in report['categories'].items():
        print(f"   {category_name.upper()}:")
        print(f"      Rules: {data['rule_count']} ({data['priority']})")
        print(f"      Numbers: {data['rules']}")
    
    # Display rule analysis
    print(f"\n6. Rule Analysis:")
    rules = report['rules']
    print(f"   All rules: {rules['all_rules']}")
    if rules['duplicates']:
        print(f"   Duplicates: {rules['duplicates']}")
    if rules['gaps']:
        print(f"   Gaps: {rules['gaps']}")
    
    # Display enterprise rules if present
    if 'enterprise_rules' in config:
        print(f"\n7. Enterprise Rules:")
        enterprise_rules = config['enterprise_rules']
        for priority, rules in enterprise_rules.items():
            print(f"   {priority.upper()}: {len(rules)} rules")
    
    print(f"\n{'='*80}")
    print("CONFIGURATION INTEGRITY TEST COMPLETE")
    print('='*80)
    
    return report['valid']

if __name__ == '__main__':
    success = run_configuration_integrity_test()
    exit(0 if success else 1)
