#!/usr/bin/env python3
"""
Dynamic Coverage Test - Automatically tests all rules from rules_config.json

This test dynamically discovers all rules from the configuration file,
making it immune to rule renumbering and easy to maintain.
"""

import json
import os
from typing import List, Dict, Set
from validator.core import ConstitutionValidator

def load_all_rules_from_config() -> Dict:
    """Load all rules and configuration from rules_config.json."""
    with open('rules_config.json', 'r') as f:
        config = json.load(f)
    
    all_rules = []
    rules_by_category = {}
    
    for category, data in config['categories'].items():
        rules = data['rules']
        all_rules.extend(rules)
        rules_by_category[category] = {
            'rules': rules,
            'priority': data['priority'],
            'description': data['description'],
            'count': len(rules)
        }
    
    return {
        'total_rules': len(all_rules),
        'all_rules': sorted(all_rules),
        'rules_by_category': rules_by_category,
        'config': config
    }

def validate_configuration_integrity(config_data: Dict) -> Dict:
    """Validate the configuration for integrity issues."""
    issues = []
    all_rules = config_data['all_rules']
    
    # Check for duplicates
    duplicates = [r for r in all_rules if all_rules.count(r) > 1]
    if duplicates:
        issues.append(f"Duplicate rules found: {duplicates}")
    
    # Verify total count matches config
    expected_total = config_data['config']['total_rules']
    actual_total = len(all_rules)
    if actual_total != expected_total:
        issues.append(f"Expected {expected_total} rules, found {actual_total}")
    
    # Check for gaps in rule numbers
    min_rule = min(all_rules)
    max_rule = max(all_rules)
    expected_range = set(range(min_rule, max_rule + 1))
    actual_rules = set(all_rules)
    gaps = expected_range - actual_rules
    
    if gaps:
        issues.append(f"Gaps in rule numbering: {sorted(gaps)}")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'rule_range': f"{min_rule}-{max_rule}",
        'total_rules': actual_total
    }

def create_comprehensive_test_file() -> str:
    """Create a comprehensive test file that should trigger many rules."""
    test_content = '''#!/usr/bin/env python3
"""
Comprehensive test file designed to trigger violations across all rule categories.
This file intentionally contains various code quality issues to test the validator.
"""

# Rule violations for testing
import os
import sys

# Hardcoded credentials (Rule 3)
password = "secret123"
api_key = "sk-1234567890abcdef"

# Magic numbers (Rule 2)
def process_data():
    if len(data) > 1000:  # Magic number
        return data * 0.15  # Hardcoded tax rate

# No logging (Rule 5)
def handle_request():
    # No logging here
    pass

# Missing docstrings (Rule 15)
def undocumented_function():
    pass

# Performance issues (Rule 8)
def slow_function():
    for i in range(10000):
        for j in range(10000):
            # Nested loops
            pass

# No error handling (Rule 14)
def risky_operation():
    result = 1 / 0

# Mixed concerns (Rule 19)
class UserInterface:
    def display_user(self):
        # UI logic mixed with business logic
        user = self.database.get_user()
        return user

# No accessibility (Rule 20)
def render_button():
    # No accessibility features
    pass

# No local processing (Rule 23)
def process_data():
    # Always sends to cloud
    cloud_api.send(data)

# No progressive disclosure (Rule 25)
def show_all_info():
    # Shows everything at once
    pass

# No offline capability (Rule 28)
def fetch_data():
    # Always requires internet
    return requests.get("https://api.example.com/data")

# No gradual adoption (Rule 50)
def deploy_all():
    # All-or-nothing deployment
    pass

# No team collaboration (Rule 52)
def individual_task():
    # No sharing
    pass

# No knowledge sharing (Rule 53)
def expert_function():
    # No documentation
    pass

# Friction points (Rule 54)
def annoying_feature():
    # Repetitive tasks
    pass

# No confidence building (Rule 55)
def scary_feature():
    # No safety nets
    pass

# No learning (Rule 56)
def static_system():
    # No adaptation
    pass

# Wrong metrics (Rule 57)
def track_activity():
    # Tracks clicks, not value
    pass

# Late issue detection (Rule 58)
def process_data():
    # No early validation
    pass

# No safety features (Rule 59)
def dangerous_action():
    # No undo
    pass

# Poor automation (Rule 60)
def automate_everything():
    # No human oversight
    pass

# No expert learning (Rule 61)
def implement_feature():
    # No best practices
    pass

# Information overload (Rule 62)
def show_dashboard():
    # Too much information
    pass

# Hidden dependencies (Rule 63)
def complex_system():
    # Dependencies not visible
    pass

# Inconsistent behavior (Rule 64)
def unpredictable_function():
    # Different behavior each time
    pass

# Work loss risk (Rule 65)
def edit_document():
    # No auto-save
    pass

# Ugly design (Rule 66)
def render_ui():
    # Poor design
    pass

# Time waste (Rule 67)
def slow_process():
    # Unnecessary delays
    pass

# Poor code quality (Rule 68)
def messy_function():
    # Unclear code
    pass

# No edge case handling (Rule 69)
def process_input(data):
    # No edge case handling
    pass

# No improvement encouragement (Rule 70)
def review_process():
    # No suggestions
    pass

# No skill adaptation (Rule 71)
def one_size_fits_all():
    # No beginner support
    pass

# Annoying help (Rule 72)
def intrusive_assistance():
    # Always interrupting
    pass

# No value demonstration (Rule 74)
def show_features():
    # No clear benefits
    pass

# No growth adaptation (Rule 75)
def static_system():
    # No scaling
    pass

# No magic moments (Rule 76)
def boring_experience():
    # No delight
    pass

# Friction everywhere (Rule 77)
def frustrating_workflow():
    # Many friction points
    pass
'''
    
    # Write the test file
    with open('test_sample_code.py', 'w') as f:
        f.write(test_content)
    
    return 'test_sample_code.py'

