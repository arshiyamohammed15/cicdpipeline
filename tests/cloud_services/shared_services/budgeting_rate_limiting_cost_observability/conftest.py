"""
Test fixtures for Budgeting Rate Limiting Cost Observability.

Uses standardized module setup from root conftest.py
"""
import pytest
from pathlib import Path
import sys

# Root conftest should have set up budgeting_rate_limiting_cost_observability package
# But ensure module path is in sys.path
MODULE_ROOT = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "shared-services" / "budgeting-rate-limiting-cost-observability"
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

# Import will work because root conftest.py sets up the package structure
# Tests can use: from budgeting_rate_limiting_cost_observability.main import app
