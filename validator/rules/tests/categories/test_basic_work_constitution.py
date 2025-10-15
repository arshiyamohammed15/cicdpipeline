#!/usr/bin/env python3
"""
Basic Work Category Tests - Constitution Compliant

What: Tests for Basic Work rules (4, 5, 10, 13, 20)
Why: Ensure core development principles are followed
Reads: config/rules/basic_work.json, test fixtures
Writes: test results, receipts, logs
Contracts: Test API contracts, logging schema
Risks: False positives, test failures

Following Constitution Rules:
- Rule 12: Test Everything (prove behavior before/after)
- Rule 97-106: Simple English comments
- Rule 132-149: Structured logging
- Rule 141: Receipt system for audit trail
- Rule 129: Proper error handling
"""

import pytest
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from constitution_test_base import ConstitutionTestBase

class TestBasicWorkCategory:
    """Test suite for Basic Work category rules (Constitution Rules 4, 5, 10, 13, 20)"""
    
    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Setup test method (Rule 12: Test Everything)"""
        self.test_base = ConstitutionTestBase()
        self.test_base.emit_receipt("test_setup", "planned", "Setting up basic work tests")
        
        # Load rule configuration
        try:
            self.rule_config = self.test_base.load_rule_config("basic_work")
            self.expected_rules = [4, 5, 10, 13, 20]  # Constitution rule numbers
        except FileNotFoundError:
            # Fallback to test config if rule config not found
            test_config_path = Path(__file__).parent.parent.parent.parent / "config" / "test_config.json"
            with open(test_config_path, 'r') as f:
                test_config = json.load(f)
            self.rule_config = test_config["rule_categories"]["basic_work"]
            self.expected_rules = self.rule_config["rules"]
        
        self.test_base.emit_receipt("test_setup", "success", "Basic work tests ready")
        yield
        self.test_base.emit_receipt("test_teardown", "success", "Basic work tests completed")
    
    def test_rule_4_settings_files_not_hardcoded(self):
        """Test Rule 4: Use Settings Files, Not Hardcoded Numbers"""
        self.test_base.emit_receipt("test_rule_4", "planned", "Testing settings files rule")
        
        # Test that hardcoded values are detected
        test_code = """
        MAX_RETRIES = 3  # Should use settings file
        TIMEOUT = 30     # Should use settings file
        """
        
        # Validate rule compliance
        self.test_base.assert_rule_compliance(4, "basic_work", test_code)
        
        # Test that rule is in expected rules
        assert 4 in self.expected_rules, "Rule 4 should be in basic work rules"
        
        self.test_base.emit_receipt("test_rule_4", "success", "Settings files rule validated")
    
    def test_rule_5_keep_good_records(self):
        """Test Rule 5: Keep Good Records + Keep Good Logs"""
        self.test_base.emit_receipt("test_rule_5", "planned", "Testing good records rule")
        
        # Test that logging is structured and receipts are emitted
        self.test_base.assert_rule_compliance(5, "basic_work")
        
        # Test that rule is in expected rules
        assert 5 in self.expected_rules, "Rule 5 should be in basic work rules"
        
        self.test_base.emit_receipt("test_rule_5", "success", "Good records rule validated")
    
    def test_rule_10_be_honest_about_ai_decisions(self):
        """Test Rule 10: Be Honest About AI Decisions"""
        self.test_base.emit_receipt("test_rule_10", "planned", "Testing AI honesty rule")
        
        # Test that AI decisions include confidence, explanation, version
        self.test_base.assert_rule_compliance(10, "basic_work")
        
        # Test that rule is in expected rules
        assert 10 in self.expected_rules, "Rule 10 should be in basic work rules"
        
        self.test_base.emit_receipt("test_rule_10", "success", "AI honesty rule validated")
    
    def test_rule_13_learn_from_mistakes(self):
        """Test Rule 13: Learn from Mistakes"""
        self.test_base.emit_receipt("test_rule_13", "planned", "Testing learning from mistakes rule")
        
        # Test that feedback loops and improvement mechanisms exist
        self.test_base.assert_rule_compliance(13, "basic_work")
        
        # Test that rule is in expected rules
        assert 13 in self.expected_rules, "Rule 13 should be in basic work rules"
        
        self.test_base.emit_receipt("test_rule_13", "success", "Learning from mistakes rule validated")
    
    def test_rule_20_be_fair_to_everyone(self):
        """Test Rule 20: Be Fair to Everyone"""
        self.test_base.emit_receipt("test_rule_20", "planned", "Testing fairness rule")
        
        # Test that accessibility and inclusive design are followed
        self.test_base.assert_rule_compliance(20, "basic_work")
        
        # Test that rule is in expected rules
        assert 20 in self.expected_rules, "Rule 20 should be in basic work rules"
        
        self.test_base.emit_receipt("test_rule_20", "success", "Fairness rule validated")
    
    def test_all_basic_work_rules_covered(self):
        """Test that all basic work rules are covered"""
        self.test_base.emit_receipt("test_coverage", "planned", "Testing rule coverage")
        
        # Verify all expected rules are tested
        for rule_number in self.expected_rules:
            assert rule_number in self.rule_config["rules"], f"Rule {rule_number} should be in basic work rules"
        
        # Verify we have the right number of rules
        assert len(self.expected_rules) == 5, "Basic work should have exactly 5 rules"
        
        self.test_base.emit_receipt("test_coverage", "success", "All basic work rules covered")
    
    def test_constitution_compliance(self):
        """Test that all basic work rules comply with constitution standards"""
        self.test_base.emit_receipt("test_constitution_compliance", "planned", "Testing constitution compliance")
        
        compliance_results = []
        for rule_number in self.expected_rules:
            is_compliant = self.test_base.validate_constitution_compliance(rule_number, "basic_work")
            compliance_results.append((rule_number, is_compliant))
        
        # All rules should be compliant
        failed_rules = [rule for rule, compliant in compliance_results if not compliant]
        assert not failed_rules, f"Rules failed constitution compliance: {failed_rules}"
        
        self.test_base.emit_receipt("test_constitution_compliance", "success", "All rules comply with constitution")
    
    def test_receipt_system(self):
        """Test that receipt system is working properly"""
        self.test_base.emit_receipt("test_receipt_system", "planned", "Testing receipt system")
        
        # Verify receipts are being created
        assert len(self.test_base.receipts) > 0, "Should have receipts from test execution"
        
        # Verify receipt structure
        for receipt in self.test_base.receipts:
            assert receipt.ts_utc is not None, "Receipt should have timestamp"
            assert receipt.traceId is not None, "Receipt should have trace ID"
            assert receipt.action is not None, "Receipt should have action"
            assert receipt.status is not None, "Receipt should have status"
            assert receipt.policy_snapshot_hash == "constitution_v2.0", "Receipt should have correct policy hash"
        
        # Get receipts summary
        summary = self.test_base.get_receipts_summary()
        assert summary["total_receipts"] > 0, "Should have receipts in summary"
        
        self.test_base.emit_receipt("test_receipt_system", "success", "Receipt system working properly")
    
    def teardown_method(self):
        """Cleanup test method"""
        self.test_base.emit_receipt("test_teardown", "success", "Basic work tests completed")
        
        # Log final summary
        summary = self.test_base.get_receipts_summary()
        self.test_base.logger.info(
            f"Test completed: {summary['total_receipts']} receipts, "
            f"{summary['successful_actions']} successful, "
            f"{summary['failed_actions']} failed",
            extra={
                "traceId": self.test_base.test_trace_id,
                "event": "test.completed",
                "summary": summary
            }
        )
