"""
Runbook RB-3: Retrieval Quality Drop

Per PRD Section 8 (RB-3):
1. Open D9 (Retrieval Evaluation) and compare with-retrieval vs without-retrieval benchmark results.
2. Confirm whether irrelevant information is being added, or timeliness is degraded.
3. Adjust relevance and timeliness thresholds (configuration) as required after calibration.

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


class RunbookRB3RetrievalQuality:
    """
    Runbook RB-3: Retrieval Quality Drop.

    Executes steps for analyzing and responding to retrieval quality issues.
    """

    def __init__(
        self,
        executor: RunbookExecutor,
        dashboard_client: DashboardClient,
    ):
        """
        Initialize RB-3 runbook.

        Args:
            executor: RunbookExecutor instance
            dashboard_client: DashboardClient for accessing D9
        """
        self._executor = executor
        self._dashboard = dashboard_client

    def execute(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute RB-3 runbook.

        Args:
            context: Execution context (tenant_id, component, channel, corpus_id, etc.)

        Returns:
            Execution result
        """
        # Step 1: Open D9 and compare benchmarks
        step1 = RunbookStep(
            step_id="rb3_step1",
            step_name="Compare Retrieval Benchmarks",
            action="query_dashboard",
            parameters={
                "dashboard_id": "D9",
                "panel_id": "d9_p1",
                "filters": {
                    "corpus_id": context.get("corpus_id"),
                    "component": context.get("component"),
                },
            },
        )

        # Step 2: Confirm relevance/timeliness issues
        step2 = RunbookStep(
            step_id="rb3_step2",
            step_name="Confirm Relevance/Timeliness Issues",
            action="check_retrieval_compliance",
            parameters={
                "relevance_threshold": context.get("relevance_threshold"),
                "timeliness_threshold": context.get("timeliness_threshold"),
            },
        )

        # Step 3: Adjust thresholds after calibration
        step3 = RunbookStep(
            step_id="rb3_step3",
            step_name="Adjust Thresholds",
            action="update_thresholds",
            parameters={
                "relevance_threshold": context.get("new_relevance_threshold"),
                "timeliness_threshold": context.get("new_timeliness_threshold"),
            },
            validation={"expected_status": "success"},
        )

        # Execute runbook
        execution = self._executor.execute(
            runbook_id="RB-3",
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


def create_rb3_runbook(
    executor: RunbookExecutor,
    dashboard_client: DashboardClient,
) -> RunbookRB3RetrievalQuality:
    """
    Create RB-3 runbook instance.

    Args:
        executor: RunbookExecutor instance
        dashboard_client: DashboardClient instance

    Returns:
        RunbookRB3RetrievalQuality instance
    """
    return RunbookRB3RetrievalQuality(executor, dashboard_client)
