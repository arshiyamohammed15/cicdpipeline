"""
Dynamic Test Factory for ZeroUI 2.0 Constitution Rules

This module provides a factory class that dynamically generates test cases
from rules.json, eliminating hardcoded rule IDs and making tests maintainable.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass


@dataclass
class TestCase:
    """Represents a dynamically generated test case."""
    rule_id: str
    rule_name: str
    category: str
    severity: str
    validator: str
    constitution: str
    test_method_name: str
    test_data: Dict[str, Any]
    expected_behavior: str
    error_code: str


class DynamicTestFactory:
    """
    Factory class for generating dynamic test cases from rules.json.

    This class loads all 89 Constitution rules and provides methods to:
    - Filter rules by various criteria
    - Generate test cases with appropriate test data
    - Create test method names dynamically
    - Provide pattern-based rule discovery
    """

    def __init__(self, rules_file: str = "tools/validator/rules.json"):
        """Initialize the factory with rules from JSON file."""
        self.rules_file = Path(rules_file)
        self.rules = self._load_rules()
        self._validate_rules()

    def _load_rules(self) -> List[Dict[str, Any]]:
        """Load all rules from the JSON file."""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('rules', [])
        except FileNotFoundError:
            raise FileNotFoundError(f"Rules file not found: {self.rules_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in rules file: {e}")

    def _validate_rules(self) -> None:
        """Validate that all required fields are present in rules."""
        required_fields = ['id', 'name', 'description', 'category', 'severity',
                          'error_code', 'validator', 'constitution']

        for rule in self.rules:
            for field in required_fields:
                if field not in rule:
                    raise ValueError(f"Rule {rule.get('id', 'unknown')} missing required field: {field}")

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Get all 89 rules."""
        return self.rules.copy()

    def get_rules_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Filter rules by category (security, api, documentation, etc.)."""
        return [rule for rule in self.rules if rule.get('category') == category]

    def get_rules_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Filter rules by severity (error, warning)."""
        return [rule for rule in self.rules if rule.get('severity') == severity]

    def get_rules_by_validator(self, validator: str) -> List[Dict[str, Any]]:
        """Filter rules by validator class."""
        return [rule for rule in self.rules if validator in rule.get('validator', '')]

    def get_rules_by_constitution(self, constitution: str) -> List[Dict[str, Any]]:
        """Filter rules by Constitution file."""
        return [rule for rule in self.rules if rule.get('constitution') == constitution]

    def get_rules_by_pattern(self, pattern: str, field: str = 'name') -> List[Dict[str, Any]]:
        """Filter rules by pattern in specified field."""
        regex = re.compile(pattern, re.IGNORECASE)
        return [rule for rule in self.rules if regex.search(rule.get(field, ''))]

    def get_rules_by_keywords(self, keywords: List[str], fields: List[str] = None) -> List[Dict[str, Any]]:
        """Filter rules by keywords in specified fields."""
        if fields is None:
            fields = ['name', 'description']

        matching_rules = []
        for rule in self.rules:
            for keyword in keywords:
                for field in fields:
                    if keyword.lower() in rule.get(field, '').lower():
                        matching_rules.append(rule)
                        break
                else:
                    continue
                break

        return matching_rules

    def create_test_cases(self, filter_func: Optional[Callable] = None) -> List[TestCase]:
        """
        Generate test cases with optional filtering.

        Args:
            filter_func: Optional function to filter rules before creating test cases

        Returns:
            List of TestCase objects
        """
        rules = self.rules
        if filter_func:
            rules = [rule for rule in rules if filter_func(rule)]

        test_cases = []
        for rule in rules:
            test_case = self._create_test_case(rule)
            test_cases.append(test_case)

        return test_cases

    def _create_test_case(self, rule: Dict[str, Any]) -> TestCase:
        """Create a TestCase object from a rule."""
        return TestCase(
            rule_id=rule['id'],
            rule_name=rule['name'],
            category=rule.get('category', 'unknown'),
            severity=rule.get('severity', 'unknown'),
            validator=rule.get('validator', ''),
            constitution=rule.get('constitution', ''),
            test_method_name=self._generate_test_method_name(rule),
            test_data=self._generate_test_data(rule),
            expected_behavior=rule.get('description', ''),
            error_code=rule.get('error_code', '')
        )

    def _generate_test_method_name(self, rule: Dict[str, Any]) -> str:
        """Generate a test method name from rule information."""
        rule_id = rule['id'].lower()
        rule_name = rule['name'].lower()

        # Clean up the name for method naming
        clean_name = re.sub(r'[^a-z0-9\s]', '', rule_name)
        clean_name = re.sub(r'\s+', '_', clean_name)

        return f"test_{rule_id}_{clean_name}"

    def _generate_test_data(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Generate appropriate test data based on rule characteristics."""
        category = rule.get('category', 'unknown')
        rule_id = rule['id']

        # Base test data structure
        test_data = {
            'rule_id': rule_id,
            'category': category,
            'severity': rule.get('severity', 'unknown'),
            'validator': rule.get('validator', ''),
            'constitution': rule.get('constitution', ''),
            'error_code': rule.get('error_code', ''),
            'violation_examples': [],
            'valid_examples': [],
            'test_files': []
        }

        # Generate category-specific test data
        if category == 'security':
            test_data.update(self._generate_security_test_data(rule))
        elif category == 'api':
            test_data.update(self._generate_api_test_data(rule))
        elif category == 'documentation':
            test_data.update(self._generate_documentation_test_data(rule))
        elif category == 'logging':
            test_data.update(self._generate_logging_test_data(rule))
        elif category == 'structure':
            test_data.update(self._generate_structure_test_data(rule))
        elif category == 'code_quality':
            test_data.update(self._generate_code_quality_test_data(rule))
        else:
            test_data.update(self._generate_generic_test_data(rule))

        return test_data

    def _generate_security_test_data(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test data for security rules."""
        rule_id = rule['id']

        if rule_id == 'R009':
            return {
                'violation_examples': [
                    'password = "secret123"',
                    'api_key = "sk-1234567890abcdef"',
                    'token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"'
                ],
                'valid_examples': [
                    'password = os.getenv("DB_PASSWORD")',
                    'api_key = keyring.get_password("service", "api_key")',
                    'token = get_auth_token()'
                ]
            }
        elif rule_id == 'R039':
            return {
                'violation_examples': [
                    'SECRET_KEY = "django-insecure-abc123"',
                    'DATABASE_URL = "postgresql://user:pass@localhost/db"'
                ],
                'valid_examples': [
                    'SECRET_KEY = os.getenv("SECRET_KEY")',
                    'DATABASE_URL = os.getenv("DATABASE_URL")'
                ]
            }

        return {'violation_examples': [], 'valid_examples': []}

    def _generate_api_test_data(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test data for API rules."""
        rule_id = rule['id']

        if rule_id == 'R013':
            return {
                'violation_examples': [
                    'POST /api/getUserData',
                    'GET /api/createUser',
                    'PUT /api/deleteUser'
                ],
                'valid_examples': [
                    'GET /api/users/{id}',
                    'POST /api/users',
                    'PUT /api/users/{id}',
                    'DELETE /api/users/{id}'
                ]
            }
        elif rule_id == 'R014':
            return {
                'violation_examples': [
                    '/api/get_user_data',
                    '/api/createUser',
                    '/api/delete_user'
                ],
                'valid_examples': [
                    '/api/users/{id}',
                    '/api/user-profiles/{id}',
                    '/api/order-items/{id}'
                ]
            }

        return {'violation_examples': [], 'valid_examples': []}

    def _generate_documentation_test_data(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test data for documentation rules."""
        rule_id = rule['id']

        if rule_id == 'R008':
            return {
                'violation_examples': [
                    '# Ascertain the authentication status of the current user session',
                    '# This routine persists the transactional data to the relational data store'
                ],
                'valid_examples': [
                    '# Check if user is logged in',
                    '# This function saves data to the database'
                ]
            }
        elif rule_id == 'R089':
            return {
                'violation_examples': [
                    'TODO: Fix this bug',
                    'TODO: Add tests later',
                    'FIXME: This needs work'
                ],
                'valid_examples': [
                    'TODO(john.doe): Fix login bug [BUG-123] [2024-12-31]',
                    'TODO(@team): Refactor API [TASK-456] [Q1-2025]',
                    'TODO(me): Add tests [2024-12-15]'
                ]
            }

        return {'violation_examples': [], 'valid_examples': []}

    def _generate_logging_test_data(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test data for logging rules."""
        rule_id = rule['id']

        if rule_id == 'R063':
            return {
                'violation_examples': [
                    '{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "User login"}\n{"timestamp": "2024-01-01T00:00:01Z", "level": "ERROR", "message": "Login failed"}'
                ],
                'valid_examples': [
                    '{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "User login"}',
                    '{"timestamp": "2024-01-01T00:00:01Z", "level": "ERROR", "message": "Login failed"}'
                ]
            }
        elif rule_id == 'R064':
            return {
                'violation_examples': [
                    '{"timestamp": "2024-01-01T00:00:00", "level": "INFO"}',
                    '{"timestamp": "2024-01-01T00:00:00+00:00", "level": "INFO"}'
                ],
                'valid_examples': [
                    '{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO"}',
                    '{"timestamp": "2024-01-01T00:00:00.000Z", "level": "INFO"}'
                ]
            }

        return {'violation_examples': [], 'valid_examples': []}

    def _generate_structure_test_data(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test data for structure rules."""
        rule_id = rule['id']

        if rule_id == 'R001':
            return {
                'violation_examples': [
                    'def large_function():\n    ' + '\n    '.join([f'    line_{i} = "This is line {i}"' for i in range(60)])
                ],
                'valid_examples': [
                    'def small_function():\n    return "Hello, World!"'
                ]
            }
        elif rule_id == 'R054':
            return {
                'violation_examples': [
                    'data_path = "C:\\\\Users\\\\data"',
                    'config_path = "/home/user/config"'
                ],
                'valid_examples': [
                    'data_path = config.get_path("data")',
                    'config_path = paths.get("config")'
                ]
            }

        return {'violation_examples': [], 'valid_examples': []}

    def _generate_code_quality_test_data(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test data for code quality rules."""
        rule_id = rule['id']

        if rule_id == 'R027':
            return {
                'violation_examples': [
                    'import os,sys,json',
                    'def function( a,b,c ):',
                    '    x=1+2+3'
                ],
                'valid_examples': [
                    'import os\nimport sys\nimport json',
                    'def function(a: int, b: str, c: bool) -> None:',
                    '    x = 1 + 2 + 3'
                ]
            }
        elif rule_id == 'R030':
            return {
                'violation_examples': [
                    'let data: any = {};',
                    'function process(input: any): any {',
                    '    return input;'
                ],
                'valid_examples': [
                    'let data: Record<string, unknown> = {};',
                    'function process(input: string): string {',
                    '    return input;'
                ]
            }

        return {'violation_examples': [], 'valid_examples': []}

    def _generate_generic_test_data(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic test data for unknown categories."""
        return {
            'violation_examples': [f'# Violation example for {rule["id"]}'],
            'valid_examples': [f'# Valid example for {rule["id"]}']
        }

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        return sorted(list(set(rule.get('category', 'unknown') for rule in self.rules)))

    def get_severities(self) -> List[str]:
        """Get all unique severities."""
        return sorted(list(set(rule.get('severity', 'unknown') for rule in self.rules)))

    def get_validators(self) -> List[str]:
        """Get all unique validators."""
        validators = set()
        for rule in self.rules:
            validator = rule.get('validator', '')
            if validator:
                # Extract validator class name
                validator_class = validator.split('.')[0]
                validators.add(validator_class)
        return sorted(list(validators))

    def get_constitutions(self) -> List[str]:
        """Get all unique constitutions."""
        return sorted(list(set(rule.get('constitution', 'unknown') for rule in self.rules)))

    def get_rule_count(self) -> int:
        """Get total number of rules."""
        return len(self.rules)

    def get_coverage_stats(self) -> Dict[str, Any]:
        """Get coverage statistics."""
        return {
            'total_rules': len(self.rules),
            'categories': len(self.get_categories()),
            'severities': len(self.get_severities()),
            'validators': len(self.get_validators()),
            'constitutions': len(self.get_constitutions()),
            'error_rules': len(self.get_rules_by_severity('error')),
            'warning_rules': len(self.get_rules_by_severity('warning'))
        }


# Global factory instance for easy access
test_factory = DynamicTestFactory()


def get_test_factory() -> DynamicTestFactory:
    """Get the global test factory instance."""
    return test_factory
