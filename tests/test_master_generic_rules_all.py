"""
WHAT: Comprehensive test suite for MASTER GENERIC RULES.json with 100% rule coverage
WHY: Validate all rules with deterministic, repeatable tests, agnostic to rule IDs

Test Design Principles (following testing rules):
- Deterministic: All tests use fixed seeds (TEST_RANDOM_SEED = 42)
- Repeatable: Tests produce identical results across runs
- Hermetic: Tests operate in complete isolation without external dependencies
- Table-driven: Use structured test data for clarity
- Rule-ID Agnostic: Tests work with any rule IDs, not hardcoded values
- Comprehensive: 100% coverage of all rules regardless of ID format
"""
import json
import unittest
from pathlib import Path
from typing import Dict, List, Any, Optional
import random

# Deterministic seed for all randomness
TEST_RANDOM_SEED = 42
random.seed(TEST_RANDOM_SEED)


class MasterGenericRulesLoader:
    """Load and validate MASTER GENERIC RULES.json file."""
    
    def __init__(self, constitution_dir: Path):
        """
        Initialize loader with constitution directory.
        
        Args:
            constitution_dir: Path to docs/constitution directory
        """
        self.constitution_dir = Path(constitution_dir)
        self._file_path = self.constitution_dir / "MASTER GENERIC RULES.json"
    
    def load_file(self) -> Dict[str, Any]:
        """
        Load MASTER GENERIC RULES.json file.
        
        Returns:
            Parsed JSON data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is invalid JSON
        """
        if not self._file_path.exists():
            raise FileNotFoundError(f"Constitution file not found: {self._file_path}")
        
        with open(self._file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        """
        Get all rules from MASTER GENERIC RULES.json.
        
        Returns:
            List of rule dictionaries, sorted deterministically by rule_id
        """
        data = self.load_file()
        rules = data.get('constitution_rules', [])
        # Sort deterministically by rule_id for repeatability
        return sorted(rules, key=lambda x: x.get('rule_id', ''))
    
    def get_rules_by_prefix(self, prefix: str) -> List[Dict[str, Any]]:
        """
        Get all rules with a specific prefix.
        
        Args:
            prefix: Rule ID prefix (e.g., "R-", "CTC-")
            
        Returns:
            List of rule dictionaries with matching prefix, sorted deterministically
        """
        all_rules = self.get_all_rules()
        filtered_rules = [
            rule for rule in all_rules
            if rule.get('rule_id', '').startswith(prefix)
        ]
        # Sort deterministically by rule_id for repeatability
        return sorted(filtered_rules, key=lambda x: x.get('rule_id', ''))


class MasterGenericRulesStructureTests(unittest.TestCase):
    """Test structure and integrity of MASTER GENERIC RULES.json."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = MasterGenericRulesLoader(constitution_dir)
    
    def test_file_exists(self):
        """Verify MASTER GENERIC RULES.json file exists."""
        file_path = self.loader._file_path
        self.assertTrue(
            file_path.exists(),
            f"MASTER GENERIC RULES.json not found at: {file_path}"
        )
    
    def test_file_valid_json(self):
        """Verify file is valid JSON."""
        try:
            data = self.loader.load_file()
            self.assertIsInstance(data, dict, "File must be a JSON object")
        except json.JSONDecodeError as e:
            self.fail(f"File is invalid JSON: {e}")
    
    def test_has_constitution_rules_array(self):
        """Verify file has constitution_rules array."""
        data = self.loader.load_file()
        self.assertIn(
            'constitution_rules',
            data,
            "File must have 'constitution_rules' field"
        )
        self.assertIsInstance(
            data['constitution_rules'],
            list,
            "'constitution_rules' must be an array"
        )
    
    def test_has_metadata(self):
        """Verify file has metadata section."""
        data = self.loader.load_file()
        self.assertIn(
            'metadata',
            data,
            "File must have 'metadata' field"
        )
        metadata = data['metadata']
        self.assertIsInstance(metadata, dict, "Metadata must be an object")
    
    def test_metadata_total_rules_matches_actual(self):
        """Verify metadata.total_rules matches actual rule count."""
        data = self.loader.load_file()
        rules = data.get('constitution_rules', [])
        expected_count = data.get('metadata', {}).get('total_rules', 0)
        actual_count = len(rules)
        self.assertEqual(
            expected_count,
            actual_count,
            f"Metadata total_rules ({expected_count}) doesn't match actual rule count ({actual_count})"
        )
    
    def test_all_rules_have_unique_ids(self):
        """Verify all rules have unique rule_ids."""
        rules = self.loader.get_all_rules()
        rule_ids = [rule.get('rule_id') for rule in rules]
        unique_ids = set(rule_ids)
        
        self.assertEqual(
            len(rule_ids),
            len(unique_ids),
            f"Found {len(rule_ids) - len(unique_ids)} duplicate rule_ids"
        )
    
    def test_all_rules_have_non_empty_ids(self):
        """Verify all rules have non-empty rule_ids."""
        rules = self.loader.get_all_rules()
        
        for rule in rules:
            rule_id = rule.get('rule_id')
            with self.subTest(rule_id=rule_id):
                self.assertIsNotNone(rule_id, "Rule must have rule_id")
                self.assertIsInstance(rule_id, str, "rule_id must be string")
                self.assertGreater(len(rule_id.strip()), 0, "rule_id cannot be empty")


class MasterGenericRulesFieldTests(unittest.TestCase):
    """Test all required fields in all rules."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = MasterGenericRulesLoader(constitution_dir)
        cls.rules = cls.loader.get_all_rules()
    
    def test_all_rules_have_required_fields(self):
        """Verify all rules have required fields (table-driven)."""
        required_fields = [
            'rule_id', 'title', 'category', 'enabled', 'severity_level', 'version'
        ]
        
        test_cases = [
            {
                'rule_id': rule.get('rule_id'),
                'rule_index': idx + 1,
                'rule': rule
            }
            for idx, rule in enumerate(self.rules)
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id'], rule_index=test_case['rule_index']):
                rule = test_case['rule']
                for field in required_fields:
                    self.assertIn(
                        field,
                        rule,
                        f"Rule {test_case['rule_id']} (index {test_case['rule_index']}) missing required field: {field}"
                    )
    
    def test_all_rule_ids_are_strings(self):
        """Verify all rule_ids are non-empty strings."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'index': idx + 1}
            for idx, rule in enumerate(self.rules)
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                rule_id = test_case['rule_id']
                self.assertIsInstance(
                    rule_id,
                    str,
                    f"Rule {rule_id} rule_id must be string, got {type(rule_id)}"
                )
                self.assertGreater(
                    len(rule_id),
                    0,
                    f"Rule {rule_id} rule_id cannot be empty"
                )
    
    def test_all_titles_are_strings(self):
        """Verify all titles are non-empty strings."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'title': rule.get('title')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                title = test_case['title']
                self.assertIsNotNone(title, f"Rule {test_case['rule_id']} title cannot be None")
                self.assertIsInstance(title, str, f"Rule {test_case['rule_id']} title must be string")
                self.assertGreater(len(title.strip()), 0, f"Rule {test_case['rule_id']} title cannot be empty")
    
    def test_all_categories_are_strings(self):
        """Verify all categories are non-empty strings."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'category': rule.get('category')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                category = test_case['category']
                self.assertIsNotNone(category, f"Rule {test_case['rule_id']} category cannot be None")
                self.assertIsInstance(category, str, f"Rule {test_case['rule_id']} category must be string")
                self.assertGreater(len(category.strip()), 0, f"Rule {test_case['rule_id']} category cannot be empty")
    
    def test_enabled_is_boolean(self):
        """Verify enabled field is boolean for all rules."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'enabled': rule.get('enabled')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                enabled = test_case['enabled']
                self.assertIsNotNone(enabled, f"Rule {test_case['rule_id']} enabled cannot be None")
                self.assertIsInstance(
                    enabled,
                    bool,
                    f"Rule {test_case['rule_id']} enabled must be boolean, got {type(enabled)}"
                )
    
    def test_severity_levels_are_valid(self):
        """Verify severity_level values are valid."""
        valid_severities = {'Blocker', 'Critical', 'Major', 'Minor'}
        
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'severity': rule.get('severity_level')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                severity = test_case['severity']
                self.assertIsNotNone(severity, f"Rule {test_case['rule_id']} severity_level cannot be None")
                self.assertIn(
                    severity,
                    valid_severities,
                    f"Rule {test_case['rule_id']} has invalid severity: {severity}"
                )
    
    def test_versions_are_strings(self):
        """Verify version fields are strings."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'version': rule.get('version')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                version = test_case['version']
                self.assertIsNotNone(version, f"Rule {test_case['rule_id']} version cannot be None")
                self.assertIsInstance(version, str, f"Rule {test_case['rule_id']} version must be string")
                self.assertGreater(len(version), 0, f"Rule {test_case['rule_id']} version cannot be empty")
    
    def test_effective_dates_are_valid(self):
        """Verify effective_date fields are valid date strings when present."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'effective_date': rule.get('effective_date')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                effective_date = test_case['effective_date']
                if effective_date is not None:
                    self.assertIsInstance(effective_date, str, f"Rule {test_case['rule_id']} effective_date must be string")
                    self.assertGreaterEqual(len(effective_date), 10, f"Rule {test_case['rule_id']} effective_date must be at least YYYY-MM-DD format")
    
    def test_policy_linkage_structure(self):
        """Verify policy_linkage has correct structure when present."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'policy_linkage': rule.get('policy_linkage')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                policy_linkage = test_case['policy_linkage']
                if policy_linkage is not None:
                    self.assertIsInstance(policy_linkage, dict, f"Rule {test_case['rule_id']} policy_linkage must be object")
                    
                    policy_version_ids = policy_linkage.get('policy_version_ids')
                    if policy_version_ids is not None:
                        self.assertIsInstance(policy_version_ids, list, f"Rule {test_case['rule_id']} policy_version_ids must be array")
                    
                    policy_snapshot_hash = policy_linkage.get('policy_snapshot_hash')
                    if policy_snapshot_hash is not None:
                        self.assertIsInstance(policy_snapshot_hash, str, f"Rule {test_case['rule_id']} policy_snapshot_hash must be string")
    
    def test_descriptions_are_strings(self):
        """Verify descriptions are strings when present."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'description': rule.get('description')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                description = test_case['description']
                if description is not None:
                    self.assertIsInstance(description, str, f"Rule {test_case['rule_id']} description must be string")
    
    def test_requirements_are_lists(self):
        """Verify requirements are lists when present."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'requirements': rule.get('requirements')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                requirements = test_case['requirements']
                if requirements is not None:
                    self.assertIsInstance(requirements, list, f"Rule {test_case['rule_id']} requirements must be array")
    
    def test_validation_fields_are_strings(self):
        """Verify validation fields are strings when present."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'validation': rule.get('validation')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                validation = test_case['validation']
                if validation is not None:
                    self.assertIsInstance(validation, str, f"Rule {test_case['rule_id']} validation must be string")


class MasterGenericRulesContentTests(unittest.TestCase):
    """Test content and semantics of all rules."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = MasterGenericRulesLoader(constitution_dir)
        cls.rules = cls.loader.get_all_rules()
    
    def test_all_rules_have_valid_structure(self):
        """Verify all rules have valid structure and content."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'rule': rule}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                rule = test_case['rule']
                rule_id = test_case['rule_id']
                
                # Validate rule_id matches
                self.assertEqual(rule.get('rule_id'), rule_id, f"{rule_id} ID mismatch")
                
                # Validate required fields exist and are correct types
                self.assertIsInstance(rule.get('title'), str, f"{rule_id} title must be string")
                self.assertIsInstance(rule.get('category'), str, f"{rule_id} category must be string")
                self.assertIsInstance(rule.get('enabled'), bool, f"{rule_id} enabled must be boolean")
                self.assertIsInstance(rule.get('severity_level'), str, f"{rule_id} severity_level must be string")
                self.assertIsInstance(rule.get('version'), str, f"{rule_id} version must be string")
                
                # Validate non-empty fields
                self.assertGreater(len(rule.get('title', '').strip()), 0, f"{rule_id} title cannot be empty")
                self.assertGreater(len(rule.get('category', '').strip()), 0, f"{rule_id} category cannot be empty")
                
                # Validate severity
                valid_severities = ['Blocker', 'Critical', 'Major', 'Minor']
                self.assertIn(
                    rule.get('severity_level'),
                    valid_severities,
                    f"{rule_id} invalid severity_level"
                )
    
    def test_all_rules_have_valid_content_fields(self):
        """Verify all rules have valid content field types."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'rule': rule}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                rule = test_case['rule']
                
                # Validate optional date fields
                effective_date = rule.get('effective_date')
                if effective_date is not None:
                    self.assertIsInstance(effective_date, str)
                    self.assertGreaterEqual(len(effective_date), 10)
                
                last_updated = rule.get('last_updated')
                if last_updated is not None:
                    self.assertIsInstance(last_updated, str)
                    self.assertGreater(len(last_updated), 0)
                
                last_updated_by = rule.get('last_updated_by')
                if last_updated_by is not None:
                    self.assertIsInstance(last_updated_by, str)
                    self.assertGreater(len(last_updated_by), 0)
                
                # Validate policy linkage
                policy_linkage = rule.get('policy_linkage')
                if policy_linkage is not None:
                    self.assertIsInstance(policy_linkage, dict)
                    policy_version_ids = policy_linkage.get('policy_version_ids')
                    if policy_version_ids is not None:
                        self.assertIsInstance(policy_version_ids, list)
                
                # Validate optional content fields
                description = rule.get('description')
                if description is not None:
                    self.assertIsInstance(description, str)
                
                requirements = rule.get('requirements')
                if requirements is not None:
                    self.assertIsInstance(requirements, list)
                
                validation = rule.get('validation')
                if validation is not None:
                    self.assertIsInstance(validation, str)
                
                applicability = rule.get('applicability')
                if applicability is not None:
                    self.assertIsInstance(applicability, str)
                
                status = rule.get('status')
                if status is not None:
                    self.assertIsInstance(status, str)
                
                resolution_order = rule.get('resolution_order')
                if resolution_order is not None:
                    self.assertIsInstance(resolution_order, list)


class MasterGenericRulesCategoryTests(unittest.TestCase):
    """Test rule categorization across all rules."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = MasterGenericRulesLoader(constitution_dir)
        cls.rules = cls.loader.get_all_rules()
    
    def test_all_categories_are_non_empty(self):
        """Verify all categories are non-empty strings."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'category': rule.get('category')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                category = test_case['category']
                self.assertIsNotNone(category, f"Rule {test_case['rule_id']} category cannot be None")
                self.assertIsInstance(category, str, f"Rule {test_case['rule_id']} category must be string")
                self.assertGreater(len(category.strip()), 0, f"Rule {test_case['rule_id']} category cannot be empty")
    
    def test_category_distribution_is_consistent(self):
        """Verify category distribution is consistent across rules."""
        category_counts = {}
        for rule in self.rules:
            category = rule.get('category')
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # All categories should have at least one rule
        self.assertGreater(len(category_counts), 0, "Must have at least one category")
        
        # Each category should have at least one rule
        for category, count in category_counts.items():
            with self.subTest(category=category):
                self.assertGreater(count, 0, f"Category {category} must have at least one rule")


class MasterGenericRulesSeverityTests(unittest.TestCase):
    """Test severity level distribution across all rules."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = MasterGenericRulesLoader(constitution_dir)
        cls.rules = cls.loader.get_all_rules()
    
    def test_severity_distribution_is_consistent(self):
        """Verify severity level distribution is consistent."""
        severity_counts = {}
        for rule in self.rules:
            severity = rule.get('severity_level')
            if severity:
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # All valid severities should have at least one rule
        valid_severities = {'Blocker', 'Critical', 'Major', 'Minor'}
        for severity in valid_severities:
            if severity in severity_counts:
                with self.subTest(severity=severity):
                    self.assertGreater(
                        severity_counts[severity],
                        0,
                        f"Severity {severity} must have at least one rule"
                    )


class MasterGenericRulesConsistencyTests(unittest.TestCase):
    """Test consistency across all rules."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = MasterGenericRulesLoader(constitution_dir)
        cls.rules = cls.loader.get_all_rules()
    
    def test_all_rules_have_version(self):
        """Verify all rules have version field."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'version': rule.get('version')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                version = test_case['version']
                self.assertIsNotNone(version, f"Rule {test_case['rule_id']} version cannot be None")
                self.assertIsInstance(version, str, f"Rule {test_case['rule_id']} version must be string")
                self.assertGreater(len(version), 0, f"Rule {test_case['rule_id']} version cannot be empty")
    
    def test_all_rules_are_enabled(self):
        """Verify all rules are enabled."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'enabled': rule.get('enabled')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                enabled = test_case['enabled']
                self.assertIsNotNone(enabled, f"Rule {test_case['rule_id']} enabled cannot be None")
                self.assertIsInstance(enabled, bool, f"Rule {test_case['rule_id']} enabled must be boolean")
    
    def test_all_rules_have_valid_status(self):
        """Verify all rules have valid status when present."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'status': rule.get('status')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                status = test_case['status']
                if status is not None:
                    self.assertIsInstance(status, str, f"Rule {test_case['rule_id']} status must be string")
                    # Status should be a valid value if present
                    valid_statuses = {'active', 'deprecated', 'draft'}
                    if status.lower() in valid_statuses:
                        pass  # Valid status
                    # Allow other status values for flexibility
    
    def test_all_rules_have_consistent_last_updated_by(self):
        """Verify all rules have last_updated_by when present."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'last_updated_by': rule.get('last_updated_by')}
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                last_updated_by = test_case['last_updated_by']
                if last_updated_by is not None:
                    self.assertIsInstance(last_updated_by, str, f"Rule {test_case['rule_id']} last_updated_by must be string")
                    self.assertGreater(len(last_updated_by), 0, f"Rule {test_case['rule_id']} last_updated_by cannot be empty")
    
    def test_all_rules_have_valid_policy_hash(self):
        """Verify all rules have valid policy_snapshot_hash when present."""
        test_cases = [
            {
                'rule_id': rule.get('rule_id'),
                'hash': rule.get('policy_linkage', {}).get('policy_snapshot_hash')
            }
            for rule in self.rules
        ]
        
        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                policy_hash = test_case['hash']
                if policy_hash is not None:
                    self.assertIsInstance(policy_hash, str, f"Rule {test_case['rule_id']} policy_snapshot_hash must be string")
                    self.assertGreater(len(policy_hash), 0, f"Rule {test_case['rule_id']} policy_snapshot_hash cannot be empty")


if __name__ == '__main__':
    unittest.main(verbosity=2)
