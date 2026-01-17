"""
Pytest fixtures for ZeroUI Observability Layer acceptance tests.
"""

import pytest
from typing import Dict, Any


@pytest.fixture
def context() -> Dict[str, Any]:
    """
    Provide test context for acceptance tests.
    
    Returns:
        Test context dictionary with default values
    """
    return {
        "tenant_id": "test-tenant-001",
        "component": "test",
        "channel": "backend",
        "test_run_id": "test-run-001",
    }
