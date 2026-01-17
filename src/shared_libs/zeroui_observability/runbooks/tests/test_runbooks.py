"""
Tests for runbooks.

OBS-16: Runbook execution tests.
"""

import unittest
from unittest.mock import MagicMock

from ..oncall_playbook import OnCallPlaybook, create_oncall_playbook
from ..runbook_executor import RunbookExecutor
from ..runbook_utils import DashboardClient, ReplayBundleClient, TraceClient


class TestRunbooks(unittest.TestCase):
    """Test runbook execution."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor = RunbookExecutor()
        self.dashboard = DashboardClient()
        self.trace = TraceClient()
        self.replay = ReplayBundleClient()

    def test_oncall_playbook_routing(self):
        """Test on-call playbook alert routing."""
        playbook = create_oncall_playbook(
            self.executor,
            self.dashboard,
            self.trace,
            self.replay,
        )

        # Test routing A1 -> RB-1
        context = {"tenant_id": "tenant_001", "component": "test", "channel": "backend"}
        result = playbook.route_alert("A1", context)
        self.assertIsNotNone(result)
        self.assertEqual(result.get("status"), "completed")

        # Test routing A2 -> RB-2
        result = playbook.route_alert("A2", context)
        self.assertIsNotNone(result)

        # Test routing A7 -> RB-5
        result = playbook.route_alert("A7", context)
        self.assertIsNotNone(result)

    def test_oncall_playbook_unknown_alert(self):
        """Test on-call playbook with unknown alert."""
        playbook = create_oncall_playbook(
            self.executor,
            self.dashboard,
            self.trace,
            self.replay,
        )

        with self.assertRaises(ValueError):
            playbook.route_alert("A99", {})


if __name__ == "__main__":
    unittest.main()
