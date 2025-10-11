#!/usr/bin/env python3
"""
Category-Based Test - Tests rules organized by category with priority levels

This test groups rules by category and provides detailed analysis
of coverage within each category.
"""

import json
import os
from typing import Dict, List, Set
from validator.core import ConstitutionValidator

def load_rules_by_category() -> Dict:
    """Load rules organized by category with metadata."""
    with open('rules_config.json', 'r') as f:
        config = json.load(f)
    
    categories = {}
    for category, data in config['categories'].items():
        categories[category] = {
            'rules': data['rules'],
            'priority': data['priority'],
            'description': data['description'],
            'count': len(data['rules'])
        }
    
    return categories

def create_category_test_file(category: str, rules: List[int]) -> str:
    """Create a test file specifically for a category of rules."""
    
    # Define test patterns for each category
    test_patterns = {
        'basic_work': '''
# Basic Work Rules Test
def test_basic_work():
    # Rule 4: Hardcoded values instead of settings
    database_url = "postgresql://user:pass@localhost/db"
    
    # Rule 5: No logging
    def process_request():
        pass
    
    # Rule 10: AI without transparency
    def ai_predict():
        return "prediction"
    
    # Rule 13: No learning from mistakes
    def handle_error():
        pass
    
    # Rule 20: No accessibility
    def render_ui():
        pass
''',
        'requirements': '''
# Requirements Rules Test
def test_requirements():
    # Rule 1: Incomplete implementation
    def incomplete_function():
        # TODO: Implement this
        pass
    
    # Rule 2: Assumptions and magic numbers
    def process_data():
        if len(data) > 1000:  # Magic number
            pass
''',
        'privacy_security': '''
# Privacy & Security Rules Test
def test_privacy_security():
    # Rule 3: Hardcoded credentials
    password = "secret123"
    api_key = "sk-1234567890abcdef"
    
    # Rule 11: No data validation
    def handle_input(user_input):
        return user_input
    
    # Rule 12: No safety measures
    def dangerous_operation():
        pass
    
    # Rule 27: Unsafe data handling
    def store_data(data):
        database.store(data)
    
    # Rule 36: Personal data exposure
    def store_user_info():
        ssn = "123-45-6789"
''',
        'performance': '''
# Performance Rules Test
def test_performance():
    # Rule 8: Performance issues
    def slow_function():
        for i in range(10000):
            for j in range(10000):
                pass
    
    # Rule 67: Time waste
    def slow_process():
        pass
''',
        'architecture': '''
# Architecture Rules Test
def test_architecture():
    # Rule 19: Mixed concerns
    class UserInterface:
        def display_user(self):
            user = self.database.get_user()
            return user
    
    # Rule 21: No hybrid system design
    def process_locally():
        pass
    
    # Rule 23: No local processing
    def process_data():
        cloud_api.send(data)
    
    # Rule 24: Requires configuration
    def initialize():
        config = load_config()
    
    # Rule 28: No offline capability
    def fetch_data():
        return requests.get("https://api.example.com/data")
''',
        'system_design': '''
# System Design Rules Test
def test_system_design():
    # Rule 22: Inconsistent modules
    def module_a():
        pass
    
    # Rule 25: No progressive disclosure
    def show_all_info():
        pass
    
    # Rule 26: Poor organization
    # No clear imports section
    
    # Rule 29: Inconsistent registration
    def register_module_a():
        pass
    
    # Rule 30: Inconsistent product experience
    def handle_error_a():
        return "Error occurred"
    
    # Rule 31: No quick adoption
    def complex_setup():
        pass
    
    # Rule 32: No UX testing
    def new_feature():
        pass
''',
        'problem_solving': '''
# Problem-Solving Rules Test
def test_problem_solving():
    # Rule 33: Over-engineering
    class AbstractFactoryBuilder:
        pass
    
    # Rule 34: No help patterns
    def complex_task():
        pass
    
    # Rule 35: No proactive prevention
    def process_request():
        pass
    
    # Rule 37: High cognitive load
    def complex_workflow():
        pass
    
    # Rule 38: No behavior change
    def static_system():
        pass
    
    # Rule 39: No accuracy reporting
    def detect_anomaly():
        pass
    
    # Rule 41: No success dashboards
    def track_metrics():
        pass
''',
        'platform': '''
# Platform Rules Test
def test_platform():
    # Rule 42: No platform features
    def basic_function():
        pass
    
    # Rule 43: Slow data processing
    def process_large_dataset():
        pass
    
    # Rule 44: Interrupting help
    def show_help():
        pass
    
    # Rule 45: No emergency handling
    def critical_operation():
        pass
    
    # Rule 46: No developer happiness
    def developer_tool():
        pass
    
    # Rule 47: No problem prevention
    def system_monitor():
        pass
    
    # Rule 48: No compliance workflow
    def process_data():
        pass
    
    # Rule 49: Blocking security
    def security_check():
        pass
    
    # Rule 50: No gradual adoption
    def deploy_all():
        pass
    
    # Rule 51: No scalability
    def handle_requests():
        pass
''',
        'testing_safety': '''
# Testing & Safety Rules Test
def test_testing_safety():
    # Rule 7: No rollback mechanism
    def update_system():
        pass
    
    # Rule 14: No error handling
    def risky_operation():
        result = 1 / 0
    
    # Rule 59: No safety features
    def dangerous_action():
        pass
    
    # Rule 69: No edge case handling
    def process_input(data):
        pass
''',
        'code_quality': '''
# Code Quality Rules Test
def test_code_quality():
    # Rule 15: No documentation
    def undocumented_function():
        pass
    
    # Rule 18: Hardcoded values
    def calculate_tax(amount):
        return amount * 0.15
    
    # Rule 68: Poor code quality
    def messy_function():
        pass
''',
        'teamwork': '''
# Teamwork Rules Test
def test_teamwork():
    # Rule 52: No team collaboration
    def individual_task():
        pass
    
    # Rule 53: Knowledge silos
    def expert_function():
        pass
    
    # Rule 54: Daily frustration
    def annoying_feature():
        pass
    
    # Rule 55: Fear-based design
    def scary_feature():
        pass
    
    # Rule 56: No learning
    def static_system():
        pass
    
    # Rule 57: Wrong metrics
    def track_activity():
        pass
    
    # Rule 58: Late issue detection
    def process_data():
        pass
    
    # Rule 60: Poor automation
    def automate_everything():
        pass
    
    # Rule 61: No expert learning
    def implement_feature():
        pass
    
    # Rule 62: Information overload
    def show_dashboard():
        pass
    
    # Rule 63: Hidden dependencies
    def complex_system():
        pass
    
    # Rule 64: Inconsistent behavior
    def unpredictable_function():
        pass
    
    # Rule 65: Work loss risk
    def edit_document():
        pass
    
    # Rule 66: Ugly design
    def render_ui():
        pass
    
    # Rule 70: No improvement encouragement
    def review_process():
        pass
    
    # Rule 71: No skill adaptation
    def one_size_fits_all():
        pass
    
    # Rule 72: Annoying help
    def intrusive_assistance():
        pass
    
    # Rule 74: No value demonstration
    def show_features():
        pass
    
    # Rule 75: No growth adaptation
    def static_system():
        pass
    
    # Rule 76: No magic moments
    def boring_experience():
        pass
    
    # Rule 77: Friction everywhere
    def frustrating_workflow():
        pass
'''
    }
    
    # Get the test pattern for this category
    test_content = test_patterns.get(category, f"# {category} Rules Test\ndef test_{category}():\n    pass")
    
    # Write the test file
    filename = f"test_{category}_category.py"
    with open(filename, 'w') as f:
        f.write(test_content)
    
    return filename

