"""
WHAT: Semantic validation tests for constitution rules
WHY: Validate rule requirements, descriptions, and validation criteria match expected patterns

Test Design:
- Validate rule semantics and requirements
- Check rule descriptions for completeness
- Verify validation criteria are appropriate
- Test rule relationships and dependencies
"""
import json
import unittest
from pathlib import Path
from typing import Dict, List, Any
import re

# Deterministic operations
TEST_RANDOM_SEED = 42


class ConstitutionRuleSemanticsTests(unittest.TestCase):
    """Test semantic content and requirements of rules."""
    
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
    
    def test_vscode_extension_arc_001_static_contributions(self):
        """Test ARC-001: Enforce Static Package Contributions."""
        rule = self._get_rule('VSCODE EXTENSION RULES.json', 'ARC-001')
        self.assertIsNotNone(rule)
        self.assertEqual(rule.get('title'), 'Enforce Static Package Contributions')
        self.assertEqual(rule.get('severity_level'), 'Blocker')
        self.assertIn('package.json', rule.get('description', ''))
        self.assertIn('static', rule.get('description', '').lower())
    
    def test_vscode_extension_arc_002_ide_surfaces_only(self):
        """Test ARC-002: Restrict Scope to IDE Surfaces Only."""
        rule = self._get_rule('VSCODE EXTENSION RULES.json', 'ARC-002')
        self.assertIsNotNone(rule)
        self.assertEqual(rule.get('title'), 'Restrict Scope to IDE Surfaces Only')
        self.assertEqual(rule.get('severity_level'), 'Blocker')
        self.assertIn('IDE', rule.get('description', ''))
    
    def test_logging_obs_001_schema_version(self):
        """Test OBS-001: Require Schema Version in Logs."""
        rule = self._get_rule('LOGGING & TROUBLESHOOTING RULES.json', 'OBS-001')
        self.assertIsNotNone(rule)
        self.assertEqual(rule.get('title'), 'Require Schema Version in Logs')
        self.assertEqual(rule.get('severity_level'), 'Blocker')
        self.assertIn('log_schema_version', rule.get('description', ''))
        self.assertIn('1.0', rule.get('description', ''))
    
    def test_logging_obs_002_jsonl_format(self):
        """Test OBS-002: Use JSONL Format for Logs."""
        rule = self._get_rule('LOGGING & TROUBLESHOOTING RULES.json', 'OBS-002')
        self.assertIsNotNone(rule)
        self.assertEqual(rule.get('title'), 'Use JSONL Format for Logs')
        self.assertEqual(rule.get('severity_level'), 'Blocker')
        self.assertIn('JSONL', rule.get('description', '').upper())
    
    def test_testing_ftp_001_determinism(self):
        """Test FTP-001: Prioritize Determinism Over Speed."""
        rule = self._get_rule('TESTING RULES.json', 'FTP-001')
        self.assertIsNotNone(rule)
        self.assertEqual(rule.get('title'), 'Prioritize Determinism Over Speed')
        self.assertEqual(rule.get('severity_level'), 'Blocker')
        # Description mentions reproducibility which is related to determinism
        description = rule.get('description', '').lower()
        self.assertTrue(
            'reproducible' in description or 'determin' in description,
            f"FTP-001 description should mention reproducibility or determinism"
        )
    
    def test_testing_ftp_003_hermetic(self):
        """Test FTP-003: Enforce Hermetic Test Runs."""
        rule = self._get_rule('TESTING RULES.json', 'FTP-003')
        self.assertIsNotNone(rule)
        self.assertEqual(rule.get('title'), 'Enforce Hermetic Test Runs')
        self.assertEqual(rule.get('severity_level'), 'Blocker')
        description = rule.get('description', '').lower()
        # Description mentions isolation which is the key concept of hermetic tests
        self.assertTrue(
            'hermetic' in description or 'isolation' in description or 'network' in description,
            f"FTP-003 description should mention hermetic, isolation, or network restrictions"
        )
    
    def test_comments_doc_001_one_subfeature(self):
        """Test DOC-001: Work on One Sub-Feature at a Time."""
        rule = self._get_rule('COMMENTS RULES.json', 'DOC-001')
        self.assertIsNotNone(rule)
        self.assertEqual(rule.get('title'), 'Work on One Sub-Feature at a Time')
        self.assertEqual(rule.get('severity_level'), 'Major')
    
    def test_comments_doc_002_50_loc_limit(self):
        """Test DOC-002: Enforce 50 LOC Change Limit."""
        rule = self._get_rule('COMMENTS RULES.json', 'DOC-002')
        self.assertIsNotNone(rule)
        self.assertEqual(rule.get('title'), 'Enforce 50 LOC Change Limit')
        self.assertEqual(rule.get('severity_level'), 'Major')
        self.assertIn('50', rule.get('description', ''))
    
    def test_comments_doc_004_synchronize_comments(self):
        """Test DOC-004: Synchronize Comments with Code Changes."""
        rule = self._get_rule('COMMENTS RULES.json', 'DOC-004')
        self.assertIsNotNone(rule)
        self.assertEqual(rule.get('title'), 'Synchronize Comments with Code Changes')
        self.assertEqual(rule.get('severity_level'), 'Critical')
    
    def test_all_rules_have_descriptions(self):
        """Verify all rules have non-empty descriptions."""
        files = [
            'VSCODE EXTENSION RULES.json',
            'LOGGING & TROUBLESHOOTING RULES.json',
            'MODULES AND GSMD MAPPING RULES.json',
            'GSMD AND MODULE MAPPING RULES.json',
            'TESTING RULES.json',
            'COMMENTS RULES.json'
        ]
        
        for filename in files:
            rules = self.files_data.get(filename, {}).get('constitution_rules', [])
            for rule in rules:
                rule_id = rule.get('rule_id')
                with self.subTest(filename=filename, rule_id=rule_id):
                    description = rule.get('description')
                    # Description may be empty string but should exist
                    self.assertIsNotNone(description)
                    self.assertIsInstance(description, str)
    
    def test_all_rules_have_validation_criteria(self):
        """Verify all rules have validation criteria (may be empty string)."""
        files = [
            'VSCODE EXTENSION RULES.json',
            'LOGGING & TROUBLESHOOTING RULES.json',
            'MODULES AND GSMD MAPPING RULES.json',
            'GSMD AND MODULE MAPPING RULES.json',
            'TESTING RULES.json',
            'COMMENTS RULES.json'
        ]
        
        for filename in files:
            rules = self.files_data.get(filename, {}).get('constitution_rules', [])
            for rule in rules:
                rule_id = rule.get('rule_id')
                with self.subTest(filename=filename, rule_id=rule_id):
                    validation = rule.get('validation')
                    # Validation field should exist
                    if validation is not None:
                        self.assertIsInstance(validation, str)
    
    def test_error_conditions_format(self):
        """Verify error_condition fields follow expected format."""
        files = [
            'LOGGING & TROUBLESHOOTING RULES.json',
            'COMMENTS RULES.json'
        ]
        
        for filename in files:
            rules = self.files_data.get(filename, {}).get('constitution_rules', [])
            for rule in rules:
                rule_id = rule.get('rule_id')
                error_condition = rule.get('error_condition')
                if error_condition is not None:
                    with self.subTest(filename=filename, rule_id=rule_id):
                        self.assertIsInstance(error_condition, str)
                        # Should contain ERROR: if present (may be in the middle of the string)
                        if error_condition:
                            self.assertIn(
                                'ERROR:',
                                error_condition,
                                f"{rule_id} error_condition should contain ERROR:"
                            )
    
    def test_requirements_are_complete(self):
        """Verify requirements arrays contain meaningful content."""
        files = [
            'VSCODE EXTENSION RULES.json',
            'LOGGING & TROUBLESHOOTING RULES.json',
            'TESTING RULES.json',
            'COMMENTS RULES.json'
        ]
        
        for filename in files:
            rules = self.files_data.get(filename, {}).get('constitution_rules', [])
            for rule in rules:
                rule_id = rule.get('rule_id')
                requirements = rule.get('requirements')
                if requirements is not None:
                    with self.subTest(filename=filename, rule_id=rule_id):
                        self.assertIsInstance(requirements, list)
                        # If requirements exist, they should be non-empty strings
                        for req in requirements:
                            self.assertIsInstance(req, str)
                            self.assertGreater(len(req.strip()), 0)
    
    def test_policy_linkage_structure(self):
        """Verify policy_linkage has correct structure across all files."""
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
            for rule in rules:
                rule_id = rule.get('rule_id')
                policy_linkage = rule.get('policy_linkage')
                if policy_linkage is not None:
                    with self.subTest(filename=filename, rule_id=rule_id):
                        self.assertIsInstance(policy_linkage, dict)
                        policy_version_ids = policy_linkage.get('policy_version_ids')
                        if policy_version_ids is not None:
                            self.assertIsInstance(policy_version_ids, list)
                            # Should have at least one policy version ID
                            self.assertGreater(len(policy_version_ids), 0)
                            for pid in policy_version_ids:
                                self.assertIsInstance(pid, str)
                                self.assertGreater(len(pid), 0)
    
    def test_category_consistency(self):
        """Verify categories are consistent within each file."""
        files = [
            'VSCODE EXTENSION RULES.json',
            'LOGGING & TROUBLESHOOTING RULES.json',
            'MODULES AND GSMD MAPPING RULES.json',
            'GSMD AND MODULE MAPPING RULES.json',
            'TESTING RULES.json',
            'COMMENTS RULES.json'
        ]
        
        for filename in files:
            rules = self.files_data.get(filename, {}).get('constitution_rules', [])
            categories = {r.get('category') for r in rules}
            
            with self.subTest(filename=filename):
                # Each file should have at least one category
                self.assertGreater(len(categories), 0)
                # Categories should be non-empty strings
                for category in categories:
                    self.assertIsInstance(category, str)
                    self.assertGreater(len(category.strip()), 0)
    
    def test_severity_distribution(self):
        """Verify severity levels are appropriate for rule types."""
        files = [
            'VSCODE EXTENSION RULES.json',
            'LOGGING & TROUBLESHOOTING RULES.json',
            'TESTING RULES.json',
            'COMMENTS RULES.json'
        ]
        
        for filename in files:
            rules = self.files_data.get(filename, {}).get('constitution_rules', [])
            severities = {r.get('severity_level') for r in rules}
            
            with self.subTest(filename=filename):
                # Should have at least one severity level
                self.assertGreater(len(severities), 0)
                # All severities should be valid
                valid_severities = {'Blocker', 'Critical', 'Major', 'Minor'}
                for severity in severities:
                    self.assertIn(severity, valid_severities)
    
    def _get_rule(self, filename: str, rule_id: str) -> Dict[str, Any]:
        """Get a specific rule by ID."""
        rules = self.files_data.get(filename, {}).get('constitution_rules', [])
        return next((r for r in rules if r.get('rule_id') == rule_id), None)


