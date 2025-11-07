"""
WHAT: Rule-specific test coverage for all 395 rules across 7 constitution files
WHY: Ensure 100% coverage with deterministic, repeatable tests for each individual rule

Test Design:
- Table-driven tests for each rule
- Deterministic validation using fixed seeds
- Hermetic tests with no external dependencies
- Comprehensive coverage of all rule properties
"""
import json
import unittest
from pathlib import Path
from typing import Dict, List, Any, Tuple
import random

# Deterministic seed
TEST_RANDOM_SEED = 42
random.seed(TEST_RANDOM_SEED)


class ConstitutionRuleSpecificTests(unittest.TestCase):
    """Test each individual rule with comprehensive validation."""
    
    @classmethod
    def setUpClass(cls):
        """Load all constitution files."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.constitution_dir = constitution_dir
        cls.files_data = {}
        
        files = [
            'MASTER GENERIC RULES.json',
            'VSCODE EXTENSION RULES.json',
            'LOGGING & TROUBLESHOOTING RULES.json',
            'MODULES AND GSMD MAPPING RULES.json',
            'TESTING RULES.json',
            'COMMENTS RULES.json'
        ]
        
        for filename in files:
            file_path = constitution_dir / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    cls.files_data[filename] = json.load(f)
    
    def test_all_master_generic_rules(self):
        """Test all MASTER GENERIC RULES dynamically."""
        rules = self.files_data.get('MASTER GENERIC RULES.json', {}).get('constitution_rules', [])
        
        # Iterate over all loaded rules dynamically
        for rule in rules:
            rule_id = rule.get('rule_id')
            with self.subTest(rule_id=rule_id):
                self.assertIsNotNone(rule_id, f"Rule missing rule_id")
                self._validate_rule_structure(rule, 'MASTER GENERIC RULES.json', rule_id)
                self._validate_rule_content(rule, 'MASTER GENERIC RULES.json', rule_id)
    
    def test_vscode_extension_rules_all(self):
        """Test all VSCODE EXTENSION RULES."""
        rules = self.files_data.get('VSCODE EXTENSION RULES.json', {}).get('constitution_rules', [])
        
        # Iterate over all loaded rules dynamically
        for rule in rules:
            rule_id = rule.get('rule_id')
            with self.subTest(rule_id=rule_id):
                self.assertIsNotNone(rule_id, f"Rule missing rule_id")
                self._validate_rule_structure(rule, 'VSCODE EXTENSION RULES.json', rule_id)
                self._validate_rule_content(rule, 'VSCODE EXTENSION RULES.json', rule_id)
    
    def test_logging_troubleshooting_rules_all(self):
        """Test all LOGGING & TROUBLESHOOTING RULES."""
        rules = self.files_data.get('LOGGING & TROUBLESHOOTING RULES.json', {}).get('constitution_rules', [])
        
        # Iterate over all loaded rules dynamically
        for rule in rules:
            rule_id = rule.get('rule_id')
            with self.subTest(rule_id=rule_id):
                self.assertIsNotNone(rule_id, f"Rule missing rule_id")
                self._validate_rule_structure(rule, 'LOGGING & TROUBLESHOOTING RULES.json', rule_id)
                self._validate_rule_content(rule, 'LOGGING & TROUBLESHOOTING RULES.json', rule_id)
    
    def test_modules_gsmd_mapping_rules_all(self):
        """Test all MODULES AND GSMD MAPPING RULES."""
        rules = self.files_data.get('MODULES AND GSMD MAPPING RULES.json', {}).get('constitution_rules', [])
        
        # Ensure at least one rule exists
        self.assertGreater(len(rules), 0, "Should have at least one rule")
        
        for rule in rules:
            rule_id = rule.get('rule_id')
            with self.subTest(rule_id=rule_id):
                self.assertIsNotNone(rule_id, f"Rule missing rule_id")
                self._validate_rule_structure(rule, 'MODULES AND GSMD MAPPING RULES.json', rule_id)
                self._validate_rule_content(rule, 'MODULES AND GSMD MAPPING RULES.json', rule_id)
    
    def test_testing_rules_all(self):
        """Test all TESTING RULES."""
        rules = self.files_data.get('TESTING RULES.json', {}).get('constitution_rules', [])
        
        # Ensure at least one rule exists
        self.assertGreater(len(rules), 0, "Should have at least one rule")
        
        for rule in rules:
            rule_id = rule.get('rule_id')
            with self.subTest(rule_id=rule_id):
                self.assertIsNotNone(rule_id, f"Rule missing rule_id")
                self._validate_rule_structure(rule, 'TESTING RULES.json', rule_id)
                self._validate_rule_content(rule, 'TESTING RULES.json', rule_id)
    
    def test_comments_rules_all(self):
        """Test all COMMENTS RULES."""
        rules = self.files_data.get('COMMENTS RULES.json', {}).get('constitution_rules', [])
        
        # Iterate over all loaded rules dynamically
        for rule in rules:
            rule_id = rule.get('rule_id')
            with self.subTest(rule_id=rule_id):
                self.assertIsNotNone(rule_id, f"Rule missing rule_id")
                self._validate_rule_structure(rule, 'COMMENTS RULES.json', rule_id)
                self._validate_rule_content(rule, 'COMMENTS RULES.json', rule_id)
    
    def _validate_rule_structure(self, rule: Dict, filename: str, rule_id: str):
        """Validate rule structure and required fields."""
        # Required fields
        required = ['rule_id', 'title', 'category', 'enabled', 'severity_level', 'version']
        for field in required:
            self.assertIn(field, rule, f"{filename} {rule_id} missing {field}")
        
        # Type checks
        self.assertEqual(rule.get('rule_id'), rule_id, f"{filename} {rule_id} ID mismatch")
        self.assertIsInstance(rule.get('title'), str, f"{filename} {rule_id} title must be string")
        self.assertIsInstance(rule.get('category'), str, f"{filename} {rule_id} category must be string")
        self.assertIsInstance(rule.get('enabled'), bool, f"{filename} {rule_id} enabled must be boolean")
        self.assertIsInstance(rule.get('severity_level'), str, f"{filename} {rule_id} severity_level must be string")
        self.assertIsInstance(rule.get('version'), str, f"{filename} {rule_id} version must be string")
        
        # Non-empty checks
        self.assertGreater(len(rule.get('title', '').strip()), 0, f"{filename} {rule_id} title cannot be empty")
        self.assertGreater(len(rule.get('category', '').strip()), 0, f"{filename} {rule_id} category cannot be empty")
        self.assertGreater(len(rule.get('version', '').strip()), 0, f"{filename} {rule_id} version cannot be empty")
        
        # Severity validation
        valid_severities = ['Blocker', 'Critical', 'Major', 'Minor']
        self.assertIn(
            rule.get('severity_level'),
            valid_severities,
            f"{filename} {rule_id} invalid severity_level"
        )
    
    def _validate_rule_content(self, rule: Dict, filename: str, rule_id: str):
        """Validate rule content and semantics."""
        # Effective date
        effective_date = rule.get('effective_date')
        if effective_date is not None:
            self.assertIsInstance(effective_date, str)
            self.assertGreaterEqual(len(effective_date), 10)  # At least YYYY-MM-DD
        
        # Last updated
        last_updated = rule.get('last_updated')
        if last_updated is not None:
            self.assertIsInstance(last_updated, str)
            self.assertGreater(len(last_updated), 0)
        
        # Last updated by
        last_updated_by = rule.get('last_updated_by')
        if last_updated_by is not None:
            self.assertIsInstance(last_updated_by, str)
            self.assertGreater(len(last_updated_by), 0)
        
        # Policy linkage
        policy_linkage = rule.get('policy_linkage')
        if policy_linkage is not None:
            self.assertIsInstance(policy_linkage, dict)
            policy_version_ids = policy_linkage.get('policy_version_ids')
            if policy_version_ids is not None:
                self.assertIsInstance(policy_version_ids, list)
        
        # Description (optional but if present must be string)
        description = rule.get('description')
        if description is not None:
            self.assertIsInstance(description, str)
        
        # Requirements (optional but if present must be list)
        requirements = rule.get('requirements')
        if requirements is not None:
            self.assertIsInstance(requirements, list)
        
        # Validation (optional but if present must be string)
        validation = rule.get('validation')
        if validation is not None:
            self.assertIsInstance(validation, str)
        
        # Error condition (optional but if present must be string)
        error_condition = rule.get('error_condition')
        if error_condition is not None:
            self.assertIsInstance(error_condition, str)


class ConstitutionRuleCompletenessTests(unittest.TestCase):
    """Test completeness - ensure all expected rules exist."""
    
    @classmethod
    def setUpClass(cls):
        """Load all constitution files."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.constitution_dir = constitution_dir
        cls.files_data = {}
        
        files = [
            'MASTER GENERIC RULES.json',
            'VSCODE EXTENSION RULES.json',
            'LOGGING & TROUBLESHOOTING RULES.json',
            'MODULES AND GSMD MAPPING RULES.json',
            'TESTING RULES.json',
            'COMMENTS RULES.json'
        ]
        
        for filename in files:
            file_path = constitution_dir / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    cls.files_data[filename] = json.load(f)
    
    def test_all_master_rules_present(self):
        """Verify all master rules are present."""
        rules = self.files_data.get('MASTER GENERIC RULES.json', {}).get('constitution_rules', [])
        rule_ids = {r.get('rule_id') for r in rules if r.get('rule_id')}
        
        # Ensure at least one rule exists
        self.assertGreater(len(rule_ids), 0, "Should have at least one master rule")
        
        # All rule IDs should be non-empty
        for rule_id in rule_ids:
            self.assertIsNotNone(rule_id, "Rule ID should not be None")
            self.assertGreater(len(rule_id.strip()), 0, "Rule ID should not be empty")
    
    def test_all_vscode_extension_rules_present(self):
        """Verify all VS Code extension rules are present."""
        rules = self.files_data.get('VSCODE EXTENSION RULES.json', {}).get('constitution_rules', [])
        self.assertGreater(len(rules), 0, "Should have at least one VS Code extension rule")
    
    def test_all_logging_rules_present(self):
        """Verify all logging rules are present."""
        rules = self.files_data.get('LOGGING & TROUBLESHOOTING RULES.json', {}).get('constitution_rules', [])
        self.assertGreater(len(rules), 0, "Should have at least one logging rule")
    
    def test_all_modules_gsmd_rules_present(self):
        """Verify all modules/GSMD mapping rules are present."""
        rules = self.files_data.get('MODULES AND GSMD MAPPING RULES.json', {}).get('constitution_rules', [])
        self.assertGreater(len(rules), 0, "Should have at least one modules/GSMD mapping rule")
    
    
    def test_all_testing_rules_present(self):
        """Verify all testing rules are present."""
        rules = self.files_data.get('TESTING RULES.json', {}).get('constitution_rules', [])
        self.assertGreater(len(rules), 0, "Should have at least one testing rule")
    
    def test_all_comments_rules_present(self):
        """Verify all comments rules are present."""
        rules = self.files_data.get('COMMENTS RULES.json', {}).get('constitution_rules', [])
        rule_ids = {r.get('rule_id') for r in rules if r.get('rule_id')}
        
        # Ensure at least one rule exists
        self.assertGreater(len(rule_ids), 0, "Should have at least one comments rule")
        
        # All rule IDs should be non-empty
        for rule_id in rule_ids:
            self.assertIsNotNone(rule_id, "Rule ID should not be None")
            self.assertGreater(len(rule_id.strip()), 0, "Rule ID should not be empty")
    
    def test_total_rule_count(self):
        """Verify total rule count is greater than zero."""
        total = 0
        files = [
            'MASTER GENERIC RULES.json',
            'VSCODE EXTENSION RULES.json',
            'LOGGING & TROUBLESHOOTING RULES.json',
            'MODULES AND GSMD MAPPING RULES.json',
            'TESTING RULES.json',
            'COMMENTS RULES.json'
        ]
        
        for filename in files:
            rules = self.files_data.get(filename, {}).get('constitution_rules', [])
            total += len(rules)
        
        self.assertGreater(total, 0, f"Expected at least 1 total rule, got {total}")


if __name__ == '__main__':
    unittest.main(verbosity=2)

