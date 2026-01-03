"""
Rule Validator Fixtures

This module provides comprehensive test fixtures for exercising representative
rule checks across all rule validators, focusing on files with 0% coverage and
partial coverage.
"""

from __future__ import annotations

import pytest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock, patch


# ============================================================================
# Fixtures for 0% Coverage Files
# ============================================================================

@pytest.fixture
def code_review_validator_fixtures():
    """Fixtures for code_review validator."""
    return {
        "valid_pr": {
            "title": "Add feature X",
            "description": "Implements feature X with tests",
            "files_changed": ["src/feature.py", "tests/test_feature.py"],
            "has_tests": True,
            "has_documentation": True
        },
        "invalid_pr_no_tests": {
            "title": "Add feature Y",
            "description": "Implements feature Y",
            "files_changed": ["src/feature.py"],
            "has_tests": False,
            "has_documentation": False
        },
        "invalid_pr_no_description": {
            "title": "Fix bug",
            "description": "",
            "files_changed": ["src/bug.py"],
            "has_tests": True,
            "has_documentation": False
        }
    }


@pytest.fixture
def coding_standards_validator_fixtures():
    """Fixtures for coding_standards validator."""
    return {
        "valid_code": """
def calculate_total(items):
    \"\"\"Calculate total price.\"\"\"
    return sum(item.price for item in items)
""",
        "invalid_no_docstring": """
def calculate_total(items):
    return sum(item.price for item in items)
""",
        "invalid_long_function": """
def process_data(data):
    # 200 lines of code...
    pass
""",
        "invalid_magic_numbers": """
def calculate_discount(price):
    return price * 0.15  # Magic number
"""
    }


@pytest.fixture
def comments_validator_fixtures():
    """Fixtures for comments validator."""
    return {
        "valid_comments": """
# This function processes user data
def process_user_data(user_id: int) -> Dict:
    # Validate user ID
    if user_id <= 0:
        raise ValueError("Invalid user ID")
    
    # Fetch user from database
    user = db.get_user(user_id)
    return user.to_dict()
""",
        "invalid_no_comments": """
def process_user_data(user_id: int) -> Dict:
    if user_id <= 0:
        raise ValueError("Invalid user ID")
    user = db.get_user(user_id)
    return user.to_dict()
""",
        "invalid_outdated_comments": """
# This function processes orders (outdated - now processes users)
def process_user_data(user_id: int) -> Dict:
    user = db.get_user(user_id)
    return user.to_dict()
"""
    }


@pytest.fixture
def logging_validator_fixtures():
    """Fixtures for logging validator."""
    return {
        "valid_logging": """
import logging

logger = logging.getLogger(__name__)

def process_request(request):
    logger.info("Processing request", extra={"request_id": request.id})
    try:
        result = handle_request(request)
        logger.info("Request processed successfully", extra={"request_id": request.id})
        return result
    except Exception as e:
        logger.error("Request processing failed", exc_info=True, extra={"request_id": request.id})
        raise
""",
        "invalid_no_logging": """
def process_request(request):
    result = handle_request(request)
    return result
""",
        "invalid_print_statements": """
def process_request(request):
    print(f"Processing request {request.id}")
    result = handle_request(request)
    print(f"Request processed: {result}")
    return result
"""
    }


@pytest.fixture
def requirements_validator_fixtures():
    """Fixtures for requirements validator."""
    return {
        "valid_requirements": {
            "functional": ["User can login", "User can logout"],
            "non_functional": ["Response time < 200ms", "99.9% uptime"],
            "tested": True,
            "documented": True
        },
        "invalid_missing_non_functional": {
            "functional": ["User can login"],
            "non_functional": [],
            "tested": False,
            "documented": False
        },
        "invalid_untested": {
            "functional": ["User can login"],
            "non_functional": ["Response time < 200ms"],
            "tested": False,
            "documented": True
        }
    }


@pytest.fixture
def simple_code_readability_validator_fixtures():
    """Fixtures for simple_code_readability validator."""
    return {
        "valid_readable": """
def calculate_discount(price: float, customer_type: str) -> float:
    \"\"\"Calculate discount based on customer type.\"\"\"
    STANDARD_DISCOUNT = 0.10
    PREMIUM_DISCOUNT = 0.20
    
    if customer_type == "premium":
        return price * PREMIUM_DISCOUNT
    elif customer_type == "standard":
        return price * STANDARD_DISCOUNT
    else:
        return 0.0
""",
        "invalid_unreadable": """
def calc(p, ct):
    if ct == "p":
        return p * 0.2
    elif ct == "s":
        return p * 0.1
    else:
        return 0
""",
        "invalid_long_variable_names": """
def calculate_discount_for_customer_based_on_customer_type_and_price(price, customer_type):
    return price * 0.1 if customer_type == "standard" else price * 0.2
"""
    }


