"""
Pytest fixtures and utilities for ZeroUI 2.0 validator tests.

This module provides pytest-style fixtures that work alongside the existing
unittest-based tests, allowing for gradual migration to pytest if desired.
"""

import pytest
import ast
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from validator.models import Violation, Severity


@pytest.fixture
def test_file_path():
    """Provide a standard test file path."""
    return "test.py"


@pytest.fixture
def config_dir():
    """Provide the configuration directory path."""
    return Path(__file__).parent.parent.parent.parent / "config"


@pytest.fixture
def sample_python_code():
    """Provide sample Python code for testing."""
    return '''
def example_function():
    """Example function for testing."""
    return "Hello, World!"

class ExampleClass:
    """Example class for testing."""
    
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value
'''


@pytest.fixture
def sample_ast():
    """Provide a sample AST for testing."""
    code = '''
def example_function():
    return "Hello, World!"

class ExampleClass:
    def __init__(self):
        self.value = 42
'''
    return ast.parse(code)


@pytest.fixture
def sample_violations():
    """Provide sample violations for testing."""
    return [
        Violation(
            rule_id="rule_001",
            severity=Severity.ERROR,
            message="Sample violation",
            file_path="test.py",
            line_number=1,
            column_number=1
        ),
        Violation(
            rule_id="rule_002", 
            severity=Severity.WARNING,
            message="Sample warning",
            file_path="test.py",
            line_number=2,
            column_number=1
        )
    ]


@pytest.fixture
def mock_config():
    """Provide mock configuration data."""
    return {
        "rules": {
            "rule_001": {
                "enabled": True,
                "severity": "error",
                "message": "Test rule"
            }
        },
        "patterns": {
            "test_pattern": {
                "enabled": True,
                "description": "Test pattern"
            }
        }
    }


# Pytest-style assertion helpers
def assert_violation_exists(violations: List[Violation], rule_id: str, 
                          severity: Severity = None, message_contains: str = None):
    """
    Assert that a specific violation exists in the violations list.
    
    Args:
        violations: List of violations to check
        rule_id: Expected rule ID
        severity: Expected severity level
        message_contains: Expected message content
    """
    matching_violations = [
        v for v in violations 
        if v.rule_id == rule_id
    ]
    
    assert len(matching_violations) > 0, f"No violations found for rule {rule_id}"
    
    if severity:
        severity_matches = [v for v in matching_violations if v.severity == severity]
        assert len(severity_matches) > 0, f"No violations found with severity {severity}"
    
    if message_contains:
        message_matches = [
            v for v in matching_violations 
            if message_contains in v.message
        ]
        assert len(message_matches) > 0, f"No violations found with message containing '{message_contains}'"


def assert_no_violations(violations: List[Violation]):
    """Assert that no violations exist."""
    assert len(violations) == 0, f"Expected no violations, but found {len(violations)}"


def assert_violation_count(violations: List[Violation], expected_count: int):
    """Assert the exact number of violations."""
    assert len(violations) == expected_count, f"Expected {expected_count} violations, but found {len(violations)}"


# Pytest markers for test categorization
pytestmark = [
    pytest.mark.unittest,  # Mark all tests in this module as unittest-compatible
]


# Pytest-style test discovery helpers
def discover_test_files(test_dir: Path) -> List[Path]:
    """Discover all test files in a directory."""
    return list(test_dir.glob("test_*.py"))


def load_test_config(config_path: Path) -> Dict[str, Any]:
    """Load test configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Pytest hooks for test setup/teardown
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for all tests."""
    # Setup code here
    yield
    # Teardown code here


# Pytest parametrize helpers
def parametrize_test_cases(test_cases: List[Dict[str, Any]]):
    """Helper to parametrize test cases."""
    return pytest.mark.parametrize("test_case", test_cases)


# Sample test cases for parametrized testing
SAMPLE_TEST_CASES = [
    {
        "name": "valid_code",
        "code": "def valid_function(): pass",
        "expected_violations": 0
    },
    {
        "name": "invalid_code", 
        "code": "def invalid_function(): pass  # TODO: implement",
        "expected_violations": 1
    }
]
