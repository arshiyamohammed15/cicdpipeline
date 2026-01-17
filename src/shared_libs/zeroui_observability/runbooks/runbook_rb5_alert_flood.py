"""
Runbook RB-5: Alert Flood Control

Per PRD Section 8 (RB-5):
1. Open D15 (False Positive Control Room) and review alert fingerprints and volumes.
2. Apply deduplication and rate limiting for repeated fingerprints.
3. Re-calibrate thresholds using historical performance trends and segmentation to avoid normal fluctuations triggering alerts.

End-of-runbook checks:
- Confirm whether this was a false positive; record evidence.
- Update threshold calibration inputs if needed.
- Document a short post-mortem note if the alert was noisy or misleading.
"""

import logging
from typing import Any, Dict

from .runbook_executor import RunbookExecutor, RunbookStep
from .runbook_utils import DashboardClient

logger = logging.getLogger(__name__)


class RunbookRB5AlertFlood:
    """
    Runbook RB-5: Alert Flood Control.

    Executes steps for controlling alert floods and reducing false positives.
    """

    def __init__(
        self,
        executor: RunbookExecutor,
        dashboard_client: DashboardClient,
    ):
        """
        Initialize RB-5 runbook.

        Args:
            executor: RunbookExecutor instance
            dashboard_client: DashboardClient for accessing D15
        """
        self._executor = executor
        self._dashboard = dashboard_client

    def execute(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute RB-5 runbook.

        Args:
            context: Execution context (tenant_id, alert_fingerprints, etc.)

        Returns:
            Execution result
        """
        # Step 1: Open D15 and review alert fingerprints
        step1 = RunbookStep(
            step_id="rb5_step1",
            step_name="Review Alert Fingerprints",
            action="query_dashboard",
            parameters={
                "dashboard_id": "D15",
                "panel_id": "d15_p1",
                "filters": {
                    "alert_fingerprints": context.get("alert_fingerprints", []),
                },
            },
        )

        # Step 2: Apply deduplication and rate limiting
        step2 = RunbookStep(
            step_id="rb5_step2",
            step_name="Apply Deduplication and Rate Limiting",
            action="apply_noise_control",
            parameters={
                "dedup_window": context.get("dedup_window", "5m"),
                "rate_limit_window": context.get("rate_limit_window", "1h"),
            },
            validation={"expected_status": "success"},
        )

        # Step 3: Re-calibrate thresholds
        step3 = RunbookStep(
            step_id="rb5_step3",
            step_name="Re-calibrate Thresholds",
            action="recalibrate_thresholds",
            parameters={
                "historical_trends": context.get("historical_trends"),
                "segmentation": context.get("segmentation"),
            },
        )

        # Execute runbook
        execution = self._executor.execute(
            runbook_id="RB-5",
            steps=[step1, step2, step3],
            context=context,
        )

        # End-of-runbook checks
        result = {
            "execution_id": execution.execution_id,
            "status": execution.status,
            "false_positive": execution.false_positive,
            "threshold_updates": execution.threshold_updates,
            "post_mortem": execution.post_mortem,
        }

        return result


def create_rb5_runbook(
    executor: RunbookExecutor,
    dashboard_client: DashboardClient,
) -> RunbookRB5AlertFlood:
    """
    Create RB-5 runbook instance.

    Args:
        executor: RunbookExecutor instance
        dashboard_client: DashboardClient instance

    Returns:
        RunbookRB5AlertFlood instance
    """
    return RunbookRB5AlertFlood(executor, dashboard_client)
