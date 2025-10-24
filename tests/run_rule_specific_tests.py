#!/usr/bin/env python3
"""
Rule-Specific Test Runner for ZeroUI 2.0 Constitution
Runs individual rule tests, implementation logic tests, and compliance validation

This test runner provides comprehensive validation for all 252 constitution rules
with strict compliance checking and no false positives.
"""

import sys
import os
import time
import json
import argparse
import unittest
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_individual_rules import IndividualRuleTester
from test_rule_implementation_logic import RuleImplementationLogicTester
from test_rule_compliance_validation import RuleComplianceValidator


class RuleSpecificTestRunner:
    """Comprehensive test runner for rule-specific tests."""
    
    def __init__(self, verbose: bool = True, clear_cache: bool = True, no_cache: bool = True):
        self.verbose = verbose
        self.clear_cache = clear_cache
        self.no_cache = no_cache
        self.project_root = Path(__file__).parent.parent
        self.output_dir = self.project_root / "tests" / "test_reports"
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize testers
        self.individual_tester = IndividualRuleTester()
        self.implementation_tester = RuleImplementationLogicTester()
        self.compliance_validator = RuleComplianceValidator()
        
        # Clear cache if requested
        if self.clear_cache:
            self._clear_all_caches()
    
    def _clear_all_caches(self):
        """Clear all test caches and temporary files."""
        if self.verbose:
            print("Clearing all test caches...")
        
        # Clear Python cache
        for pycache in self.project_root.rglob("__pycache__"):
            if pycache.is_dir():
                import shutil
                shutil.rmtree(pycache)
        
        # Clear test cache files
        cache_files = [
            "test_cache.json",
            "test_results.json",
            "individual_rule_test_results.json",
            "rule_implementation_logic_results.json",
            "rule_compliance_validation_results.json"
        ]
        
        for cache_file in cache_files:
            cache_path = self.project_root / "tests" / cache_file
            if cache_path.exists():
                cache_path.unlink()
        
        if self.verbose:
            print("Cache cleared successfully.")
    
    def run_individual_rule_tests(self) -> Dict[str, Any]:
        """Run individual rule compliance tests."""
        if self.verbose:
            print("\n" + "=" * 80)
            print("RUNNING INDIVIDUAL RULE COMPLIANCE TESTS")
            print("=" * 80)
        
        start_time = time.time()
        results = self.individual_tester.run_all_rule_tests()
        execution_time = time.time() - start_time
        
        results['execution_time'] = execution_time
        results['test_type'] = 'individual_rules'
        
        # Save results
        output_file = self.output_dir / f"individual_rule_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        if self.verbose:
            print(f"Individual rule tests completed in {execution_time:.2f}s")
            print(f"Results saved to: {output_file}")
        
        return results
    
    def run_implementation_logic_tests(self) -> Dict[str, Any]:
        """Run rule implementation logic tests."""
        if self.verbose:
            print("\n" + "=" * 80)
            print("RUNNING RULE IMPLEMENTATION LOGIC TESTS")
            print("=" * 80)
        
        start_time = time.time()
        results = self.implementation_tester.run_all_implementation_logic_tests()
        execution_time = time.time() - start_time
        
        results['execution_time'] = execution_time
        results['test_type'] = 'implementation_logic'
        
        # Save results
        output_file = self.output_dir / f"implementation_logic_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        if self.verbose:
            print(f"Implementation logic tests completed in {execution_time:.2f}s")
            print(f"Results saved to: {output_file}")
        
        return results
    
    def run_compliance_validation_tests(self) -> Dict[str, Any]:
        """Run rule compliance validation tests."""
        if self.verbose:
            print("\n" + "=" * 80)
            print("RUNNING RULE COMPLIANCE VALIDATION TESTS")
            print("=" * 80)
        
        start_time = time.time()
        results = self.compliance_validator.run_all_compliance_validations()
        execution_time = time.time() - start_time
        
        results['execution_time'] = execution_time
        results['test_type'] = 'compliance_validation'
        
        # Save results
        output_file = self.output_dir / f"compliance_validation_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        if self.verbose:
            print(f"Compliance validation tests completed in {execution_time:.2f}s")
            print(f"Results saved to: {output_file}")
        
        return results
    
    def run_all_rule_specific_tests(self) -> Dict[str, Any]:
        """Run all rule-specific tests."""
        if self.verbose:
            print("=" * 100)
            print("ZEROUI 2.0 CONSTITUTION RULES - RULE-SPECIFIC TEST SUITE")
            print("=" * 100)
            print(f"Test Execution Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Clear Cache: {'Enabled' if self.clear_cache else 'Disabled'}")
            print(f"No Cache: {'Enabled' if self.no_cache else 'Disabled'}")
            print("=" * 100)
        
        overall_start_time = time.time()
        
        # Run all test types
        individual_results = self.run_individual_rule_tests()
        implementation_results = self.run_implementation_logic_tests()
        compliance_results = self.run_compliance_validation_tests()
        
        overall_execution_time = time.time() - overall_start_time
        
        # Compile comprehensive results
        comprehensive_results = {
            'test_execution_info': {
                'start_time': datetime.now().isoformat(),
                'execution_time': overall_execution_time,
                'clear_cache': self.clear_cache,
                'no_cache': self.no_cache,
                'test_types': ['individual_rules', 'implementation_logic', 'compliance_validation']
            },
            'individual_rule_tests': individual_results,
            'implementation_logic_tests': implementation_results,
            'compliance_validation_tests': compliance_results,
            'summary': {
                'total_execution_time': overall_execution_time,
                'individual_rules_compliance': individual_results.get('compliance_rate', 0),
                'implementation_logic_compliance': implementation_results.get('compliance_rate', 0),
                'compliance_validation_rate': compliance_results.get('compliance_rate', 0),
                'total_violations': (
                    individual_results.get('total_violations', 0) +
                    implementation_results.get('total_violations', 0) +
                    compliance_results.get('total_violations', 0)
                ),
                'critical_violations': compliance_results.get('critical_violations', 0)
            }
        }
        
        # Save comprehensive results
        output_file = self.output_dir / f"comprehensive_rule_specific_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_results, f, indent=2)
        
        if self.verbose:
            self._print_comprehensive_summary(comprehensive_results)
            print(f"\nComprehensive results saved to: {output_file}")
        
        return comprehensive_results
    
    def _print_comprehensive_summary(self, results: Dict[str, Any]):
        """Print comprehensive test summary."""
        print("\n" + "=" * 100)
        print("COMPREHENSIVE RULE-SPECIFIC TEST SUMMARY")
        print("=" * 100)
        
        summary = results['summary']
        
        print(f"Total Execution Time: {summary['total_execution_time']:.2f}s")
        print(f"Individual Rules Compliance: {summary['individual_rules_compliance']:.1f}%")
        print(f"Implementation Logic Compliance: {summary['implementation_logic_compliance']:.1f}%")
        print(f"Compliance Validation Rate: {summary['compliance_validation_rate']:.1f}%")
        print(f"Total Violations: {summary['total_violations']}")
        print(f"Critical Violations: {summary['critical_violations']}")
        
        # Overall compliance rate
        overall_compliance = (
            summary['individual_rules_compliance'] +
            summary['implementation_logic_compliance'] +
            summary['compliance_validation_rate']
        ) / 3
        
        print(f"Overall Compliance Rate: {overall_compliance:.1f}%")
        
        if overall_compliance >= 90:
            print("STATUS: [PASS] EXCELLENT COMPLIANCE")
        elif overall_compliance >= 75:
            print("STATUS: [WARN] GOOD COMPLIANCE (needs improvement)")
        else:
            print("STATUS: [FAIL] POOR COMPLIANCE (requires immediate attention)")
        
        print("=" * 100)


def main():
    """Main function to run rule-specific tests."""
    parser = argparse.ArgumentParser(description='ZeroUI 2.0 Constitution Rules - Rule-Specific Test Runner')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--clear-cache', action='store_true', default=True, help='Clear test cache before running')
    parser.add_argument('--no-cache', action='store_true', default=True, help='Disable test caching')
    parser.add_argument('--test-type', choices=['individual', 'implementation', 'compliance', 'all'], 
                       default='all', help='Type of tests to run')
    
    args = parser.parse_args()
    
    runner = RuleSpecificTestRunner(
        verbose=args.verbose,
        clear_cache=args.clear_cache,
        no_cache=args.no_cache
    )
    
    if args.test_type == 'individual':
        results = runner.run_individual_rule_tests()
    elif args.test_type == 'implementation':
        results = runner.run_implementation_logic_tests()
    elif args.test_type == 'compliance':
        results = runner.run_compliance_validation_tests()
    else:  # all
        results = runner.run_all_rule_specific_tests()
    
    # Exit with error code if tests failed
    if results.get('summary', {}).get('total_violations', 0) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
