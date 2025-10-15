"""
Intelligent Test Data Generator for ZeroUI 2.0 Rules

This module provides intelligent test data generation based on rule characteristics,
creating appropriate violation and valid examples for each rule type.
"""

import json
import re
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DataTemplate:
    """Template for generating test data for a specific rule type."""
    rule_id: str
    category: str
    violation_examples: List[str]
    valid_examples: List[str]
    test_files: List[str]
    metadata: Dict[str, Any]


class DataGenerator:
    """
    Intelligent test data generator that creates appropriate test data
    based on rule characteristics and category.
    """

    def __init__(self):
        """Initialize the test data generator."""
        self.templates = self._load_templates()
        self.patterns = self._load_patterns()

    def _load_templates(self) -> Dict[str, DataTemplate]:
        """Load test data templates for different rule types."""
        return {
            'security': DataTemplate(
                rule_id='',
                category='security',
                violation_examples=[
                    'password = "secret123"',
                    'api_key = "sk-1234567890abcdef"',
                    'token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"',
                    'SECRET_KEY = "django-insecure-abc123"',
                    'DATABASE_URL = "postgresql://user:pass@localhost/db"'
                ],
                valid_examples=[
                    'password = os.getenv("DB_PASSWORD")',
                    'api_key = keyring.get_password("service", "api_key")',
                    'token = get_auth_token()',
                    'SECRET_KEY = os.getenv("SECRET_KEY")',
                    'DATABASE_URL = os.getenv("DATABASE_URL")'
                ],
                test_files=['security_violation.py', 'security_valid.py'],
                metadata={'severity': 'error', 'validator': 'security_validator'}
            ),
            'api': DataTemplate(
                rule_id='',
                category='api',
                violation_examples=[
                    'POST /api/getUserData',
                    'GET /api/createUser',
                    '/api/get_user_data',
                    '/api/createUser',
                    '{"error": "Invalid request"}'
                ],
                valid_examples=[
                    'GET /api/users/{id}',
                    'POST /api/users',
                    '/api/users/{id}',
                    '/api/user-profiles/{id}',
                    '{"error": {"code": "INVALID_REQUEST", "message": "Invalid request"}}'
                ],
                test_files=['api_violation.yaml', 'api_valid.yaml'],
                metadata={'severity': 'error', 'validator': 'api_validator'}
            ),
            'documentation': DataTemplate(
                rule_id='',
                category='documentation',
                violation_examples=[
                    '# Ascertain the authentication status of the current user session',
                    '# This routine persists the transactional data to the relational data store',
                    'TODO: Fix this bug',
                    'TODO: Add tests later',
                    'FIXME: This needs work'
                ],
                valid_examples=[
                    '# Check if user is logged in',
                    '# This function saves data to the database',
                    'TODO(john.doe): Fix login bug [BUG-123] [2024-12-31]',
                    'TODO(@team): Refactor API [TASK-456] [Q1-2025]',
                    'TODO(me): Add tests [2024-12-15]'
                ],
                test_files=['comment_violation.py', 'comment_valid.py'],
                metadata={'severity': 'error', 'validator': 'comment_validator'}
            ),
            'logging': DataTemplate(
                rule_id='',
                category='logging',
                violation_examples=[
                    '{"timestamp": "2024-01-01T00:00:00", "level": "INFO"}',
                    '{"timestamp": "2024-01-01T00:00:00+00:00", "level": "INFO"}',
                    '{"level": "INFO", "message": "User login"}',
                    '{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "User login"}\n{"timestamp": "2024-01-01T00:00:01Z", "level": "ERROR", "message": "Login failed"}'
                ],
                valid_examples=[
                    '{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO"}',
                    '{"timestamp": "2024-01-01T00:00:00.000Z", "level": "INFO"}',
                    '{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "User login"}',
                    '{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "User login"}',
                    '{"timestamp": "2024-01-01T00:00:01Z", "level": "ERROR", "message": "Login failed"}'
                ],
                test_files=['log_violation.jsonl', 'log_valid.jsonl'],
                metadata={'severity': 'error', 'validator': 'logging_validator'}
            ),
            'structure': DataTemplate(
                rule_id='',
                category='structure',
                violation_examples=[
                    'def large_function():\n    ' + '\n    '.join([f'    line_{i} = "This is line {i}"' for i in range(60)]),
                    'data_path = "C:\\\\Users\\\\data"',
                    'config_path = "/home/user/config"',
                    'def function_without_tests():\n    return "Hello, World!"'
                ],
                valid_examples=[
                    'def small_function():\n    return "Hello, World!"',
                    'data_path = config.get_path("data")',
                    'config_path = paths.get("config")',
                    'def function_with_tests():\n    return "Hello, World!"\n\ndef test_function_with_tests():\n    assert function_with_tests() == "Hello, World!"'
                ],
                test_files=['structure_violation.py', 'structure_valid.py'],
                metadata={'severity': 'error', 'validator': 'structure_validator'}
            ),
            'code_quality': DataTemplate(
                rule_id='',
                category='code_quality',
                violation_examples=[
                    'import os,sys,json',
                    'def function( a,b,c ):',
                    '    x=1+2+3',
                    'let data: any = {};',
                    'function process(input: any): any {'
                ],
                valid_examples=[
                    'import os\nimport sys\nimport json',
                    'def function(a: int, b: str, c: bool) -> None:',
                    '    x = 1 + 2 + 3',
                    'let data: Record<string, unknown> = {};',
                    'function process(input: string): string {'
                ],
                test_files=['code_violation.py', 'code_valid.py', 'code_violation.ts', 'code_valid.ts'],
                metadata={'severity': 'error', 'validator': 'code_quality_validator'}
            )
        }

    def _load_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for generating rule-specific test data."""
        return {
            'loc_limit': {
                'violation': ['def large_function():\n    ' + '\n    '.join([f'    line_{i} = "This is line {i}"' for i in range(60)])],
                'valid': ['def small_function():\n    return "Hello, World!"']
            },
            'todo_policy': {
                'violation': ['TODO: Fix this bug', 'TODO: Add tests later', 'FIXME: This needs work'],
                'valid': ['TODO(john.doe): Fix login bug [BUG-123] [2024-12-31]', 'TODO(@team): Refactor API [TASK-456] [Q1-2025]', 'TODO(me): Add tests [2024-12-15]']
            },
            'http_verbs': {
                'violation': ['POST /api/getUserData', 'GET /api/createUser', 'PUT /api/deleteUser'],
                'valid': ['GET /api/users/{id}', 'POST /api/users', 'PUT /api/users/{id}', 'DELETE /api/users/{id}']
            },
            'uuid_format': {
                'violation': ['user_id = 123', 'user_id = "abc-123"', 'user_id = "12345678-1234-1234-1234-123456789012"'],
                'valid': ['user_id = "01234567-89ab-7def-0123-456789abcdef"', 'user_id = "01234567-89ab-7def-0123-456789abcdef"']
            },
            'timestamp_format': {
                'violation': ['{"timestamp": "2024-01-01T00:00:00"}', '{"timestamp": "2024-01-01T00:00:00+00:00"}'],
                'valid': ['{"timestamp": "2024-01-01T00:00:00Z"}', '{"timestamp": "2024-01-01T00:00:00.000Z"}']
            },
            'jsonl_format': {
                'violation': ['{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "User login"}\n{"timestamp": "2024-01-01T00:00:01Z", "level": "ERROR", "message": "Login failed"}'],
                'valid': ['{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "User login"}', '{"timestamp": "2024-01-01T00:00:01Z", "level": "ERROR", "message": "Login failed"}']
            }
        }

    def generate_test_data(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate test data for a specific rule.

        Args:
            rule: Rule dictionary from rules.json

        Returns:
            Dictionary containing test data
        """
        rule_id = rule.get('id', '')
        category = rule.get('category', 'unknown')
        rule_name = rule.get('name', '').lower()

        # Get base template for category
        template = self.templates.get(category, self.templates['code_quality'])

        # Generate rule-specific data
        violation_examples = self._generate_violation_examples(rule, template)
        valid_examples = self._generate_valid_examples(rule, template)
        test_files = self._generate_test_files(rule, template)

        return {
            'rule_id': rule_id,
            'category': category,
            'severity': rule.get('severity', 'unknown'),
            'validator': rule.get('validator', ''),
            'constitution': rule.get('constitution', ''),
            'error_code': rule.get('error_code', ''),
            'violation_examples': violation_examples,
            'valid_examples': valid_examples,
            'test_files': test_files,
            'metadata': {
                'generated_by': 'DataGenerator',
                'rule_name': rule.get('name', ''),
                'description': rule.get('description', ''),
                'template_used': category
            }
        }

    def _generate_violation_examples(self, rule: Dict[str, Any], template: DataTemplate) -> List[str]:
        """Generate violation examples for a rule."""
        rule_id = rule.get('id', '')
        rule_name = rule.get('name', '').lower()

        # Check for specific patterns
        if 'loc' in rule_name and 'limit' in rule_name:
            return self.patterns.get('loc_limit', {}).get('violation', template.violation_examples)
        elif 'todo' in rule_name:
            return self.patterns.get('todo_policy', {}).get('violation', template.violation_examples)
        elif 'http' in rule_name and 'verb' in rule_name:
            return self.patterns.get('http_verbs', {}).get('violation', template.violation_examples)
        elif 'uuid' in rule_name:
            return self.patterns.get('uuid_format', {}).get('violation', template.violation_examples)
        elif 'timestamp' in rule_name:
            return self.patterns.get('timestamp_format', {}).get('violation', template.violation_examples)
        elif 'jsonl' in rule_name:
            return self.patterns.get('jsonl_format', {}).get('violation', template.violation_examples)

        # Use template examples with rule-specific modifications
        examples = template.violation_examples.copy()

        # Add rule-specific modifications
        if rule_id == 'R001':  # LOC Limit
            examples.append('def large_function():\n    ' + '\n    '.join([f'    line_{i} = "This is line {i}"' for i in range(60)]))
        elif rule_id == 'R008':  # Simple English Comments
            examples.extend([
                '# Ascertain the authentication status of the current user session',
                '# This routine persists the transactional data to the relational data store'
            ])
        elif rule_id == 'R013':  # HTTP Verbs
            examples.extend(['POST /api/getUserData', 'GET /api/createUser'])
        elif rule_id == 'R015':  # UUIDv7 IDs
            examples.extend(['user_id = 123', 'user_id = "abc-123"'])
        elif rule_id == 'R063':  # JSONL Format
            examples.append('{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "User login"}\n{"timestamp": "2024-01-01T00:00:01Z", "level": "ERROR", "message": "Login failed"}')

        return examples

    def _generate_valid_examples(self, rule: Dict[str, Any], template: DataTemplate) -> List[str]:
        """Generate valid examples for a rule."""
        rule_id = rule.get('id', '')
        rule_name = rule.get('name', '').lower()

        # Check for specific patterns
        if 'loc' in rule_name and 'limit' in rule_name:
            return self.patterns.get('loc_limit', {}).get('valid', template.valid_examples)
        elif 'todo' in rule_name:
            return self.patterns.get('todo_policy', {}).get('valid', template.valid_examples)
        elif 'http' in rule_name and 'verb' in rule_name:
            return self.patterns.get('http_verbs', {}).get('valid', template.valid_examples)
        elif 'uuid' in rule_name:
            return self.patterns.get('uuid_format', {}).get('valid', template.valid_examples)
        elif 'timestamp' in rule_name:
            return self.patterns.get('timestamp_format', {}).get('valid', template.valid_examples)
        elif 'jsonl' in rule_name:
            return self.patterns.get('jsonl_format', {}).get('valid', template.valid_examples)

        # Use template examples with rule-specific modifications
        examples = template.valid_examples.copy()

        # Add rule-specific modifications
        if rule_id == 'R001':  # LOC Limit
            examples.append('def small_function():\n    return "Hello, World!"')
        elif rule_id == 'R008':  # Simple English Comments
            examples.extend([
                '# Check if user is logged in',
                '# This function saves data to the database'
            ])
        elif rule_id == 'R013':  # HTTP Verbs
            examples.extend(['GET /api/users/{id}', 'POST /api/users'])
        elif rule_id == 'R015':  # UUIDv7 IDs
            examples.extend(['user_id = "01234567-89ab-7def-0123-456789abcdef"'])
        elif rule_id == 'R063':  # JSONL Format
            examples.extend([
                '{"timestamp": "2024-01-01T00:00:00Z", "level": "INFO", "message": "User login"}',
                '{"timestamp": "2024-01-01T00:00:01Z", "level": "ERROR", "message": "Login failed"}'
            ])

        return examples

    def _generate_test_files(self, rule: Dict[str, Any], template: DataTemplate) -> List[str]:
        """Generate test file names for a rule."""
        rule_id = rule.get('id', '')
        category = rule.get('category', 'unknown')

        # Generate category-specific test files
        if category == 'security':
            return [f'{rule_id}_security_violation.py', f'{rule_id}_security_valid.py']
        elif category == 'api':
            return [f'{rule_id}_api_violation.yaml', f'{rule_id}_api_valid.yaml']
        elif category == 'documentation':
            return [f'{rule_id}_comment_violation.py', f'{rule_id}_comment_valid.py']
        elif category == 'logging':
            return [f'{rule_id}_log_violation.jsonl', f'{rule_id}_log_valid.jsonl']
        elif category == 'structure':
            return [f'{rule_id}_structure_violation.py', f'{rule_id}_structure_valid.py']
        elif category == 'code_quality':
            return [f'{rule_id}_code_violation.py', f'{rule_id}_code_valid.py', f'{rule_id}_code_violation.ts', f'{rule_id}_code_valid.ts']
        else:
            return [f'{rule_id}_violation.txt', f'{rule_id}_valid.txt']

    def generate_fixture_files(self, rules: List[Dict[str, Any]], output_dir: str = "tests/fixtures") -> Dict[str, List[str]]:
        """
        Generate fixture files for all rules.

        Args:
            rules: List of rule dictionaries
            output_dir: Output directory for fixture files

        Returns:
            Dictionary mapping rule IDs to generated file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        generated_files = {}

        for rule in rules:
            rule_id = rule.get('id', '')
            test_data = self.generate_test_data(rule)

            rule_files = []

            # Generate violation files
            for i, violation_example in enumerate(test_data['violation_examples']):
                filename = f"{rule_id}_violation_{i+1}.txt"
                filepath = output_path / filename

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# Violation example for {rule_id}: {rule.get('name', '')}\n")
                    f.write(f"# {rule.get('description', '')}\n\n")
                    f.write(violation_example)

                rule_files.append(str(filepath))

            # Generate valid files
            for i, valid_example in enumerate(test_data['valid_examples']):
                filename = f"{rule_id}_valid_{i+1}.txt"
                filepath = output_path / filename

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# Valid example for {rule_id}: {rule.get('name', '')}\n")
                    f.write(f"# {rule.get('description', '')}\n\n")
                    f.write(valid_example)

                rule_files.append(str(filepath))

            generated_files[rule_id] = rule_files

        return generated_files

    def generate_test_data_summary(self, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of test data for all rules.

        Args:
            rules: List of rule dictionaries

        Returns:
            Summary dictionary with statistics and metadata
        """
        summary = {
            'total_rules': len(rules),
            'categories': {},
            'severities': {},
            'validators': {},
            'constitutions': {},
            'test_data_stats': {
                'total_violation_examples': 0,
                'total_valid_examples': 0,
                'total_test_files': 0
            }
        }

        for rule in rules:
            category = rule.get('category', 'unknown')
            severity = rule.get('severity', 'unknown')
            validator = rule.get('validator', '').split('.')[0] if rule.get('validator') else 'unknown'
            constitution = rule.get('constitution', 'unknown')

            # Count by category
            summary['categories'][category] = summary['categories'].get(category, 0) + 1

            # Count by severity
            summary['severities'][severity] = summary['severities'].get(severity, 0) + 1

            # Count by validator
            summary['validators'][validator] = summary['validators'].get(validator, 0) + 1

            # Count by constitution
            summary['constitutions'][constitution] = summary['constitutions'].get(constitution, 0) + 1

            # Generate test data and count examples
            test_data = self.generate_test_data(rule)
            summary['test_data_stats']['total_violation_examples'] += len(test_data['violation_examples'])
            summary['test_data_stats']['total_valid_examples'] += len(test_data['valid_examples'])
            summary['test_data_stats']['total_test_files'] += len(test_data['test_files'])

        return summary


# Global generator instance
test_data_generator = DataGenerator()


def get_test_data_generator() -> DataGenerator:
    """Get the global test data generator instance."""
    return test_data_generator


if __name__ == "__main__":
    # Example usage
    generator = DataGenerator()

    # Load rules from JSON
    with open('tools/validator/rules.json', 'r') as f:
        rules_data = json.load(f)
        rules = rules_data.get('rules', [])

    # Generate test data for all rules
    print("Generating test data for all rules...")
    for rule in rules[:5]:  # Test with first 5 rules
        test_data = generator.generate_test_data(rule)
        print(f"Rule {rule['id']}: {len(test_data['violation_examples'])} violations, {len(test_data['valid_examples'])} valid examples")

    # Generate summary
    summary = generator.generate_test_data_summary(rules)
    print(f"\nSummary: {summary['total_rules']} rules, {summary['test_data_stats']['total_violation_examples']} violation examples, {summary['test_data_stats']['total_valid_examples']} valid examples")