def test_category_coverage(category: str, rules: List[int], priority: str, description: str) -> Dict:
    """Test coverage for a specific category."""
    print(f"\n{'='*60}")
    print(f"CATEGORY: {category.upper()}")
    print(f"Priority: {priority}")
    print(f"Description: {description}")
    print(f"Rules: {rules} ({len(rules)} rules)")
    print('='*60)
    
    # Create test file for this category
    test_file = create_category_test_file(category, rules)
    print(f"Created test file: {test_file}")
    
    # Run validator
    validator = ConstitutionValidator()
    result = validator.validate_file(test_file)
    
    # Analyze results
    all_violations = result.violations
    category_violations = [v for v in all_violations if v.rule_number in rules]
    rules_tested = set(v.rule_number for v in category_violations)
    
    print(f"\nResults:")
    print(f"  Total violations: {len(all_violations)}")
    print(f"  Category violations: {len(category_violations)}")
    print(f"  Rules tested: {len(rules_tested)}/{len(rules)} ({len(rules_tested)/len(rules)*100:.1f}%)")
    print(f"  Rules triggered: {sorted(rules_tested)}")
    
    # Show missing rules
    missing_rules = set(rules) - rules_tested
    if missing_rules:
        print(f"  Missing rules: {sorted(missing_rules)}")
    else:
        print(f"  [OK] All rules in category tested!")
    
    # Show violations by rule
    if category_violations:
        print(f"\n  Violations by rule:")
        rule_counts = {}
        for v in category_violations:
            rule_num = v.rule_number
            rule_counts[rule_num] = rule_counts.get(rule_num, 0) + 1
        
        for rule_num in sorted(rule_counts.keys()):
            print(f"    Rule {rule_num}: {rule_counts[rule_num]} violations")
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\n  Cleaned up: {test_file}")
    
    return {
        'category': category,
        'priority': priority,
        'total_rules': len(rules),
        'rules_tested': len(rules_tested),
        'coverage_percentage': len(rules_tested)/len(rules)*100,
        'rules_triggered': sorted(rules_tested),
        'missing_rules': sorted(missing_rules),
        'violations_count': len(category_violations)
    }

