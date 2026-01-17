"""
On-Call Playbook for ZeroUI Observability Layer.

OBS-16: Orchestrates runbook execution based on alert type and severity.
Routes alerts to appropriate runbooks (RB-1 through RB-5).
"""

import logging
from typing import Any, Dict, Optional

from .runbook_executor import RunbookExecutor
from .runbook_rb1_error_spike import RunbookRB1ErrorSpike, create_rb1_runbook
from .runbook_rb2_latency_regression import RunbookRB2LatencyRegression, create_rb2_runbook
from .runbook_rb3_retrieval_quality import RunbookRB3RetrievalQuality, create_rb3_runbook
from .runbook_rb4_bias_spike import RunbookRB4BiasSpike, create_rb4_runbook
from .runbook_rb5_alert_flood import RunbookRB5AlertFlood, create_rb5_runbook
from .runbook_utils import DashboardClient, ReplayBundleClient, TraceClient

logger = logging.getLogger(__name__)


class OnCallPlaybook:
    """
    On-Call Playbook orchestrator.

    Routes alerts to appropriate runbooks based on alert type and severity.
    Per OBS-16 requirements:
    - Routes alerts to RB-1 through RB-5 based on alert type
    - Executes runbooks with proper context
    - Tracks execution results
    """

    # Alert ID to Runbook mapping (from PRD Section 7.3)
    ALERT_TO_RUNBOOK = {
        "A1": "RB-1",  # Decision Success SLO Burn -> RB-1
        "A2": "RB-2",  # Latency Regression -> RB-2
        "A3": "RB-1",  # Error Capture Coverage Drop -> RB-1
        "A4": "RB-3",  # Retrieval Timeliness/Relevance Non-Compliance -> RB-3
        "A5": "RB-1",  # Evaluation Quality Drift -> RB-1 (or RB-4)
        "A6": "RB-4",  # Bias Signal Spike -> RB-4
        "A7": "RB-5",  # Alert Flood Guard -> RB-5
    }

    def __init__(
        self,
        executor: RunbookExecutor,
        dashboard_client: DashboardClient,
        trace_client: TraceClient,
        replay_client: ReplayBundleClient,
    ):
        """
        Initialize on-call playbook.

        Args:
            executor: RunbookExecutor instance
            dashboard_client: DashboardClient instance
            trace_client: TraceClient instance
            replay_client: ReplayBundleClient instance
        """
        self._executor = executor
        self._dashboard = dashboard_client
        self._trace = trace_client
        self._replay = replay_client

        # Initialize runbooks
        self._rb1 = create_rb1_runbook(executor, dashboard_client, trace_client, replay_client)
        self._rb2 = create_rb2_runbook(executor, dashboard_client)
        self._rb3 = create_rb3_runbook(executor, dashboard_client)
        self._rb4 = create_rb4_runbook(executor, dashboard_client)
        self._rb5 = create_rb5_runbook(executor, dashboard_client)

    def route_alert(
        self,
        alert_id: str,
        alert_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Route alert to appropriate runbook.

        Args:
            alert_id: Alert ID (A1-A7)
            alert_context: Alert context (tenant_id, component, channel, trace_id, etc.)

        Returns:
            Runbook execution result

        Raises:
            ValueError: If alert_id is not recognized
        """
        # Map alert to runbook
        runbook_id = self.ALERT_TO_RUNBOOK.get(alert_id)
        if not runbook_id:
            raise ValueError(f"Unknown alert_id: {alert_id}")

        logger.info(f"Routing alert {alert_id} to {runbook_id}")

        # Execute appropriate runbook
        if runbook_id == "RB-1":
            return self._rb1.execute(alert_context)
        elif runbook_id == "RB-2":
            return self._rb2.execute(alert_context)
        elif runbook_id == "RB-3":
            return self._rb3.execute(alert_context)
        elif runbook_id == "RB-4":
            return self._rb4.execute(alert_context)
        elif runbook_id == "RB-5":
            return self._rb5.execute(alert_context)
        else:
            raise ValueError(f"Unknown runbook_id: {runbook_id}")

    def execute_runbook(
        self,
        runbook_id: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute runbook directly by ID.

        Args:
            runbook_id: Runbook ID (RB-1 through RB-5)
            context: Execution context

        Returns:
            Runbook execution result

        Raises:
            ValueError: If runbook_id is not recognized
        """
        if runbook_id == "RB-1":
            return self._rb1.execute(context)
        elif runbook_id == "RB-2":
            return self._rb2.execute(context)
        elif runbook_id == "RB-3":
            return self._rb3.execute(context)
        elif runbook_id == "RB-4":
            return self._rb4.execute(context)
        elif runbook_id == "RB-5":
            return self._rb5.execute(context)
        else:
            raise ValueError(f"Unknown runbook_id: {runbook_id}")


def create_oncall_playbook(
    executor: RunbookExecutor,
    dashboard_client: DashboardClient,
    trace_client: TraceClient,
    replay_client: ReplayBundleClient,
) -> OnCallPlaybook:
    """
    Create on-call playbook instance.

    Args:
        executor: RunbookExecutor instance
        dashboard_client: DashboardClient instance
        trace_client: TraceClient instance
        replay_client: ReplayBundleClient instance

    Returns:
        OnCallPlaybook instance
    """
    return OnCallPlaybook(executor, dashboard_client, trace_client, replay_client)