def run_dynamic_coverage_test():
    """Run the comprehensive dynamic coverage test."""
    print("=" * 80)
    print("DYNAMIC RULE COVERAGE TEST")
    print("=" * 80)
    
    # Load configuration
    print("\n1. Loading configuration...")
    config_data = load_all_rules_from_config()
    
    print(f"   Total rules configured: {config_data['total_rules']}")
    print(f"   Rule range: {min(config_data['all_rules'])}-{max(config_data['all_rules'])}")
    
    # Validate configuration
    print("\n2. Validating configuration integrity...")
    integrity = validate_configuration_integrity(config_data)
    
    if integrity['valid']:
        print("   [OK] Configuration is valid")
    else:
        print("   [ERROR] Configuration issues found:")
        for issue in integrity['issues']:
            print(f"      - {issue}")
        return
    
    # Create test file
    print("\n3. Creating comprehensive test file...")
    test_file = create_comprehensive_test_file()
    print(f"   [OK] Created {test_file}")
    
    # Run validator
    print("\n4. Running validator...")
    validator = ConstitutionValidator()
    result = validator.validate_file(test_file)
    
    # Analyze results
    print("\n5. Analyzing results...")
    all_violations = result.violations
    rules_tested = set(v.rule_number for v in all_violations)
    
    print(f"   Total violations found: {len(all_violations)}")
    print(f"   Unique rules tested: {len(rules_tested)}")
    print(f"   Coverage: {len(rules_tested)}/{config_data['total_rules']} ({len(rules_tested)/config_data['total_rules']*100:.1f}%)")
    
    # Show rules by category
    print("\n6. Coverage by category:")
    for category, data in config_data['rules_by_category'].items():
        category_rules = set(data['rules'])
        category_tested = rules_tested.intersection(category_rules)
        coverage_pct = len(category_tested) / len(category_rules) * 100
        
        print(f"   {category.upper()}:")
        print(f"      Rules: {len(category_tested)}/{len(category_rules)} ({coverage_pct:.1f}%)")
        print(f"      Priority: {data['priority']}")
        print(f"      Tested: {sorted(category_tested)}")
        if len(category_tested) < len(category_rules):
            missing = category_rules - category_tested
            print(f"      Missing: {sorted(missing)}")
    
    # Show missing rules
    missing_rules = set(config_data['all_rules']) - rules_tested
    if missing_rules:
        print(f"\n7. Rules not triggered ({len(missing_rules)}):")
        print(f"   {sorted(missing_rules)}")
    else:
        print("\n7. [OK] All rules were triggered!")
    
    # Show violations by rule
    print(f"\n8. Violations by rule:")
    rule_counts = {}
    for v in all_violations:
        rule_num = v.rule_number
        rule_counts[rule_num] = rule_counts.get(rule_num, 0) + 1
    
    for rule_num in sorted(rule_counts.keys()):
        print(f"   Rule {rule_num}: {rule_counts[rule_num]} violations")
    
    # Cleanup
    print(f"\n9. Cleanup...")
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"   [OK] Removed {test_file}")
    
    print("\n" + "=" * 80)
    print("DYNAMIC COVERAGE TEST COMPLETE")
    print("=" * 80)
    
    return {
        'total_rules': config_data['total_rules'],
        'rules_tested': len(rules_tested),
        'coverage_percentage': len(rules_tested)/config_data['total_rules']*100,
        'missing_rules': sorted(missing_rules),
        'violations_by_rule': rule_counts
    }

if __name__ == '__main__':
    results = run_dynamic_coverage_test()
