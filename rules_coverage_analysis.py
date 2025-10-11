#!/usr/bin/env python3
"""
Rules Coverage Analysis for ZEROUI 2.0 Constitution Code Validator.

This script analyzes which rules are implemented and tested.
"""

import json
from pathlib import Path


def analyze_rules_coverage():
    """Analyze the coverage of implemented rules."""
    
    # Load configuration
    with open('rules_config.json', 'r') as f:
        config = json.load(f)
    
    # All 71 unique rules from constitution
    all_rules = set()
    for category in config['categories'].values():
        all_rules.update(category['rules'])
    
    # Rules we implemented validators for
    implemented_rules = {
        # Privacy & Security
        3, 12, 27, 36,
        # Performance  
        8, 67,
        # Architecture
        19, 21, 23,
        # Testing & Safety
        7, 14, 59, 69,
        # Code Quality
        15, 18, 68
    }
    
    # Rules we tested with violations
    tested_rules = {
        3, 8, 12, 15, 19, 21, 23, 27, 36, 59, 67, 68, 69
    }
    
    # Enterprise critical rules
    enterprise_critical = set(config['enterprise_critical_rules'])
    enterprise_important = set(config['enterprise_important_rules'])
    enterprise_recommended = set(config['enterprise_recommended_rules'])
    
    print("ZEROUI 2.0 CONSTITUTION RULES COVERAGE ANALYSIS")
    print("=" * 60)
    
    print(f"\nTotal Rules in Constitution: {len(all_rules)}")
    print(f"Implemented Rules: {len(implemented_rules)}")
    print(f"Tested Rules: {len(tested_rules)}")
    
    print(f"\nImplementation Coverage: {len(implemented_rules)/len(all_rules)*100:.1f}%")
    print(f"Testing Coverage: {len(tested_rules)/len(all_rules)*100:.1f}%")
    
    # Enterprise coverage
    enterprise_implemented = implemented_rules.intersection(enterprise_critical.union(enterprise_important))
    enterprise_tested = tested_rules.intersection(enterprise_critical.union(enterprise_important))
    
    print(f"\nEnterprise Rules Implemented: {len(enterprise_implemented)}/{len(enterprise_critical.union(enterprise_important))}")
    print(f"Enterprise Rules Tested: {len(enterprise_tested)}/{len(enterprise_critical.union(enterprise_important))}")
    
    # Detailed breakdown
    print(f"\nDETAILED BREAKDOWN:")
    print(f"-" * 40)
    
    # Basic Work Rules
    basic_work = set(config['categories']['basic_work']['rules'])
    basic_implemented = implemented_rules.intersection(basic_work)
    basic_tested = tested_rules.intersection(basic_work)
    print(f"Basic Work Rules: {len(basic_implemented)}/{len(basic_work)} implemented, {len(basic_tested)}/{len(basic_work)} tested")
    
    # System Design Rules
    system_design = set(config['categories']['system_design']['rules'])
    system_implemented = implemented_rules.intersection(system_design)
    system_tested = tested_rules.intersection(system_design)
    print(f"System Design Rules: {len(system_implemented)}/{len(system_design)} implemented, {len(system_tested)}/{len(system_design)} tested")
    
    # Problem Solving Rules
    problem_solving = set(config['categories']['problem_solving']['rules'])
    problem_implemented = implemented_rules.intersection(problem_solving)
    problem_tested = tested_rules.intersection(problem_solving)
    print(f"Problem Solving Rules: {len(problem_implemented)}/{len(problem_solving)} implemented, {len(problem_tested)}/{len(problem_solving)} tested")
    
    # Platform Rules
    platform = set(config['categories']['platform']['rules'])
    platform_implemented = implemented_rules.intersection(platform)
    platform_tested = tested_rules.intersection(platform)
    print(f"Platform Rules: {len(platform_implemented)}/{len(platform)} implemented, {len(platform_tested)}/{len(platform)} tested")
    
    # Teamwork Rules
    teamwork = set(config['categories']['teamwork']['rules'])
    teamwork_implemented = implemented_rules.intersection(teamwork)
    teamwork_tested = tested_rules.intersection(teamwork)
    print(f"Teamwork Rules: {len(teamwork_implemented)}/{len(teamwork)} implemented, {len(teamwork_tested)}/{len(teamwork)} tested")
    
    # Missing implementations
    missing_implementation = all_rules - implemented_rules
    missing_testing = implemented_rules - tested_rules
    
    print(f"\nMISSING IMPLEMENTATIONS ({len(missing_implementation)} rules):")
    print(f"-" * 40)
    for rule in sorted(missing_implementation):
        category = "Unknown"
        for cat_name, cat_data in config['categories'].items():
            if rule in cat_data['rules']:
                category = cat_name.replace('_', ' ').title()
                break
        print(f"Rule {rule} ({category})")
    
    print(f"\nIMPLEMENTED BUT NOT TESTED ({len(missing_testing)} rules):")
    print(f"-" * 40)
    for rule in sorted(missing_testing):
        category = "Unknown"
        for cat_name, cat_data in config['categories'].items():
            if rule in cat_data['rules']:
                category = cat_name.replace('_', ' ').title()
                break
        print(f"Rule {rule} ({category})")
    
    # Priority analysis
    print(f"\nPRIORITY ANALYSIS:")
    print(f"-" * 40)
    
    critical_implemented = implemented_rules.intersection(enterprise_critical)
    critical_tested = tested_rules.intersection(enterprise_critical)
    print(f"Critical Rules: {len(critical_implemented)}/{len(enterprise_critical)} implemented, {len(critical_tested)}/{len(enterprise_critical)} tested")
    
    important_implemented = implemented_rules.intersection(enterprise_important)
    important_tested = tested_rules.intersection(enterprise_important)
    print(f"Important Rules: {len(important_implemented)}/{len(enterprise_important)} implemented, {len(important_tested)}/{len(enterprise_important)} tested")
    
    recommended_implemented = implemented_rules.intersection(enterprise_recommended)
    recommended_tested = tested_rules.intersection(enterprise_recommended)
    print(f"Recommended Rules: {len(recommended_implemented)}/{len(enterprise_recommended)} implemented, {len(recommended_tested)}/{len(enterprise_recommended)} tested")
    
    return {
        'total_rules': len(all_rules),
        'implemented': len(implemented_rules),
        'tested': len(tested_rules),
        'implementation_coverage': len(implemented_rules)/len(all_rules)*100,
        'testing_coverage': len(tested_rules)/len(all_rules)*100,
        'enterprise_coverage': len(enterprise_implemented)/len(enterprise_critical.union(enterprise_important))*100
    }


if __name__ == "__main__":
    analyze_rules_coverage()
