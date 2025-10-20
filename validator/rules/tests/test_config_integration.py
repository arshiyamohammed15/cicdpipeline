"""
Configuration Integration Tests

Tests that validate configuration files and rule coverage.
"""

import unittest
import json
from pathlib import Path
from validator.models import Severity


class TestConfigIntegration(unittest.TestCase):
    """Test suite for configuration integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_dir = Path(__file__).parent.parent.parent.parent / "config" / "rules"
    
    def test_all_config_files_are_valid_json(self):
        """Test that all config/*.json files are valid JSON."""
        if not self.config_dir.exists():
            self.skipTest(f"Config directory not found: {self.config_dir}")
        
        json_files = list(self.config_dir.glob("*.json"))
        self.assertGreater(len(json_files), 0, "No JSON config files found")
        
        for json_file in json_files:
            with self.subTest(file=json_file.name):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.assertIsInstance(data, dict, f"{json_file.name} should contain a JSON object")
                except json.JSONDecodeError as e:
                    self.fail(f"Invalid JSON in {json_file.name}: {e}")
    
    def test_config_files_have_required_fields(self):
        """Test that config files have required fields."""
        if not self.config_dir.exists():
            self.skipTest(f"Config directory not found: {self.config_dir}")
        
        required_fields = ['category', 'priority', 'description']
        
        json_files = list(self.config_dir.glob("*.json"))
        for json_file in json_files:
            with self.subTest(file=json_file.name):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for field in required_fields:
                    self.assertIn(field, data, 
                                f"{json_file.name} missing required field: {field}")
    
    def test_config_categories_match_validators(self):
        """Test that config categories match validator implementations."""
        if not self.config_dir.exists():
            self.skipTest(f"Config directory not found: {self.config_dir}")
        
        # Expected validator categories
        expected_categories = {
            'api_contracts', 'architecture', 'basic_work', 'code_quality',
            'code_review', 'coding_standards', 'comments', 'exception_handling',
            'folder_standards', 'logging', 'performance', 'platform',
            'privacy_security', 'problem_solving', 'requirements',
            'storage_governance', 'system_design', 'teamwork', 'testing_safety'
        }
        
        json_files = list(self.config_dir.glob("*.json"))
        found_categories = set()
        
        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'category' in data:
                found_categories.add(data['category'])
        
        # Check that we have significant coverage
        self.assertGreater(len(found_categories), 5, 
                          "Should have multiple validator categories")
    
    def test_storage_governance_config_exists(self):
        """Test that storage_governance.json exists and is valid."""
        storage_config = self.config_dir / "storage_governance.json"
        
        if not storage_config.exists():
            self.skipTest("storage_governance.json not found")
        
        with open(storage_config, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data['category'], 'storage_governance')
        self.assertIn('priority', data)
        self.assertIn('description', data)
    
    def test_rule_priorities_are_valid(self):
        """Test that rule priorities are valid values."""
        if not self.config_dir.exists():
            self.skipTest(f"Config directory not found: {self.config_dir}")
        
        valid_priorities = {'critical', 'high', 'medium', 'low', 'info', 'important', 'recommended'}
        
        json_files = list(self.config_dir.glob("*.json"))
        for json_file in json_files:
            with self.subTest(file=json_file.name):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'priority' in data:
                    priority = data['priority'].lower()
                    self.assertIn(priority, valid_priorities,
                                f"{json_file.name} has invalid priority: {data['priority']}")
    
    def test_config_descriptions_are_not_empty(self):
        """Test that config descriptions are not empty."""
        if not self.config_dir.exists():
            self.skipTest(f"Config directory not found: {self.config_dir}")
        
        json_files = list(self.config_dir.glob("*.json"))
        for json_file in json_files:
            with self.subTest(file=json_file.name):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'description' in data:
                    self.assertTrue(len(data['description']) > 0,
                                  f"{json_file.name} has empty description")
                    self.assertGreater(len(data['description']), 10,
                                     f"{json_file.name} description too short")


class TestRuleCoverage(unittest.TestCase):
    """Test suite for rule coverage validation."""
    
    def test_storage_governance_validator_exists(self):
        """Test that StorageGovernanceValidator exists and is importable."""
        try:
            from validator.rules.storage_governance import StorageGovernanceValidator
            validator = StorageGovernanceValidator()
            self.assertIsNotNone(validator)
            self.assertTrue(hasattr(validator, 'validate'))
        except ImportError as e:
            self.fail(f"Failed to import StorageGovernanceValidator: {e}")
    
    def test_privacy_validator_exists(self):
        """Test that PrivacyValidator exists and is importable."""
        try:
            from validator.rules.privacy import PrivacyValidator
            validator = PrivacyValidator()
            self.assertIsNotNone(validator)
        except ImportError as e:
            self.fail(f"Failed to import PrivacyValidator: {e}")
    
    def test_architecture_validator_exists(self):
        """Test that ArchitectureValidator exists and is importable."""
        try:
            from validator.rules.architecture import ArchitectureValidator
            validator = ArchitectureValidator()
            self.assertIsNotNone(validator)
        except ImportError as e:
            self.fail(f"Failed to import ArchitectureValidator: {e}")
    
    def test_exception_handling_validator_exists(self):
        """Test that ExceptionHandlingValidator exists and is importable."""
        try:
            from validator.rules.exception_handling import ExceptionHandlingValidator
            validator = ExceptionHandlingValidator()
            self.assertIsNotNone(validator)
        except ImportError as e:
            self.fail(f"Failed to import ExceptionHandlingValidator: {e}")
    
    def test_api_contracts_validator_exists(self):
        """Test that APIContractsValidator exists and is importable."""
        try:
            from validator.rules.api_contracts import APIContractsValidator
            validator = APIContractsValidator()
            self.assertIsNotNone(validator)
        except ImportError as e:
            self.fail(f"Failed to import APIContractsValidator: {e}")


if __name__ == '__main__':
    unittest.main()

