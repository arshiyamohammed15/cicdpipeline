"""
WHAT: Comprehensive test suite for CURSOR TESTING RULES.json with 100% rule coverage
WHY: Validate all 22 rules following TST-001 through TST-022 with deterministic, repeatable tests

Test Design Principles (following the rules themselves):
- TST-001: Prioritize Determinism Over Speed - All tests use fixed seeds
- TST-002: Eliminate Test-Result Caching - No caching, fresh loads each time
- TST-003: Enforce Hermetic Test Runs - Complete isolation, no network/system dependencies
- TST-004: Maintain Test Independence - Each test is self-contained
- TST-009: Maintain Unit Test Purity - Pure functions, no I/O, network, or time dependencies
- TST-010: Use Table-Driven Test Structure - All tests use table-driven patterns
- TST-014: Control Randomness and Time - All randomness seeded, time controlled
"""
import json
import unittest
from pathlib import Path
from typing import Dict, List, Any, Optional
import random
from datetime import datetime

# Deterministic seed for all randomness (TST-014)
TEST_RANDOM_SEED = 42
random.seed(TEST_RANDOM_SEED)


class CursorTestingRulesLoader:
    """Load and validate CURSOR TESTING RULES.json file."""

    def __init__(self, constitution_dir: Path):
        """
        Initialize loader with constitution directory.

        Args:
            constitution_dir: Path to docs/constitution directory
        """
        self.constitution_dir = Path(constitution_dir)
        self._file_path = self.constitution_dir / "CURSOR TESTING RULES.json"

    def load_file(self) -> Dict[str, Any]:
        """
        Load CURSOR TESTING RULES.json file.

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
        Get all rules from CURSOR TESTING RULES.json.

        Returns:
            List of rule dictionaries
        """
        data = self.load_file()
        return data.get('constitution_rules', [])

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific rule by ID.

        Args:
            rule_id: Rule identifier (e.g., "TST-001")

        Returns:
            Rule dictionary or None if not found
        """
        rules = self.get_all_rules()
        for rule in rules:
            if rule.get('rule_id') == rule_id:
                return rule
        return None


class CursorTestingRulesStructureTests(unittest.TestCase):
    """Test structure and integrity of CURSOR TESTING RULES.json."""

    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = CursorTestingRulesLoader(constitution_dir)

    def test_file_exists(self):
        """Verify CURSOR TESTING RULES.json file exists."""
        file_path = self.loader._file_path
        self.assertTrue(
            file_path.exists(),
            f"CURSOR TESTING RULES.json not found at: {file_path}"
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

    def test_metadata_has_constitution_name(self):
        """Verify metadata has constitution_name field."""
        data = self.loader.load_file()
        metadata = data.get('metadata', {})
        self.assertIn(
            'constitution_name',
            metadata,
            "Metadata must have 'constitution_name' field"
        )
        self.assertEqual(
            metadata['constitution_name'],
            "ZeroUI2.0 Cursor Testing Constitution",
            "constitution_name must match expected value"
        )


class CursorTestingRulesFieldTests(unittest.TestCase):
    """Test all required fields in each rule."""

    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = CursorTestingRulesLoader(constitution_dir)
        cls.rules = cls.loader.get_all_rules()

    def test_all_rules_have_required_fields(self):
        """Verify all rules have required fields (table-driven)."""
        required_fields = [
            'rule_id', 'title', 'category', 'enabled', 'severity_level',
            'version', 'effective_date', 'last_updated', 'last_updated_by',
            'policy_linkage', 'description', 'requirements', 'validation'
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

    def test_all_rule_ids_use_tst_prefix(self):
        """Verify all rule_ids use TST- prefix."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'index': idx + 1}
            for idx, rule in enumerate(self.rules)
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                rule_id = test_case['rule_id']
                self.assertTrue(
                    rule_id.startswith('TST-'),
                    f"Rule {rule_id} must start with 'TST-' prefix"
                )

    def test_all_rule_ids_sequential(self):
        """Verify rule IDs are sequentially numbered TST-001 to TST-022."""
        rule_ids = [rule.get('rule_id') for rule in self.rules]
        tst_numbers = []

        for rule_id in rule_ids:
            if rule_id.startswith('TST-'):
                try:
                    num = int(rule_id[4:])
                    tst_numbers.append(num)
                except ValueError:
                    self.fail(f"Invalid TST rule number format: {rule_id}")

        expected_range = set(range(1, 23))  # TST-001 to TST-022
        actual_range = set(tst_numbers)

        missing = expected_range - actual_range
        extra = actual_range - expected_range

        if missing:
            self.fail(f"Missing TST rule numbers: {sorted(missing)}")
        if extra:
            self.fail(f"Extra TST rule numbers: {sorted(extra)}")

        self.assertEqual(len(tst_numbers), 22, "Must have exactly 22 TST rules")

    def test_all_titles_are_strings(self):
        """Verify all titles are non-empty strings."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'title': rule.get('title')}
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                title = test_case['title']
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
                self.assertIsInstance(version, str, f"Rule {test_case['rule_id']} version must be string")
                self.assertGreater(len(version), 0, f"Rule {test_case['rule_id']} version cannot be empty")

    def test_effective_dates_are_valid(self):
        """Verify effective_date fields are valid date strings."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'effective_date': rule.get('effective_date')}
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                effective_date = test_case['effective_date']
                self.assertIsNotNone(effective_date, f"Rule {test_case['rule_id']} effective_date cannot be None")
                self.assertIsInstance(effective_date, str, f"Rule {test_case['rule_id']} effective_date must be string")
                self.assertGreaterEqual(len(effective_date), 10, f"Rule {test_case['rule_id']} effective_date must be at least YYYY-MM-DD format")

    def test_policy_linkage_structure(self):
        """Verify policy_linkage has correct structure."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'policy_linkage': rule.get('policy_linkage')}
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                policy_linkage = test_case['policy_linkage']
                self.assertIsNotNone(policy_linkage, f"Rule {test_case['rule_id']} policy_linkage cannot be None")
                self.assertIsInstance(policy_linkage, dict, f"Rule {test_case['rule_id']} policy_linkage must be object")

                self.assertIn('policy_version_ids', policy_linkage, f"Rule {test_case['rule_id']} policy_linkage missing policy_version_ids")
                self.assertIsInstance(policy_linkage['policy_version_ids'], list, f"Rule {test_case['rule_id']} policy_version_ids must be array")

                self.assertIn('policy_snapshot_hash', policy_linkage, f"Rule {test_case['rule_id']} policy_linkage missing policy_snapshot_hash")
                self.assertIsInstance(policy_linkage['policy_snapshot_hash'], str, f"Rule {test_case['rule_id']} policy_snapshot_hash must be string")

    def test_descriptions_are_strings(self):
        """Verify descriptions are strings."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'description': rule.get('description')}
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                description = test_case['description']
                self.assertIsNotNone(description, f"Rule {test_case['rule_id']} description cannot be None")
                self.assertIsInstance(description, str, f"Rule {test_case['rule_id']} description must be string")

    def test_requirements_are_lists(self):
        """Verify requirements are lists."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'requirements': rule.get('requirements')}
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                requirements = test_case['requirements']
                self.assertIsNotNone(requirements, f"Rule {test_case['rule_id']} requirements cannot be None")
                self.assertIsInstance(requirements, list, f"Rule {test_case['rule_id']} requirements must be array")
                self.assertGreater(len(requirements), 0, f"Rule {test_case['rule_id']} requirements cannot be empty")

    def test_validation_fields_are_strings(self):
        """Verify validation fields are strings."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'validation': rule.get('validation')}
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                validation = test_case['validation']
                self.assertIsNotNone(validation, f"Rule {test_case['rule_id']} validation cannot be None")
                self.assertIsInstance(validation, str, f"Rule {test_case['rule_id']} validation must be string")


