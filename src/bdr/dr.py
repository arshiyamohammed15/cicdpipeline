"""Disaster recovery scenario management."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Sequence

from .catalog import BackupCatalog
from .models import (
    BackupStatus,
    DecisionReceipt,
    DecisionType,
    DRScenario,
    DrillResult,
)
from .observability import MetricsRegistry, StructuredLogger
from .receipts import DecisionReceiptEmitter


class DRError(RuntimeError):
    """Raised when DR operations fail."""


class DRScenarioCatalog:
    """Stores DR scenarios and provides lookup utilities."""

    def __init__(self) -> None:
        self._scenarios: Dict[str, DRScenario] = {}

    def register(self, scenario: DRScenario) -> None:
        if scenario.scenario_id in self._scenarios:
            msg = f"Scenario {scenario.scenario_id} already registered"
            raise DRError(msg)
        self._scenarios[scenario.scenario_id] = scenario

    def get(self, scenario_id: str) -> DRScenario:
        if scenario_id not in self._scenarios:
            msg = f"Scenario {scenario_id} not found"
            raise DRError(msg)
        return self._scenarios[scenario_id]

    def list(self) -> List[DRScenario]:
        return list(self._scenarios.values())


class FailoverOrchestrator:
    """Coordinates failover/failback flows."""

    def __init__(
        self,
        scenarios: DRScenarioCatalog,
        metrics: MetricsRegistry,
        logger: StructuredLogger,
        receipts: DecisionReceiptEmitter,
    ) -> None:
        self._scenarios = scenarios
        self._metrics = metrics
        self._logger = logger
        self._receipts = receipts

    def execute(
        self,
        scenario_id: str,
        initiator: str,
        target_env: str,
        outcome: BackupStatus = BackupStatus.SUCCESS,
    ) -> None:
        scenario = self._require_scenario(scenario_id)
        self._logger.info(
            "dr_failover",
            scenario_id=scenario_id,
            initiator=initiator,
            target_env=target_env,
            outcome=outcome.value,
        )
        self._metrics.increment("bdr_dr_events", f"{scenario_id}:{outcome.value}")
        self._receipts.emit(
            DecisionReceipt(
                decision_type=DecisionType.DR_EVENT_COMPLETED,
                operation_id=f"dr_{scenario_id}_{datetime.now(timezone.utc).isoformat()}",
                scenario_id=scenario_id,
                dataset_ids=[],
                result=outcome,
                details={"target_env": target_env, "initiator": initiator},
            )
        )

    def _require_scenario(self, scenario_id: str) -> DRScenario:
        return self._scenarios.get(scenario_id)


class DrillRunner:
    """Executes DR drills and updates plan maintenance metadata."""

    def __init__(
        self,
        catalog: BackupCatalog,
        metrics: MetricsRegistry,
        logger: StructuredLogger,
        receipts: DecisionReceiptEmitter,
        stale_after: timedelta,
    ) -> None:
        self._catalog = catalog
        self._metrics = metrics
        self._logger = logger
        self._receipts = receipts
        self._stale_after = stale_after

    def run_drill(
        self,
        scenario: DRScenario,
        involved_plans: Iterable[str],
        achieved_rpo: str,
        achieved_rto: str,
        status: BackupStatus = BackupStatus.SUCCESS,
    ) -> DrillResult:
        started = datetime.now(timezone.utc)
        finished = started + timedelta(minutes=5)
        result = DrillResult(
            scenario_id=scenario.scenario_id,
            started_at=started,
            finished_at=finished,
            achieved_rpo=achieved_rpo,
            achieved_rto=achieved_rto,
            status=status,
            issues=[],
        )
        for plan_id in involved_plans:
            self._catalog.mark_plan_test(plan_id, result, self._stale_after)
        self._metrics.increment("bdr_dr_drills", f"{scenario.scenario_id}:{status.value}")
        self._logger.info(
            "dr_drill",
            scenario_id=scenario.scenario_id,
            status=status.value,
            achieved_rpo=achieved_rpo,
            achieved_rto=achieved_rto,
        )
        self._receipts.emit(
            DecisionReceipt(
                decision_type=DecisionType.DR_EVENT_COMPLETED,
                operation_id=f"drill_{scenario.scenario_id}_{started.isoformat()}",
                scenario_id=scenario.scenario_id,
                result=status,
                details={
                    "achieved_rpo": achieved_rpo,
                    "achieved_rto": achieved_rto,
                    "runbook_steps": len(scenario.runbook),
                },
            )
        )
        return result

    def stale_plans(self) -> List[str]:
        return self._catalog.stale_plans()