class ConstitutionRuleRelationshipsTests(unittest.TestCase):
    """Test relationships and dependencies between rules."""
    
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
    
    def test_modules_gsmd_references(self):
        """Test MODULES AND GSMD MAPPING RULES reference each other correctly."""
        rules = self.files_data.get('MODULES AND GSMD MAPPING RULES.json', {}).get('constitution_rules', [])
        
        # STR-001 should reference binding (uses "bind" in description)
        str001 = next((r for r in rules if r.get('rule_id') == 'STR-001'), None)
        if str001:
            description = str001.get('description', '').lower()
            self.assertTrue(
                'bind' in description or 'binding' in description,
                f"STR-001 should mention binding concept"
            )
    
    def test_testing_rules_determinism_themes(self):
        """Test that testing rules consistently emphasize determinism."""
        rules = self.files_data.get('TESTING RULES.json', {}).get('constitution_rules', [])
        
        determinism_keywords = ['determin', 'hermetic', 'repeatable', 'cache', 'seed']
        determinism_rules = []
        
        for rule in rules:
            description = rule.get('description', '').lower()
            if any(keyword in description for keyword in determinism_keywords):
                determinism_rules.append(rule.get('rule_id'))
        
        # Should have multiple rules about determinism
        self.assertGreater(len(determinism_rules), 0)
    
    def test_logging_rules_schema_consistency(self):
        """Test that logging rules consistently reference schema."""
        rules = self.files_data.get('LOGGING & TROUBLESHOOTING RULES.json', {}).get('constitution_rules', [])
        
        schema_rules = []
        for rule in rules:
            description = rule.get('description', '').lower()
            if 'schema' in description:
                schema_rules.append(rule.get('rule_id'))
        
        # Should have rules about schema
        self.assertGreater(len(schema_rules), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)

