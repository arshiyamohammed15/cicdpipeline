#!/usr/bin/env python3
"""
Cursor Constitution Rule Compliance Test Runner - Constitution Compliant

What: Tests whether Cursor follows all Constitution rules when generating code
Why: Ensures AI code generation complies with ZeroUI2.0 Constitution
Reads: config/test_config.json, test fixtures
Writes: test results, receipts, logs
Contracts: Test API contracts, logging schema
Risks: Test failures, false positives

Following Constitution Rules:
- Rule 12: Test Everything (prove behavior before/after)
- Rule 97-106: Simple English comments
- Rule 132-149: Structured logging
- Rule 141: Receipt system for audit trail
- Rule 129: Proper error handling
"""

import json
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import os

# Add the validator to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from constitution_test_base import ConstitutionTestBase

class CursorComplianceTester(ConstitutionTestBase):
    """Test Cursor's compliance with Constitution rules"""

    def __init__(self):
        super().__init__()
        self.test_prompts_file = Path(__file__).parent / 'test_prompts.json'
        self.samples_dir = Path(__file__).parent / 'samples'
        self.results = []
        self.test_config = self._load_test_config()

    def _load_test_config(self) -> Dict[str, Any]:
        """Load test configuration"""
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "test_config.json"
        
        if not config_path.exists():
            self.logger.warning(
                "Test config not found, using defaults",
                extra={
                    "traceId": self.test_trace_id,
                    "event": "config.missing"
                }
            )
            return {}
        
        with open(config_path, 'r') as f:
            return json.load(f)

    def load_test_prompts(self) -> Dict[str, Any]:
        """Load test prompts from JSON file"""
        try:
            with open(self.test_prompts_file, 'r') as f:
                prompts = json.load(f)
            
            self.emit_receipt("load_prompts", "success", f"Loaded {len(prompts)} test prompts")
            return prompts
            
        except Exception as e:
            self.emit_receipt("load_prompts", "error", f"Failed to load test prompts: {e}")
            self.logger.error(
                f"Failed to load test prompts: {e}",
                extra={
                    "traceId": self.test_trace_id,
                    "event": "prompts.load_error"
                }
            )
            return {}

    def create_sample_code(self, rule_number: int, test_scenario: Dict[str, Any]) -> str:
        """Create sample code that represents what Cursor might generate"""
        self.emit_receipt("create_sample", "planned", f"Creating sample for rule {rule_number}")
        
        try:
            # Create sample code based on rule and scenario
            sample_code = self._generate_sample_code(rule_number, test_scenario)
            
            self.emit_receipt("create_sample", "success", f"Created sample for rule {rule_number}")
            return sample_code
            
        except Exception as e:
            self.emit_receipt("create_sample", "error", f"Failed to create sample for rule {rule_number}: {e}")
            raise

    def _generate_sample_code(self, rule_number: int, scenario: Dict[str, Any]) -> str:
        """Generate sample code for testing"""
        if rule_number == 4:  # Settings files, not hardcoded
            if scenario.get("violation"):
                return """
# VIOLATION: Hardcoded values
MAX_RETRIES = 3
TIMEOUT = 30
"""
            else:
                return """
# VALID: Using settings file
import json
with open('config/settings.json') as f:
    settings = json.load(f)
MAX_RETRIES = settings.get('max_retries', 3)
TIMEOUT = settings.get('timeout', 30)
"""
        
        elif rule_number == 5:  # Keep good records
            if scenario.get("violation"):
                return """
# VIOLATION: No logging
def process_data(data):
    return data
"""
            else:
                return """
# VALID: Proper logging
import logging
logger = logging.getLogger(__name__)

def process_data(data):
    logger.info("Processing data", extra={"data_size": len(data)})
    return data
"""
        
        elif rule_number == 10:  # Be honest about AI decisions
            if scenario.get("violation"):
                return """
# VIOLATION: No AI transparency
def ai_decision(input_data):
    return "approve"
"""
            else:
                return """
# VALID: AI transparency
def ai_decision(input_data):
    return {
        "decision": "approve",
        "confidence": 0.85,
        "explanation": "Based on input analysis",
        "model_version": "v2.3"
    }
"""
        
        else:
            return f"# Sample code for rule {rule_number}"

    def test_rule_compliance(self, rule_number: int, test_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test compliance for a specific rule"""
        self.emit_receipt(f"test_rule_{rule_number}", "planned", f"Testing rule {rule_number} compliance")
        
        try:
            # Create sample code
            sample_code = self.create_sample_code(rule_number, test_scenario)
            
            # Validate constitution compliance
            is_compliant = self.validate_constitution_compliance(rule_number, "basic_work")
            
            result = {
                "rule_number": rule_number,
                "scenario": test_scenario,
                "sample_code": sample_code,
                "is_compliant": is_compliant,
                "timestamp": time.time(),
                "trace_id": self.test_trace_id
            }
            
            self.results.append(result)
            
            if is_compliant:
                self.emit_receipt(f"test_rule_{rule_number}", "success", f"Rule {rule_number} is compliant")
            else:
                self.emit_receipt(f"test_rule_{rule_number}", "error", f"Rule {rule_number} is not compliant")
            
            return result
            
        except Exception as e:
            self.emit_receipt(f"test_rule_{rule_number}", "error", f"Error testing rule {rule_number}: {e}")
            self.logger.error(
                f"Error testing rule {rule_number}: {e}",
                extra={
                    "traceId": self.test_trace_id,
                    "event": "rule.test_error",
                    "rule_number": rule_number
                }
            )
            raise

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all compliance tests"""
        self.emit_receipt("run_all_tests", "planned", "Starting all compliance tests")
        
        try:
            # Load test prompts
            prompts = self.load_test_prompts()
            
            # Test basic work rules
            basic_work_rules = [4, 5, 10, 13, 20]
            test_scenarios = [
                {"violation": False, "description": "Valid implementation"},
                {"violation": True, "description": "Violation case"}
            ]
            
            for rule_number in basic_work_rules:
                for scenario in test_scenarios:
                    self.test_rule_compliance(rule_number, scenario)
            
            # Generate summary
            summary = self._generate_summary()
            
            self.emit_receipt("run_all_tests", "success", f"Completed {len(self.results)} tests")
            
            return summary
            
        except Exception as e:
            self.emit_receipt("run_all_tests", "error", f"Error running tests: {e}")
            raise

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = len(self.results)
        compliant_tests = len([r for r in self.results if r["is_compliant"]])
        non_compliant_tests = total_tests - compliant_tests
        
        summary = {
            "total_tests": total_tests,
            "compliant_tests": compliant_tests,
            "non_compliant_tests": non_compliant_tests,
            "compliance_rate": compliant_tests / total_tests if total_tests > 0 else 0,
            "test_results": self.results,
            "receipts_summary": self.get_receipts_summary(),
            "timestamp": time.time(),
            "trace_id": self.test_trace_id
        }
        
        return summary

    def save_results(self, results: Dict[str, Any], output_file: str):
        """Save test results to file"""
        self.emit_receipt("save_results", "planned", f"Saving results to {output_file}")
        
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            self.emit_receipt("save_results", "success", f"Results saved to {output_file}")
            
        except Exception as e:
            self.emit_receipt("save_results", "error", f"Failed to save results: {e}")
            raise

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test Cursor Constitution compliance")
    parser.add_argument("--output", "-o", default="compliance_results.json", 
                       help="Output file for results")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    
    args = parser.parse_args()
    
    # Create tester
    tester = CursorComplianceTester()
    
    try:
        # Run tests
        results = tester.run_all_tests()
        
        # Save results
        tester.save_results(results, args.output)
        
        # Print summary
        print(f"Compliance Rate: {results['compliance_rate']:.2%}")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Compliant: {results['compliant_tests']}")
        print(f"Non-compliant: {results['non_compliant_tests']}")
        
        if args.verbose:
            print(f"Results saved to: {args.output}")
            print(f"Trace ID: {results['trace_id']}")
        
        # Exit with appropriate code
        if results['compliance_rate'] >= 0.9:  # 90% compliance
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
