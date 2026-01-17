"""
Runbook Executor for ZeroUI Observability Layer.

OBS-16: Executes runbook steps with validation checks and rollback steps.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from ...cccs.receipts.service import ReceiptService, ReceiptConfig, OfflineCourier
    from ...cccs.wal import WALQueue
    CCCS_AVAILABLE = True
except ImportError:
    CCCS_AVAILABLE = False
    ReceiptService = None  # type: ignore
    ReceiptConfig = None  # type: ignore
    OfflineCourier = None  # type: ignore
    WALQueue = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class RunbookStep:
    """Runbook step definition."""

    step_id: str
    step_name: str
    action: str
    parameters: Dict[str, Any]
    validation: Optional[Dict[str, Any]] = None
    rollback: Optional[Dict[str, Any]] = None


@dataclass
class RunbookExecution:
    """Runbook execution record."""

    execution_id: str
    runbook_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, rolled_back
    steps_completed: List[str] = None
    steps_failed: List[str] = None
    false_positive: Optional[bool] = None
    threshold_updates: Dict[str, Any] = None
    post_mortem: Optional[str] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.steps_completed is None:
            self.steps_completed = []
        if self.steps_failed is None:
            self.steps_failed = []
        if self.threshold_updates is None:
            self.threshold_updates = {}


class RunbookExecutor:
    """
    Executes runbook steps with validation and rollback support.

    Per OBS-16 requirements:
    - Executes runbook steps sequentially
    - Validates each step before proceeding
    - Supports rollback on failure
    - Generates receipts for all actions
    - Stores execution logs in Evidence Plane
    """

    def __init__(
        self,
        receipt_service: Optional[ReceiptService] = None,
        storage_path: Optional[str] = None,
    ):
        """
        Initialize runbook executor.

        Args:
            receipt_service: ReceiptService for generating receipts
            storage_path: Path for storing execution logs
        """
        self._receipt_service = receipt_service
        self._storage_path = storage_path
        self._executions: Dict[str, RunbookExecution] = {}

    def execute(
        self,
        runbook_id: str,
        steps: List[RunbookStep],
        context: Dict[str, Any],
    ) -> RunbookExecution:
        """
        Execute runbook steps.

        Args:
            runbook_id: Runbook identifier (RB-1, RB-2, etc.)
            steps: List of runbook steps
            context: Execution context (tenant_id, component, channel, etc.)

        Returns:
            RunbookExecution record
        """
        import uuid
        execution_id = f"exec_{uuid.uuid4().hex[:16]}"

        execution = RunbookExecution(
            execution_id=execution_id,
            runbook_id=runbook_id,
            started_at=datetime.now(timezone.utc),
        )

        self._executions[execution_id] = execution

        try:
            # Execute steps sequentially
            for step in steps:
                try:
                    # Execute step
                    result = self._execute_step(step, context, execution)

                    # Validate step result
                    if step.validation:
                        if not self._validate_step(step, result):
                            execution.steps_failed.append(step.step_id)
                            logger.error(f"Step {step.step_id} validation failed")
                            # Rollback if configured
                            if step.rollback:
                                self._rollback_step(step, context, execution)
                            break

                    execution.steps_completed.append(step.step_id)
                    logger.info(f"Step {step.step_id} completed successfully")

                except Exception as e:
                    execution.steps_failed.append(step.step_id)
                    logger.error(f"Step {step.step_id} failed: {e}")
                    # Rollback if configured
                    if step.rollback:
                        self._rollback_step(step, context, execution)
                    break

            # Mark execution as completed
            execution.completed_at = datetime.now(timezone.utc)
            if execution.steps_failed:
                execution.status = "failed"
            else:
                execution.status = "completed"

        except Exception as e:
            execution.status = "failed"
            execution.completed_at = datetime.now(timezone.utc)
            logger.error(f"Runbook execution failed: {e}")

        # Store execution log
        self._store_execution_log(execution, context)

        return execution

    def _execute_step(
        self,
        step: RunbookStep,
        context: Dict[str, Any],
        execution: RunbookExecution,
    ) -> Dict[str, Any]:
        """
        Execute a single runbook step.

        Args:
            step: Runbook step
            context: Execution context
            execution: Execution record

        Returns:
            Step execution result
        """
        # Generate receipt for step execution
        if self._receipt_service and CCCS_AVAILABLE:
            try:
                receipt = self._receipt_service.emit_receipt(
                    gate_id=f"runbook_{execution.runbook_id}",
                    decision="pass",
                    decision_rationale=f"Executing runbook step {step.step_id}: {step.step_name}",
                    inputs={
                        "step_id": step.step_id,
                        "step_name": step.step_name,
                        "action": step.action,
                        "parameters": step.parameters,
                    },
                    actor_repo_id=context.get("tenant_id", "unknown"),
                )
                logger.debug(f"Generated receipt for step {step.step_id}: {receipt.get('receipt_id')}")
            except Exception as e:
                logger.warning(f"Failed to generate receipt for step {step.step_id}: {e}")

        # Execute step action (placeholder - will be implemented by specific runbooks)
        logger.info(f"Executing step {step.step_id}: {step.action}")
        return {"status": "success", "step_id": step.step_id}

    def _validate_step(
        self,
        step: RunbookStep,
        result: Dict[str, Any],
    ) -> bool:
        """
        Validate step execution result.

        Args:
            step: Runbook step
            result: Step execution result

        Returns:
            True if validation passes, False otherwise
        """
        if not step.validation:
            return True

        # Check validation criteria
        expected_status = step.validation.get("expected_status")
        if expected_status and result.get("status") != expected_status:
            return False

        return True

    def _rollback_step(
        self,
        step: RunbookStep,
        context: Dict[str, Any],
        execution: RunbookExecution,
    ) -> None:
        """
        Rollback a failed step.

        Args:
            step: Runbook step
            context: Execution context
            execution: Execution record
        """
        if not step.rollback:
            return

        logger.info(f"Rolling back step {step.step_id}")
        # Execute rollback action (placeholder)
        # In production, would execute step.rollback["action"] with step.rollback["parameters"]

    def _store_execution_log(
        self,
        execution: RunbookExecution,
        context: Dict[str, Any],
    ) -> None:
        """
        Store runbook execution log in Evidence Plane.

        Args:
            execution: Execution record
            context: Execution context
        """
        if not self._storage_path:
            return

        import json
        from pathlib import Path

        # Build storage path per folder-business-rules.md
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        tenant_id = context.get("tenant_id", "unknown")
        region = context.get("region", "")

        region_part = f"{region}/" if region else ""
        storage_path = (
            Path(self._storage_path)
            / "tenant"
            / tenant_id
            / region_part
            / "evidence"
            / "data"
            / "runbook-executions"
            / f"dt={date_str}"
            / f"{execution.execution_id}.jsonl"
        )

        # Create parent directories
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Build log entry
        log_entry = {
            "execution_id": execution.execution_id,
            "runbook_id": execution.runbook_id,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "status": execution.status,
            "steps_completed": execution.steps_completed,
            "steps_failed": execution.steps_failed,
            "false_positive": execution.false_positive,
            "threshold_updates": execution.threshold_updates,
            "post_mortem": execution.post_mortem,
            "context": context,
        }

        # Write to JSONL file (append-only)
        try:
            with open(storage_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, sort_keys=True) + "\n")
            logger.info(f"Stored runbook execution log at {storage_path}")
        except IOError as e:
            logger.error(f"Failed to store execution log: {e}")

    def get_execution(self, execution_id: str) -> Optional[RunbookExecution]:
        """
        Get execution record by ID.

        Args:
            execution_id: Execution ID

        Returns:
            RunbookExecution or None if not found
        """
        return self._executions.get(execution_id)
