from __future__ import annotations
"""
Pytest plugin for automatic evidence pack generation.

This plugin hooks into pytest's test execution lifecycle to:
1. Collect ERIS receipts during test runs
2. Capture configuration snapshots
3. Aggregate performance metrics
4. Generate timestamped evidence packs after test completion
"""


import json
from pathlib import Path
from typing import Any, Dict, List

import pytest
from _pytest.config import Config
from _pytest.nodes import Item
from _pytest.reports import TestReport

try:
    from tests.shared_harness import EvidencePackBuilder
except ImportError:
    EvidencePackBuilder = None


class EvidenceCollector:
    """Collects evidence during test execution."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.receipts: List[Dict[str, Any]] = []
        self.config_snapshots: List[Dict[str, Any]] = []
        self.metrics: List[Dict[str, Any]] = []
        self.test_results: List[Dict[str, Any]] = []

    def add_receipt(self, receipt: Dict[str, Any]) -> None:
        """Add an ERIS receipt."""
        self.receipts.append(receipt)

    def add_config(self, name: str, config: Dict[str, Any]) -> None:
        """Add a configuration snapshot."""
        self.config_snapshots.append({"name": name, "config": config})

    def add_metrics(self, metrics: Dict[str, Any]) -> None:
        """Add performance or operational metrics."""
        self.metrics.append(metrics)

    def record_test_result(self, item: Item, report: TestReport) -> None:
        """Record test execution result."""
        self.test_results.append({
            "nodeid": item.nodeid,
            "outcome": report.outcome,
            "duration": getattr(report, "duration", 0.0),
            "markers": [m.name for m in item.iter_markers()],
        })


# Global evidence collector (initialized per session)
_evidence_collector: EvidenceCollector | None = None


def pytest_configure(config: Config) -> None:
    """Initialize evidence collector when pytest starts."""
    global _evidence_collector

    if EvidencePackBuilder is None:
        return

    output_dir = Path(config.rootpath) / "artifacts" / "evidence"
    output_dir.mkdir(parents=True, exist_ok=True)
    _evidence_collector = EvidenceCollector(output_dir)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: Item, call):
    """Capture test results for evidence pack."""
    outcome = yield
    report = outcome.get_result()

    if _evidence_collector and report.when == "call":
        _evidence_collector.record_test_result(item, report)

    return outcome


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Generate evidence pack after all tests complete."""
    global _evidence_collector

    if _evidence_collector is None or EvidencePackBuilder is None:
        return

    # Determine module name from test paths
    module_name = "zeroui"
    test_paths = [str(item.fspath) for item in session.items[:10]]  # Sample first 10
    if any("data-governance-privacy" in p for p in test_paths):
        module_name = "dgp"
    elif any("alerting" in p for p in test_paths):
        module_name = "alerting"
    elif any("budgeting" in p for p in test_paths):
        module_name = "budgeting"
    elif any("deployment" in p for p in test_paths):
        module_name = "deployment"

    # Build evidence pack
    builder = EvidencePackBuilder(output_dir=str(_evidence_collector.output_dir))

    # Add collected evidence
    for receipt in _evidence_collector.receipts:
        builder.add_receipt(receipt)

    for config_snap in _evidence_collector.config_snapshots:
        builder.add_config_snapshot(config_snap["config"], config_snap["name"])

    for metrics in _evidence_collector.metrics:
        builder.add_metrics(metrics)

    # Add test execution summary
    builder.add_metrics({
        "test_execution": {
            "total": len(_evidence_collector.test_results),
            "passed": sum(1 for r in _evidence_collector.test_results if r["outcome"] == "passed"),
            "failed": sum(1 for r in _evidence_collector.test_results if r["outcome"] == "failed"),
            "skipped": sum(1 for r in _evidence_collector.test_results if r["outcome"] == "skipped"),
            "exit_status": exitstatus,
        }
    })

    try:
        evidence_path = builder.build(module_name=module_name, test_suite="pytest_session")
        print(f"\n{'='*60}")
        print(f"✓ Evidence pack generated: {evidence_path}")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"\n⚠ Failed to generate evidence pack: {e}\n")


def get_evidence_collector() -> EvidenceCollector | None:
    """Get the global evidence collector (for use in tests)."""
    return _evidence_collector

