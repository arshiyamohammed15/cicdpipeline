"""Facade that exposes the BDR backend capabilities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Sequence

from .catalog import BackupCatalog
from .dr import DRScenario, DRScenarioCatalog, DrillRunner, FailoverOrchestrator
from .engine import BackupExecutor, EngineError, RestoreExecutor
from .models import (
    BackupPlan,
    BackupType,
    Dataset,
    DRStrategy,
    IAMContext,
    RestoreRequest,
)
from .observability import MetricsRegistry, StructuredLogger
from .policy import PolicyBundle, PolicyLoader, PolicyLoadError
from .receipts import DecisionReceiptEmitter
from .scheduler import BackupScheduler
from .security import IAMGuard, KeyResolver, PermissionDeniedError
from .storage import BackupStorageBackend
from .verification import ChecksumComputer


class BDRServiceError(RuntimeError):
    """Raised for unrecoverable service errors."""


class BDRService:
    """High-level API for the Backup & Disaster Recovery module."""

    def __init__(
        self,
        dataset_source,
        plan_source,
        storage: BackupStorageBackend,
        *,
        iam_guard: IAMGuard | None = None,
        key_resolver: KeyResolver | None = None,
        drill_stale_after: timedelta | None = None,
    ) -> None:
        self._policy_loader = PolicyLoader(dataset_source=dataset_source, plan_source=plan_source)
        self._storage = storage
        self._catalog = BackupCatalog()
        self._metrics = MetricsRegistry()
        self._logger = StructuredLogger()
        self._receipts = DecisionReceiptEmitter()
        self._scheduler = BackupScheduler()
        self._iam = iam_guard or IAMGuard()
        self._key_resolver = key_resolver or KeyResolver(allowed_prefixes=("kid:",))
        self._checksum = ChecksumComputer()
        self._policy_bundle: PolicyBundle | None = None
        self._dataset_index: Dict[str, Dataset] = {}
        self._plan_index: Dict[str, BackupPlan] = {}
        self._dataset_plan_index: Dict[str, str] = {}
        self._backup_executor = BackupExecutor(
            catalog=self._catalog,
            storage=self._storage,
            metrics=self._metrics,
            logger=self._logger,
            receipts=self._receipts,
            checksum=self._checksum,
        )
        self._restore_executor = RestoreExecutor(
            catalog=self._catalog,
            storage=self._storage,
            metrics=self._metrics,
            logger=self._logger,
            receipts=self._receipts,
            dataset_plan_index=self._dataset_plan_index,
        )
        self._dr_catalog = DRScenarioCatalog()
        stale_after = drill_stale_after or timedelta(days=90)
        self._dr_runner = DrillRunner(
            catalog=self._catalog,
            metrics=self._metrics,
            logger=self._logger,
            receipts=self._receipts,
            stale_after=stale_after,
        )
        self._failover = FailoverOrchestrator(
            scenarios=self._dr_catalog,
            metrics=self._metrics,
            logger=self._logger,
            receipts=self._receipts,
        )
        self.reload_policy()

    @property
    def metrics(self) -> MetricsRegistry:
        return self._metrics

    @property
    def logger(self) -> StructuredLogger:
        return self._logger

    @property
    def receipts(self) -> DecisionReceiptEmitter:
        return self._receipts

    def reload_policy(self) -> None:
        bundle = self._policy_loader.load()
        self._policy_bundle = bundle
        self._dataset_index = {dataset.dataset_id: dataset for dataset in bundle.datasets}
        self._plan_index = {plan.plan_id: plan for plan in bundle.plans}
        self._dataset_plan_index.clear()
        self._scheduler = BackupScheduler()
        for plan in bundle.plans:
            for dataset_id in plan.dataset_ids:
                if dataset_id in self._dataset_plan_index:
                    raise PolicyLoadError(f"Dataset {dataset_id} assigned to multiple plans")
                self._dataset_plan_index[dataset_id] = plan.plan_id
            self._key_resolver.validate(plan.encryption_key_ref)
            self._scheduler.register_plan(plan, now=datetime.now(timezone.utc))

    def run_scheduled_backups(self, context: IAMContext, now: datetime | None = None) -> List[str]:
        now = now or datetime.now(timezone.utc)
        self._iam.require(context, "backup:run")
        plan_ids = self._scheduler.due(now)
        executed: List[str] = []
        for plan_id in plan_ids:
            self._execute_plan(plan_id)
            self._scheduler.mark_executed(plan_id, now)
            executed.append(plan_id)
        return executed

    def run_backup(self, context: IAMContext, plan_id: str, backup_type: BackupType = BackupType.FULL) -> None:
        self._iam.require(context, "backup:run")
        self._execute_plan(plan_id, backup_type=backup_type)

    def request_restore(self, context: IAMContext, request: RestoreRequest) -> None:
        self._iam.require(context, "restore:execute")
        bundle = self._require_bundle()
        try:
            self._restore_executor.restore(
                request=request,
                policy_snapshot_hash=bundle.snapshot_hash,
                policy_versions=[bundle.snapshot_hash],
            )
        except EngineError as exc:
            raise BDRServiceError(str(exc)) from exc

    def register_dr_scenario(self, context: IAMContext, scenario: DRScenario) -> None:
        self._iam.require(context, "dr:admin")
        self._dr_catalog.register(scenario)

    def execute_dr_drill(
        self,
        context: IAMContext,
        scenario_id: str,
        involved_plans: Iterable[str],
        achieved_rpo: str,
        achieved_rto: str,
    ) -> None:
        self._iam.require(context, "dr:execute")
        scenario = self._dr_catalog.get(scenario_id)
        self._dr_runner.run_drill(
            scenario=scenario,
            involved_plans=list(involved_plans),
            achieved_rpo=achieved_rpo,
            achieved_rto=achieved_rto,
        )

    def run_failover(self, context: IAMContext, scenario_id: str, target_env: str) -> None:
        self._iam.require(context, "dr:execute")
        self._failover.execute(
            scenario_id=scenario_id,
            initiator=context.actor,
            target_env=target_env,
        )

    def stale_plans(self) -> List[str]:
        return self._dr_runner.stale_plans()

    def _execute_plan(self, plan_id: str, backup_type: BackupType = BackupType.FULL) -> None:
        bundle = self._require_bundle()
        plan = self._plan_index.get(plan_id)
        if plan is None:
            raise BDRServiceError(f"Unknown plan {plan_id}")
        datasets = [self._dataset_index[dataset_id] for dataset_id in plan.dataset_ids]
        self._backup_executor.execute(
            plan=plan,
            datasets=datasets,
            policy_snapshot_hash=bundle.snapshot_hash,
            policy_versions=[bundle.snapshot_hash],
            backup_type=backup_type,
        )

    def _require_bundle(self) -> PolicyBundle:
        if self._policy_bundle is None:
            raise BDRServiceError("Policy bundle not loaded")
        return self._policy_bundle

