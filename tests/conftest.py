"""
Root-level pytest configuration for ZeroUI test suites.

Provides:
- Automatic evidence pack generation via pytest hooks
- Marker registration
- Shared fixtures available to all test modules
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from _pytest.config import Config
from _pytest.terminal import TerminalReporter

# Add src/ to path for imports
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

# Import evidence builder
try:
    from tests.shared_harness import EvidencePackBuilder
except ImportError:
    # Fallback if shared_harness not available
    EvidencePackBuilder = None


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    """Register custom markers and configure evidence generation."""
    # Markers are registered in pytest.ini, but we ensure they're recognized
    config.addinivalue_line(
        "markers", "dgp_regression: Regression tests for DG&P module"
    )
    config.addinivalue_line(
        "markers", "dgp_security: Security tests for DG&P module"
    )
    config.addinivalue_line(
        "markers", "dgp_performance: Performance tests for DG&P module"
    )
    config.addinivalue_line(
        "markers", "alerting_regression: Regression tests for Alerting module"
    )
    config.addinivalue_line(
        "markers", "alerting_security: Security tests for Alerting module"
    )
    config.addinivalue_line(
        "markers", "budgeting_regression: Regression tests for Budgeting module"
    )
    config.addinivalue_line(
        "markers", "deployment_regression: Regression tests for Deployment module"
    )


@pytest.fixture(scope="session")
def evidence_builder(request) -> EvidencePackBuilder | None:
    """Provide evidence pack builder for test session."""
    if EvidencePackBuilder is None:
        return None
    
    # Determine module name from test path
    test_path = request.config.rootpath
    module_name = "zeroui"
    
    # Try to infer module from test path
    if "data-governance-privacy" in str(test_path):
        module_name = "dgp"
    elif "alerting" in str(test_path):
        module_name = "alerting"
    elif "budgeting" in str(test_path):
        module_name = "budgeting"
    elif "deployment" in str(test_path):
        module_name = "deployment"
    
    output_dir = test_path / "artifacts" / "evidence"
    return EvidencePackBuilder(output_dir=str(output_dir))


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Generate evidence pack after test session completes."""
    if EvidencePackBuilder is None:
        return
    
    # Collect evidence from session
    builder = EvidencePackBuilder(output_dir=str(session.config.rootpath / "artifacts" / "evidence"))
    
    # Add test summary
    test_summary = {
        "total_tests": session.testscollected,
        "passed": sum(1 for item in session.items if hasattr(item, "rep_call") and item.rep_call.outcome == "passed"),
        "failed": sum(1 for item in session.items if hasattr(item, "rep_call") and item.rep_call.outcome == "failed"),
        "skipped": sum(1 for item in session.items if hasattr(item, "rep_call") and item.rep_call.outcome == "skipped"),
        "exit_status": exitstatus,
    }
    builder.add_metrics({"test_summary": test_summary})
    
    # Build evidence pack
    try:
        evidence_path = builder.build(module_name="zeroui", test_suite="session")
        print(f"\n✓ Evidence pack generated: {evidence_path}")
    except Exception as e:
        print(f"\n⚠ Failed to generate evidence pack: {e}")