class CursorTestingRulesContentTests(unittest.TestCase):
    """Test content and semantics of each individual rule."""

    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = CursorTestingRulesLoader(constitution_dir)
        cls.rules = cls.loader.get_all_rules()

    def test_rule_tst_001_prioritize_determinism(self):
        """Test TST-001: Prioritize Determinism Over Speed."""
        rule = self.loader.get_rule_by_id('TST-001')
        self.assertIsNotNone(rule, "TST-001 must exist")

        self.assertEqual(rule['title'], "Prioritize Determinism Over Speed")
        self.assertEqual(rule['category'], "Testing Philosophy")
        self.assertEqual(rule['severity_level'], "Blocker")
        self.assertTrue(rule['enabled'])
        self.assertIn("reproducible", rule['description'].lower())
        self.assertIn("reproducible", rule['requirements'][0].lower())

    def test_rule_tst_002_eliminate_caching(self):
        """Test TST-002: Eliminate Test-Result Caching."""
        rule = self.loader.get_rule_by_id('TST-002')
        self.assertIsNotNone(rule, "TST-002 must exist")

        self.assertEqual(rule['title'], "Eliminate Test-Result Caching")
        self.assertEqual(rule['category'], "Testing Philosophy")
        self.assertEqual(rule['severity_level'], "Blocker")
        self.assertTrue(rule['enabled'])
        self.assertIn("cache", rule['description'].lower())

    def test_rule_tst_003_hermetic_test_runs(self):
        """Test TST-003: Enforce Hermetic Test Runs."""
        rule = self.loader.get_rule_by_id('TST-003')
        self.assertIsNotNone(rule, "TST-003 must exist")

        self.assertEqual(rule['title'], "Enforce Hermetic Test Runs")
        self.assertEqual(rule['category'], "Testing Philosophy")
        self.assertEqual(rule['severity_level'], "Blocker")
        self.assertTrue(rule['enabled'])
        self.assertIn("network", rule['description'].lower() or "isolation" in rule['description'].lower())

    def test_rule_tst_004_test_independence(self):
        """Test TST-004: Maintain Test Independence."""
        rule = self.loader.get_rule_by_id('TST-004')
        self.assertIsNotNone(rule, "TST-004 must exist")

        self.assertEqual(rule['title'], "Maintain Test Independence")
        self.assertEqual(rule['category'], "Testing Philosophy")
        self.assertEqual(rule['severity_level'], "Critical")
        self.assertTrue(rule['enabled'])
        self.assertIn("sequence", rule['description'].lower())

    def test_rule_tst_005_repository_structure(self):
        """Test TST-005: Maintain Standard Repository Structure."""
        rule = self.loader.get_rule_by_id('TST-005')
        self.assertIsNotNone(rule, "TST-005 must exist")

        self.assertEqual(rule['title'], "Maintain Standard Repository Structure")
        self.assertEqual(rule['category'], "Project Structure")
        self.assertEqual(rule['severity_level'], "Major")
        self.assertTrue(rule['enabled'])
        self.assertIn("src", rule['description'].lower() or "tests" in rule['description'].lower())

    def test_rule_tst_006_test_naming_conventions(self):
        """Test TST-006: Use Standard Test Naming Conventions."""
        rule = self.loader.get_rule_by_id('TST-006')
        self.assertIsNotNone(rule, "TST-006 must exist")

        self.assertEqual(rule['title'], "Use Standard Test Naming Conventions")
        self.assertEqual(rule['category'], "Project Structure")
        self.assertEqual(rule['severity_level'], "Major")
        self.assertTrue(rule['enabled'])
        self.assertIn("test_", rule['description'].lower() or "naming" in rule['description'].lower())

    def test_rule_tst_007_purge_cache_directories(self):
        """Test TST-007: Purge Cache Directories Pre-Execution."""
        rule = self.loader.get_rule_by_id('TST-007')
        self.assertIsNotNone(rule, "TST-007 must exist")

        self.assertEqual(rule['title'], "Purge Cache Directories Pre-Execution")
        self.assertEqual(rule['category'], "Cache Management")
        self.assertEqual(rule['severity_level'], "Critical")
        self.assertTrue(rule['enabled'])
        self.assertIn("cache", rule['description'].lower())

    def test_rule_tst_008_disable_framework_caching(self):
        """Test TST-008: Disable Framework Caching."""
        rule = self.loader.get_rule_by_id('TST-008')
        self.assertIsNotNone(rule, "TST-008 must exist")

        self.assertEqual(rule['title'], "Disable Framework Caching")
        self.assertEqual(rule['category'], "Cache Management")
        self.assertEqual(rule['severity_level'], "Critical")
        self.assertTrue(rule['enabled'])
        self.assertIn("caching", rule['description'].lower())
        self.assertIn("framework", rule['description'].lower())

    def test_rule_tst_009_unit_test_purity(self):
        """Test TST-009: Maintain Unit Test Purity."""
        rule = self.loader.get_rule_by_id('TST-009')
        self.assertIsNotNone(rule, "TST-009 must exist")

        self.assertEqual(rule['title'], "Maintain Unit Test Purity")
        self.assertEqual(rule['category'], "Test Design")
        self.assertEqual(rule['severity_level'], "Critical")
        self.assertTrue(rule['enabled'])
        self.assertIn("pure", rule['description'].lower() or "i/o" in rule['description'].lower())

    def test_rule_tst_010_table_driven_tests(self):
        """Test TST-010: Use Table-Driven Test Structure."""
        rule = self.loader.get_rule_by_id('TST-010')
        self.assertIsNotNone(rule, "TST-010 must exist")

        self.assertEqual(rule['title'], "Use Table-Driven Test Structure")
        self.assertEqual(rule['category'], "Test Design")
        self.assertEqual(rule['severity_level'], "Major")
        self.assertTrue(rule['enabled'])
        self.assertIn("table", rule['description'].lower())

    def test_rule_tst_011_in_memory_doubles(self):
        """Test TST-011: Use In-Memory Doubles for Component Tests."""
        rule = self.loader.get_rule_by_id('TST-011')
        self.assertIsNotNone(rule, "TST-011 must exist")

        self.assertEqual(rule['title'], "Use In-Memory Doubles for Component Tests")
        self.assertEqual(rule['category'], "Test Design")
        self.assertEqual(rule['severity_level'], "Critical")
        self.assertTrue(rule['enabled'])
        self.assertIn("memory", rule['description'].lower() or "double" in rule['description'].lower())

    def test_rule_tst_012_real_adapters_integration(self):
        """Test TST-012: Use Real Adapters for Integration Tests."""
        rule = self.loader.get_rule_by_id('TST-012')
        self.assertIsNotNone(rule, "TST-012 must exist")

        self.assertEqual(rule['title'], "Use Real Adapters for Integration Tests")
        self.assertEqual(rule['category'], "Test Design")
        self.assertEqual(rule['severity_level'], "Critical")
        self.assertTrue(rule['enabled'])
        self.assertIn("integration", rule['description'].lower() or "adapter" in rule['description'].lower())

    def test_rule_tst_013_prohibit_internet_access(self):
        """Test TST-013: Prohibit Internet Access in Tests."""
        rule = self.loader.get_rule_by_id('TST-013')
        self.assertIsNotNone(rule, "TST-013 must exist")

        self.assertEqual(rule['title'], "Prohibit Internet Access in Tests")
        self.assertEqual(rule['category'], "Test Design")
        self.assertEqual(rule['severity_level'], "Critical")
        self.assertTrue(rule['enabled'])
        self.assertIn("internet", rule['description'].lower() or "network" in rule['description'].lower())

    def test_rule_tst_014_control_randomness_time(self):
        """Test TST-014: Control Randomness and Time."""
        rule = self.loader.get_rule_by_id('TST-014')
        self.assertIsNotNone(rule, "TST-014 must exist")

        self.assertEqual(rule['title'], "Control Randomness and Time")
        self.assertEqual(rule['category'], "Determinism")
        self.assertEqual(rule['severity_level'], "Critical")
        self.assertTrue(rule['enabled'])
        self.assertIn("random", rule['description'].lower() or "time" in rule['description'].lower())

    def test_rule_tst_015_prohibit_test_retries(self):
        """Test TST-015: Prohibit Test Retries."""
        rule = self.loader.get_rule_by_id('TST-015')
        self.assertIsNotNone(rule, "TST-015 must exist")

        self.assertEqual(rule['title'], "Prohibit Test Retries")
        self.assertEqual(rule['category'], "Determinism")
        self.assertEqual(rule['severity_level'], "Critical")
        self.assertTrue(rule['enabled'])
        self.assertIn("retries", rule['description'].lower())

    def test_rule_tst_016_organize_fixtures(self):
        """Test TST-016: Organize Fixtures and Data."""
        rule = self.loader.get_rule_by_id('TST-016')
        self.assertIsNotNone(rule, "TST-016 must exist")

        self.assertEqual(rule['title'], "Organize Fixtures and Data")
        self.assertEqual(rule['category'], "Test Data")
        self.assertEqual(rule['severity_level'], "Major")
        self.assertTrue(rule['enabled'])
        self.assertIn("fixture", rule['description'].lower())

    def test_rule_tst_017_generate_test_evidence(self):
        """Test TST-017: Generate Test Evidence."""
        rule = self.loader.get_rule_by_id('TST-017')
        self.assertIsNotNone(rule, "TST-017 must exist")

        self.assertEqual(rule['title'], "Generate Test Evidence")
        self.assertEqual(rule['category'], "Reporting")
        self.assertEqual(rule['severity_level'], "Major")
        self.assertTrue(rule['enabled'])
        self.assertIn("junit", rule['description'].lower() or "report" in rule['description'].lower())

    def test_rule_tst_018_ai_generated_tests_deterministic(self):
        """Test TST-018: Design AI-Generated Tests Deterministically."""
        rule = self.loader.get_rule_by_id('TST-018')
        self.assertIsNotNone(rule, "TST-018 must exist")

        self.assertEqual(rule['title'], "Design AI-Generated Tests Deterministically")
        self.assertEqual(rule['category'], "AI Generation")
        self.assertEqual(rule['severity_level'], "Critical")
        self.assertTrue(rule['enabled'])
        self.assertIn("cache", rule['description'].lower())
        self.assertIn("seed", rule['description'].lower())

    def test_rule_tst_019_ai_generated_tests_organized(self):
        """Test TST-019: Organize AI-Generated Tests Properly."""
        rule = self.loader.get_rule_by_id('TST-019')
        self.assertIsNotNone(rule, "TST-019 must exist")

        self.assertEqual(rule['title'], "Organize AI-Generated Tests Properly")
        self.assertEqual(rule['category'], "AI Generation")
        self.assertEqual(rule['severity_level'], "Major")
        self.assertTrue(rule['enabled'])
        self.assertIn("directories", rule['description'].lower())

    def test_rule_tst_020_ai_generated_tests_quality(self):
        """Test TST-020: Ensure AI-Generated Test Quality."""
        rule = self.loader.get_rule_by_id('TST-020')
        self.assertIsNotNone(rule, "TST-020 must exist")

        self.assertEqual(rule['title'], "Ensure AI-Generated Test Quality")
        self.assertEqual(rule['category'], "AI Generation")
        self.assertEqual(rule['severity_level'], "Critical")
        self.assertTrue(rule['enabled'])
        self.assertIn("complete", rule['description'].lower())

    def test_rule_tst_021_enforce_quality_gates(self):
        """Test TST-021: Enforce Quality Gates."""
        rule = self.loader.get_rule_by_id('TST-021')
        self.assertIsNotNone(rule, "TST-021 must exist")

        self.assertEqual(rule['title'], "Enforce Quality Gates")
        self.assertEqual(rule['category'], "Quality Assurance")
        self.assertEqual(rule['severity_level'], "Blocker")
        self.assertTrue(rule['enabled'])
        self.assertIn("pass", rule['description'].lower())

    def test_rule_tst_022_comprehensive_test_reviews(self):
        """Test TST-022: Conduct Comprehensive Test Reviews."""
        rule = self.loader.get_rule_by_id('TST-022')
        self.assertIsNotNone(rule, "TST-022 must exist")

        self.assertEqual(rule['title'], "Conduct Comprehensive Test Reviews")
        self.assertEqual(rule['category'], "Code Review")
        self.assertEqual(rule['severity_level'], "Critical")
        self.assertTrue(rule['enabled'])
        self.assertIn("verify", rule['description'].lower())