def run_category_based_test():
    """Run the comprehensive category-based test."""
    print("=" * 80)
    print("CATEGORY-BASED RULE COVERAGE TEST")
    print("=" * 80)
    
    # Load categories
    categories = load_rules_by_category()
    
    print(f"\nFound {len(categories)} categories:")
    for category, data in categories.items():
        print(f"  {category}: {data['count']} rules ({data['priority']})")
    
    # Test each category
    results = []
    for category, data in categories.items():
        result = test_category_coverage(
            category=category,
            rules=data['rules'],
            priority=data['priority'],
            description=data['description']
        )
        results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("CATEGORY COVERAGE SUMMARY")
    print('='*80)
    
    total_rules = sum(r['total_rules'] for r in results)
    total_tested = sum(r['rules_tested'] for r in results)
    overall_coverage = total_tested / total_rules * 100
    
    print(f"\nOverall Coverage: {total_tested}/{total_rules} ({overall_coverage:.1f}%)")
    
    print(f"\nBy Category:")
    for result in results:
        status = "[OK]" if result['coverage_percentage'] == 100 else "[WARN]"
        print(f"  {status} {result['category'].upper()}: {result['rules_tested']}/{result['total_rules']} ({result['coverage_percentage']:.1f}%) [{result['priority']}]")
    
    # Priority breakdown
    print(f"\nBy Priority:")
    for priority in ['critical', 'important', 'recommended']:
        priority_results = [r for r in results if r['priority'] == priority]
        if priority_results:
            priority_total = sum(r['total_rules'] for r in priority_results)
            priority_tested = sum(r['rules_tested'] for r in priority_results)
            priority_coverage = priority_tested / priority_total * 100
            print(f"  {priority.upper()}: {priority_tested}/{priority_total} ({priority_coverage:.1f}%)")
    
    print(f"\n{'='*80}")
    print("CATEGORY-BASED TEST COMPLETE")
    print('='*80)
    
    return results

if __name__ == '__main__':
    results = run_category_based_test()
