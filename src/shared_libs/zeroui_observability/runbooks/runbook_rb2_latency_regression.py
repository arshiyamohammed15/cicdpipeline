"""
Runbook RB-2: Latency / Performance Regression

Per PRD Section 8 (RB-2):
1. Open D12 (Performance Under Load) and confirm latency increase is not caused by normal load fluctuations.
2. Check caching indicators for repeated queries and validate cache behaviour.
3. Check async indicators for non-critical tasks to ensure they are not blocking the main workflow.
4. Check RAG latency breakdown to identify whether retrieval is the bottleneck.
5. Validate improvements under load after changes; adjust resource allocation based on usage patterns.

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


class RunbookRB2LatencyRegression:
    """
    Runbook RB-2: Latency / Performance Regression.

    Executes steps for analyzing and responding to latency regressions.
    """

    def __init__(
        self,
        executor: RunbookExecutor,
        dashboard_client: DashboardClient,
    ):
        """
        Initialize RB-2 runbook.

        Args:
            executor: RunbookExecutor instance
            dashboard_client: DashboardClient for accessing D12
        """
        self._executor = executor
        self._dashboard = dashboard_client

    def execute(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute RB-2 runbook.

        Args:
            context: Execution context (tenant_id, component, channel, alert_id, etc.)

        Returns:
            Execution result
        """
        # Step 1: Open D12 and confirm latency increase
        step1 = RunbookStep(
            step_id="rb2_step1",
            step_name="Confirm Latency Increase",
            action="query_dashboard",
            parameters={
                "dashboard_id": "D12",
                "panel_id": "d12_p1",
                "filters": {
                    "component": context.get("component"),
                    "channel": context.get("channel"),
                },
            },
        )

        # Step 2: Check caching indicators
        step2 = RunbookStep(
            step_id="rb2_step2",
            step_name="Check Cache Indicators",
            action="check_cache_indicators",
            parameters={
                "dashboard_id": "D12",
                "panel_id": "d12_p2",  # Cache hit rate panel
            },
        )

        # Step 3: Check async indicators
        step3 = RunbookStep(
            step_id="rb2_step3",
            step_name="Check Async Indicators",
            action="check_async_indicators",
            parameters={
                "dashboard_id": "D12",
                "panel_id": "d12_p3",  # Async path indicators
            },
        )

        # Step 4: Check RAG latency breakdown
        step4 = RunbookStep(
            step_id="rb2_step4",
            step_name="Check RAG Latency Breakdown",
            action="check_rag_latency",
            parameters={
                "dashboard_id": "D12",
                "panel_id": "d12_p4",  # RAG latency breakdown
            },
        )

        # Step 5: Validate improvements and adjust resource allocation
        step5 = RunbookStep(
            step_id="rb2_step5",
            step_name="Validate Improvements",
            action="validate_improvements",
            parameters={
                "resource_allocation": context.get("resource_allocation"),
            },
        )

        # Execute runbook
        execution = self._executor.execute(
            runbook_id="RB-2",
            steps=[step1, step2, step3, step4, step5],
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


def create_rb2_runbook(
    executor: RunbookExecutor,
    dashboard_client: DashboardClient,
) -> RunbookRB2LatencyRegression:
    """
    Create RB-2 runbook instance.

    Args:
        executor: RunbookExecutor instance
        dashboard_client: DashboardClient instance

    Returns:
        RunbookRB2LatencyRegression instance
    """
    return RunbookRB2LatencyRegression(executor, dashboard_client)