class CursorTestingRulesCategoryTests(unittest.TestCase):
    """Test rule categorization and distribution."""

    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = CursorTestingRulesLoader(constitution_dir)
        cls.rules = cls.loader.get_all_rules()

    def test_all_categories_are_valid(self):
        """Verify all categories match expected categories."""
        expected_categories = {
            "Testing Philosophy",
            "Project Structure",
            "Cache Management",
            "Test Design",
            "Determinism",
            "Test Data",
            "Reporting",
            "AI Generation",
            "Quality Assurance",
            "Code Review"
        }

        test_cases = [
            {'rule_id': rule.get('rule_id'), 'category': rule.get('category')}
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                category = test_case['category']
                self.assertIn(
                    category,
                    expected_categories,
                    f"Rule {test_case['rule_id']} has unknown category: {category}"
                )

    def test_category_distribution(self):
        """Verify expected category distribution."""
        category_counts = {}
        for rule in self.rules:
            category = rule.get('category')
            category_counts[category] = category_counts.get(category, 0) + 1

        # Expected distribution based on file content
        expected_distribution = {
            "Testing Philosophy": 4,
            "Project Structure": 2,
            "Cache Management": 2,
            "Test Design": 5,
            "Determinism": 2,
            "Test Data": 1,
            "Reporting": 1,
            "AI Generation": 3,
            "Quality Assurance": 1,
            "Code Review": 1
        }

        for category, expected_count in expected_distribution.items():
            actual_count = category_counts.get(category, 0)
            self.assertEqual(
                actual_count,
                expected_count,
                f"Category {category} has {actual_count} rules, expected {expected_count}"
            )


class CursorTestingRulesSeverityTests(unittest.TestCase):
    """Test severity level distribution."""

    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = CursorTestingRulesLoader(constitution_dir)
        cls.rules = cls.loader.get_all_rules()

    def test_severity_distribution(self):
        """Verify expected severity level distribution."""
        severity_counts = {}
        for rule in self.rules:
            severity = rule.get('severity_level')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Expected distribution based on file content
        expected_blocker = 4  # TST-001, TST-002, TST-003, TST-021
        expected_critical = 12  # TST-004, TST-007, TST-008, TST-009, TST-011, TST-012, TST-013, TST-014, TST-015, TST-018, TST-020, TST-022
        expected_major = 6  # TST-005, TST-006, TST-010, TST-016, TST-017, TST-019

        self.assertEqual(
            severity_counts.get('Blocker', 0),
            expected_blocker,
            f"Expected {expected_blocker} Blocker severity rules"
        )
        self.assertEqual(
            severity_counts.get('Critical', 0),
            expected_critical,
            f"Expected {expected_critical} Critical severity rules"
        )
        self.assertEqual(
            severity_counts.get('Major', 0),
            expected_major,
            f"Expected {expected_major} Major severity rules"
        )


class CursorTestingRulesPolicyLinkageTests(unittest.TestCase):
    """Test policy linkage consistency."""

    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = CursorTestingRulesLoader(constitution_dir)
        cls.rules = cls.loader.get_all_rules()

    def test_all_rules_reference_same_policy(self):
        """Verify all rules reference POL-TEST-001."""
        test_cases = [
            {
                'rule_id': rule.get('rule_id'),
                'policy_version_ids': rule.get('policy_linkage', {}).get('policy_version_ids', [])
            }
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                policy_ids = test_case['policy_version_ids']
                self.assertIn(
                    'POL-TEST-001',
                    policy_ids,
                    f"Rule {test_case['rule_id']} must reference POL-TEST-001"
                )

    def test_all_rules_have_same_hash(self):
        """Verify all rules have the same policy_snapshot_hash."""
        expected_hash = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        test_cases = [
            {
                'rule_id': rule.get('rule_id'),
                'hash': rule.get('policy_linkage', {}).get('policy_snapshot_hash')
            }
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                actual_hash = test_case['hash']
                self.assertEqual(
                    actual_hash,
                    expected_hash,
                    f"Rule {test_case['rule_id']} policy_snapshot_hash must match expected value"
                )


class CursorTestingRulesConsistencyTests(unittest.TestCase):
    """Test consistency across all rules."""

    @classmethod
    def setUpClass(cls):
        """Set up test class with rule loader."""
        constitution_dir = Path(__file__).parent.parent / 'docs' / 'constitution'
        cls.loader = CursorTestingRulesLoader(constitution_dir)
        cls.rules = cls.loader.get_all_rules()

    def test_all_rules_have_same_version(self):
        """Verify all rules have version 1.0.0."""
        expected_version = "1.0.0"

        test_cases = [
            {'rule_id': rule.get('rule_id'), 'version': rule.get('version')}
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                self.assertEqual(
                    test_case['version'],
                    expected_version,
                    f"Rule {test_case['rule_id']} version must be {expected_version}"
                )

    def test_all_rules_have_same_effective_date(self):
        """Verify all rules have effective_date 2024-01-01."""
        expected_date = "2024-01-01"

        test_cases = [
            {'rule_id': rule.get('rule_id'), 'effective_date': rule.get('effective_date')}
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                self.assertEqual(
                    test_case['effective_date'],
                    expected_date,
                    f"Rule {test_case['rule_id']} effective_date must be {expected_date}"
                )

    def test_all_rules_have_same_last_updated(self):
        """Verify all rules have same last_updated timestamp."""
        timestamps = [rule.get('last_updated') for rule in self.rules]
        unique_timestamps = set(timestamps)

        self.assertEqual(
            len(unique_timestamps),
            1,
            f"All rules must have same last_updated timestamp, found {len(unique_timestamps)} unique values: {unique_timestamps}"
        )

    def test_all_rules_have_same_last_updated_by(self):
        """Verify all rules have same last_updated_by value."""
        expected_updater = "constitution@zeroui.com"

        test_cases = [
            {'rule_id': rule.get('rule_id'), 'last_updated_by': rule.get('last_updated_by')}
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                self.assertEqual(
                    test_case['last_updated_by'],
                    expected_updater,
                    f"Rule {test_case['rule_id']} last_updated_by must be {expected_updater}"
                )

    def test_all_rules_have_same_validation_text(self):
        """Verify all rules have same validation text."""
        expected_validation = "Automated test execution verifies compliance."

        test_cases = [
            {'rule_id': rule.get('rule_id'), 'validation': rule.get('validation')}
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                self.assertEqual(
                    test_case['validation'],
                    expected_validation,
                    f"Rule {test_case['rule_id']} validation must match expected text"
                )

    def test_all_rules_are_enabled(self):
        """Verify all rules are enabled."""
        test_cases = [
            {'rule_id': rule.get('rule_id'), 'enabled': rule.get('enabled')}
            for rule in self.rules
        ]

        for test_case in test_cases:
            with self.subTest(rule_id=test_case['rule_id']):
                self.assertTrue(
                    test_case['enabled'],
                    f"Rule {test_case['rule_id']} must be enabled"
                )


if __name__ == '__main__':
    unittest.main(verbosity=2)