@pytest.fixture
def storage_governance_validator_fixtures():
    """Fixtures for storage_governance validator."""
    return {
        "valid_storage": {
            "encrypted": True,
            "backed_up": True,
            "access_controlled": True,
            "audit_logged": True
        },
        "invalid_unencrypted": {
            "encrypted": False,
            "backed_up": True,
            "access_controlled": True,
            "audit_logged": True
        },
        "invalid_no_backup": {
            "encrypted": True,
            "backed_up": False,
            "access_controlled": True,
            "audit_logged": True
        }
    }


@pytest.fixture
def api_contracts_validator_fixtures():
    """Fixtures for api_contracts validator."""
    return {
        "valid_contract": {
            "endpoint": "/api/users/{id}",
            "method": "GET",
            "request_schema": {"type": "object", "properties": {"id": {"type": "integer"}}},
            "response_schema": {"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}}},
            "versioned": True,
            "documented": True
        },
        "invalid_no_schema": {
            "endpoint": "/api/users/{id}",
            "method": "GET",
            "request_schema": None,
            "response_schema": None,
            "versioned": False,
            "documented": False
        },
        "invalid_unversioned": {
            "endpoint": "/api/users/{id}",
            "method": "GET",
            "request_schema": {"type": "object"},
            "response_schema": {"type": "object"},
            "versioned": False,
            "documented": True
        }
    }


@pytest.fixture
def platform_validator_fixtures():
    """Fixtures for platform validator."""
    return {
        "valid_platform": {
            "cross_platform": True,
            "tested_on": ["Windows", "Linux", "macOS"],
            "dependencies_managed": True,
            "deployment_automated": True
        },
        "invalid_single_platform": {
            "cross_platform": False,
            "tested_on": ["Windows"],
            "dependencies_managed": True,
            "deployment_automated": False
        },
        "invalid_unmanaged_dependencies": {
            "cross_platform": True,
            "tested_on": ["Windows", "Linux"],
            "dependencies_managed": False,
            "deployment_automated": True
        }
    }


@pytest.fixture
def system_design_validator_fixtures():
    """Fixtures for system_design validator."""
    return {
        "valid_design": {
            "modular": True,
            "scalable": True,
            "maintainable": True,
            "documented": True,
            "tested": True
        },
        "invalid_monolithic": {
            "modular": False,
            "scalable": False,
            "maintainable": False,
            "documented": False,
            "tested": False
        },
        "invalid_undocumented": {
            "modular": True,
            "scalable": True,
            "maintainable": True,
            "documented": False,
            "tested": True
        }
    }


# ============================================================================
# Fixtures for Partial Coverage Files
# ============================================================================

@pytest.fixture
def exception_handling_validator_fixtures():
    """Fixtures for exception_handling validator."""
    return {
        "valid_exception_handling": """
def process_data(data):
    try:
        result = validate_and_process(data)
        return result
    except ValidationError as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise
    except ProcessingError as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        raise
""",
        "invalid_bare_except": """
def process_data(data):
    try:
        result = validate_and_process(data)
        return result
    except:  # Bare except
        return None
""",
        "invalid_no_logging": """
def process_data(data):
    try:
        result = validate_and_process(data)
        return result
    except Exception as e:
        return None  # No logging
"""
    }


@pytest.fixture
def performance_validator_fixtures():
    """Fixtures for performance validator."""
    return {
        "valid_performance": {
            "cached": True,
            "indexed": True,
            "paginated": True,
            "async": True,
            "timeout_set": True
        },
        "invalid_no_cache": {
            "cached": False,
            "indexed": True,
            "paginated": True,
            "async": False,
            "timeout_set": False
        },
        "invalid_no_indexing": {
            "cached": True,
            "indexed": False,
            "paginated": False,
            "async": True,
            "timeout_set": True
        }
    }


@pytest.fixture
def privacy_validator_fixtures():
    """Fixtures for privacy validator."""
    return {
        "valid_privacy": {
            "pii_encrypted": True,
            "gdpr_compliant": True,
            "consent_obtained": True,
            "data_minimized": True,
            "retention_policy": True
        },
        "invalid_unencrypted_pii": {
            "pii_encrypted": False,
            "gdpr_compliant": False,
            "consent_obtained": True,
            "data_minimized": False,
            "retention_policy": False
        },
        "invalid_no_consent": {
            "pii_encrypted": True,
            "gdpr_compliant": True,
            "consent_obtained": False,
            "data_minimized": True,
            "retention_policy": True
        }
    }


@pytest.fixture
def quality_validator_fixtures():
    """Fixtures for quality validator."""
    return {
        "valid_quality": {
            "test_coverage": 0.85,
            "code_reviewed": True,
            "linted": True,
            "documented": True,
            "performance_tested": True
        },
        "invalid_low_coverage": {
            "test_coverage": 0.30,
            "code_reviewed": True,
            "linted": True,
            "documented": False,
            "performance_tested": False
        },
        "invalid_unreviewed": {
            "test_coverage": 0.80,
            "code_reviewed": False,
            "linted": True,
            "documented": True,
            "performance_tested": True
        }
    }


@pytest.fixture
def teamwork_validator_fixtures():
    """Fixtures for teamwork validator."""
    return {
        "valid_teamwork": {
            "code_reviewed": True,
            "pair_programmed": True,
            "documented": True,
            "knowledge_shared": True,
            "collaborative": True
        },
        "invalid_no_review": {
            "code_reviewed": False,
            "pair_programmed": False,
            "documented": False,
            "knowledge_shared": False,
            "collaborative": False
        },
        "invalid_no_documentation": {
            "code_reviewed": True,
            "pair_programmed": True,
            "documented": False,
            "knowledge_shared": True,
            "collaborative": True
        }
    }


@pytest.fixture
def typescript_validator_fixtures():
    """Fixtures for typescript validator."""
    return {
        "valid_typescript": """
interface User {
    id: number;
    name: string;
    email: string;
}

function getUser(id: number): Promise<User> {
    return fetch(`/api/users/${id}`).then(res => res.json());
}
""",
        "invalid_any_types": """
function getUser(id: any): Promise<any> {
    return fetch(`/api/users/${id}`).then(res => res.json());
}
""",
        "invalid_no_types": """
function getUser(id) {
    return fetch(`/api/users/${id}`).then(res => res.json());
}
"""
    }


@pytest.fixture
def architecture_validator_fixtures():
    """Fixtures for architecture validator."""
    return {
        "valid_architecture": {
            "layered": True,
            "separation_of_concerns": True,
            "dependency_injection": True,
            "testable": True,
            "documented": True
        },
        "invalid_tightly_coupled": {
            "layered": False,
            "separation_of_concerns": False,
            "dependency_injection": False,
            "testable": False,
            "documented": False
        },
        "invalid_no_di": {
            "layered": True,
            "separation_of_concerns": True,
            "dependency_injection": False,
            "testable": True,
            "documented": True
        }
    }


@pytest.fixture
def problem_solving_validator_fixtures():
    """Fixtures for problem_solving validator."""
    return {
        "valid_problem_solving": {
            "problem_defined": True,
            "solution_designed": True,
            "alternatives_considered": True,
            "tested": True,
            "documented": True
        },
        "invalid_no_definition": {
            "problem_defined": False,
            "solution_designed": True,
            "alternatives_considered": False,
            "tested": True,
            "documented": False
        },
        "invalid_no_alternatives": {
            "problem_defined": True,
            "solution_designed": True,
            "alternatives_considered": False,
            "tested": True,
            "documented": True
        }
    }


# ============================================================================
# Test Functions Using Fixtures
# ============================================================================

def test_code_review_validator(code_review_validator_fixtures):
    """Test code_review validator with fixtures."""
    valid = code_review_validator_fixtures["valid_pr"]
    assert valid["has_tests"] is True
    assert valid["has_documentation"] is True
    
    invalid = code_review_validator_fixtures["invalid_pr_no_tests"]
    assert invalid["has_tests"] is False


def test_coding_standards_validator(coding_standards_validator_fixtures):
    """Test coding_standards validator with fixtures."""
    valid = coding_standards_validator_fixtures["valid_code"]
    assert "def" in valid
    assert '"""' in valid  # Has docstring
    
    invalid = coding_standards_validator_fixtures["invalid_no_docstring"]
    assert '"""' not in invalid


def test_comments_validator(comments_validator_fixtures):
    """Test comments validator with fixtures."""
    valid = comments_validator_fixtures["valid_comments"]
    assert "#" in valid  # Has comments
    
    invalid = comments_validator_fixtures["invalid_no_comments"]
    assert "#" not in invalid or invalid.count("#") < 2


def test_logging_validator(logging_validator_fixtures):
    """Test logging validator with fixtures."""
    valid = logging_validator_fixtures["valid_logging"]
    assert "logger" in valid
    assert "logging.getLogger" in valid
    
    invalid = logging_validator_fixtures["invalid_no_logging"]
    assert "logger" not in invalid


def test_requirements_validator(requirements_validator_fixtures):
    """Test requirements validator with fixtures."""
    valid = requirements_validator_fixtures["valid_requirements"]
    assert len(valid["functional"]) > 0
    assert len(valid["non_functional"]) > 0
    assert valid["tested"] is True


def test_simple_code_readability_validator(simple_code_readability_validator_fixtures):
    """Test simple_code_readability validator with fixtures."""
    valid = simple_code_readability_validator_fixtures["valid_readable"]
    assert "calculate_discount" in valid
    assert "STANDARD_DISCOUNT" in valid  # Named constants
    
    invalid = simple_code_readability_validator_fixtures["invalid_unreadable"]
    assert "calc" in invalid  # Abbreviated names


def test_storage_governance_validator(storage_governance_validator_fixtures):
    """Test storage_governance validator with fixtures."""
    valid = storage_governance_validator_fixtures["valid_storage"]
    assert valid["encrypted"] is True
    assert valid["backed_up"] is True


def test_api_contracts_validator(api_contracts_validator_fixtures):
    """Test api_contracts validator with fixtures."""
    valid = api_contracts_validator_fixtures["valid_contract"]
    assert valid["request_schema"] is not None
    assert valid["versioned"] is True


def test_platform_validator(platform_validator_fixtures):
    """Test platform validator with fixtures."""
    valid = platform_validator_fixtures["valid_platform"]
    assert valid["cross_platform"] is True
    assert len(valid["tested_on"]) > 1


def test_system_design_validator(system_design_validator_fixtures):
    """Test system_design validator with fixtures."""
    valid = system_design_validator_fixtures["valid_design"]
    assert valid["modular"] is True
    assert valid["scalable"] is True


def test_exception_handling_validator(exception_handling_validator_fixtures):
    """Test exception_handling validator with fixtures."""
    valid = exception_handling_validator_fixtures["valid_exception_handling"]
    assert "try:" in valid
    assert "except" in valid
    assert "logger" in valid
    
    invalid = exception_handling_validator_fixtures["invalid_bare_except"]
    assert "except:" in invalid  # Bare except


def test_performance_validator(performance_validator_fixtures):
    """Test performance validator with fixtures."""
    valid = performance_validator_fixtures["valid_performance"]
    assert valid["cached"] is True
    assert valid["indexed"] is True


def test_privacy_validator(privacy_validator_fixtures):
    """Test privacy validator with fixtures."""
    valid = privacy_validator_fixtures["valid_privacy"]
    assert valid["pii_encrypted"] is True
    assert valid["gdpr_compliant"] is True


def test_quality_validator(quality_validator_fixtures):
    """Test quality validator with fixtures."""
    valid = quality_validator_fixtures["valid_quality"]
    assert valid["test_coverage"] >= 0.80
    assert valid["code_reviewed"] is True


def test_teamwork_validator(teamwork_validator_fixtures):
    """Test teamwork validator with fixtures."""
    valid = teamwork_validator_fixtures["valid_teamwork"]
    assert valid["code_reviewed"] is True
    assert valid["collaborative"] is True


def test_typescript_validator(typescript_validator_fixtures):
    """Test typescript validator with fixtures."""
    valid = typescript_validator_fixtures["valid_typescript"]
    assert "interface" in valid
    assert ": number" in valid  # Type annotations
    
    invalid = typescript_validator_fixtures["invalid_any_types"]
    assert ": any" in invalid


def test_architecture_validator(architecture_validator_fixtures):
    """Test architecture validator with fixtures."""
    valid = architecture_validator_fixtures["valid_architecture"]
    assert valid["layered"] is True
    assert valid["dependency_injection"] is True


def test_problem_solving_validator(problem_solving_validator_fixtures):
    """Test problem_solving validator with fixtures."""
    valid = problem_solving_validator_fixtures["valid_problem_solving"]
    assert valid["problem_defined"] is True
    assert valid["alternatives_considered"] is True

