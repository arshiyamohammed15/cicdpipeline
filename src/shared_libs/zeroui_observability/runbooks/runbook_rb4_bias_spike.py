"""
Runbook RB-4: Bias Spike / Bias Detection Review

Per PRD Section 8 (RB-4):
1. Open D6 (Bias Monitoring) and confirm the bias signal is supported by more than one detection method.
2. Run counterfactual and adversarial prompt tests for the affected scenarios.
3. Route borderline or low-confidence cases to human validation before any corrective action.
4. Record outcomes for continuous calibration of bias detection.

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


class RunbookRB4BiasSpike:
    """
    Runbook RB-4: Bias Spike / Bias Detection Review.

    Executes steps for analyzing and responding to bias detection signals.
    """

    def __init__(
        self,
        executor: RunbookExecutor,
        dashboard_client: DashboardClient,
    ):
        """
        Initialize RB-4 runbook.

        Args:
            executor: RunbookExecutor instance
            dashboard_client: DashboardClient for accessing D6
        """
        self._executor = executor
        self._dashboard = dashboard_client

    def execute(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute RB-4 runbook.

        Args:
            context: Execution context (tenant_id, component, channel, bias_category, etc.)

        Returns:
            Execution result
        """
        # Step 1: Open D6 and confirm bias signal
        step1 = RunbookStep(
            step_id="rb4_step1",
            step_name="Confirm Bias Signal",
            action="query_dashboard",
            parameters={
                "dashboard_id": "D6",
                "panel_id": "d6_p1",
                "filters": {
                    "component": context.get("component"),
                    "bias_category": context.get("bias_category"),
                },
            },
        )

        # Step 2: Run counterfactual/adversarial tests
        step2 = RunbookStep(
            step_id="rb4_step2",
            step_name="Run Counterfactual Tests",
            action="run_bias_tests",
            parameters={
                "test_type": "counterfactual",
                "scenarios": context.get("scenarios", []),
            },
        )

        # Step 3: Route to human validation if needed
        step3 = RunbookStep(
            step_id="rb4_step3",
            step_name="Route to Human Validation",
            action="route_human_validation",
            parameters={
                "confidence_threshold": context.get("confidence_threshold", 0.8),
                "bias_signals": context.get("bias_signals", []),
            },
            validation={"expected_status": "success"},
        )

        # Step 4: Record outcomes for calibration
        step4 = RunbookStep(
            step_id="rb4_step4",
            step_name="Record Calibration Outcomes",
            action="record_calibration",
            parameters={
                "bias_detection_updates": context.get("bias_detection_updates"),
            },
        )

        # Execute runbook
        execution = self._executor.execute(
            runbook_id="RB-4",
            steps=[step1, step2, step3, step4],
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


def create_rb4_runbook(
    executor: RunbookExecutor,
    dashboard_client: DashboardClient,
) -> RunbookRB4BiasSpike:
    """
    Create RB-4 runbook instance.

    Args:
        executor: RunbookExecutor instance
        dashboard_client: DashboardClient instance

    Returns:
        RunbookRB4BiasSpike instance
    """
    return RunbookRB4BiasSpike(executor, dashboard_client)
