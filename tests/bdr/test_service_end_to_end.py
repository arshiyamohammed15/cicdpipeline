from datetime import datetime, timedelta, timezone

import pytest

from bdr.dr import DRScenarioCatalog
from bdr.models import (
    BackupStatus,
    DRRunbookStep,
    DRScenario,
    DRStrategy,
    IAMContext,
    RestoreMode,
    RestorePoint,
    RestoreRequest,
)
from bdr.policy import PolicyLoadError
from bdr.service import BDRService, BDRServiceError
from bdr.storage import InMemoryBackupStorage


class FailingBackupStorage(InMemoryBackupStorage):
    def create_backup(self, plan, datasets, backup_type):
        raise RuntimeError("snapshot_failed")


class FailingRestoreStorage(InMemoryBackupStorage):
    def restore(self, artifacts, mode, target_env):
        raise RuntimeError("restore_failed")


@pytest.mark.integration
def test_service_backup_and_restore_flow(bdr_service, iam_context, restore_request):
    bdr_service.run_backup(iam_context, "bp_policy_store")
    bdr_service.request_restore(iam_context, restore_request)
    assert bdr_service.metrics.get_counter("bdr_backup_runs", "bp_policy_store:success") == 1
    assert bdr_service.metrics.get_counter("bdr_restore_runs", "success:side_by_side") == 1
    assert bdr_service.receipts.captured[-1].decision_type.value == "restore_completed"
    assert isinstance(bdr_service.logger.entries, list)


@pytest.mark.integration
def test_service_run_scheduled_backups(bdr_service, iam_context):
    now = datetime.now(timezone.utc) + timedelta(minutes=31)
    executed = bdr_service.run_scheduled_backups(iam_context, now=now)
    assert set(executed) == {"bp_policy_store", "bp_observability"}


@pytest.mark.integration
def test_service_dr_scenario_drill_and_failover(bdr_service, iam_context):
    scenario = DRScenario(
        scenario_id="sc_loss_core",
        name="Loss of Core Service",
        trigger="core_db_failure",
        strategy=DRStrategy.BACKUP_AND_RESTORE,
        rpo_target="PT15M",
        rto_target="PT30M",
        runbook=[DRRunbookStep(name="step1", description="failover", automated=True)],
    )
    bdr_service.register_dr_scenario(iam_context, scenario)
    bdr_service.execute_dr_drill(
        iam_context,
        scenario_id="sc_loss_core",
        involved_plans=["bp_policy_store"],
        achieved_rpo="PT10M",
        achieved_rto="PT20M",
    )
    bdr_service.run_failover(iam_context, scenario_id="sc_loss_core", target_env="backup")
    assert bdr_service.metrics.get_counter("bdr_dr_drills", "sc_loss_core:success") == 1
    assert bdr_service.metrics.get_counter("bdr_dr_events", "sc_loss_core:success") == 1
    assert isinstance(bdr_service.stale_plans(), list)


@pytest.mark.integration
def test_service_rejects_policy_with_duplicate_dataset(dataset_definitions, plan_definitions):
    duplicate_plans = plan_definitions + [
        plan_definitions[0] | {"plan_id": "bp_duplicate", "dataset_ids": ["ds_policy_store"]}
    ]
    storage = InMemoryBackupStorage()
    storage.seed_dataset("ds_policy_store", "data")
    with pytest.raises(PolicyLoadError):
        BDRService(dataset_source=dataset_definitions, plan_source=duplicate_plans, storage=storage)


@pytest.mark.integration
def test_service_restore_failure_path(bdr_service, iam_context):
    request = RestoreRequest(
        dataset_ids=["unknown_ds"],
        target_env="staging",
        mode=RestoreMode.IN_PLACE,
        restore_point=RestorePoint(type="latest"),
    )
    with pytest.raises(BDRServiceError):
        bdr_service.request_restore(iam_context, request)


@pytest.mark.integration
def test_service_unknown_plan_raises(bdr_service, iam_context):
    with pytest.raises(BDRServiceError):
        bdr_service.run_backup(iam_context, "unknown_plan")


@pytest.mark.integration
def test_service_require_bundle_guard(bdr_service):
    original = bdr_service._policy_bundle  # type: ignore[attr-defined]
    bdr_service._policy_bundle = None  # type: ignore[attr-defined]
    with pytest.raises(BDRServiceError):
        bdr_service._require_bundle()
    bdr_service._policy_bundle = original  # type: ignore[attr-defined]


@pytest.mark.integration
def test_backup_failure_emits_failure_receipt(dataset_definitions, plan_definitions):
    storage = FailingBackupStorage()
    service = BDRService(dataset_source=dataset_definitions, plan_source=plan_definitions, storage=storage)
    context = IAMContext(actor="svc", roles=["backup:run"], scopes=["backup:run"])
    service.run_backup(context, "bp_policy_store")
    receipt = service.receipts.captured[-1]
    assert receipt.result == BackupStatus.FAILURE


@pytest.mark.integration
def test_restore_failure_logs_and_raises(dataset_definitions, plan_definitions):
    storage = FailingRestoreStorage()
    storage.seed_dataset("ds_policy_store", "data")
    storage.seed_dataset("ds_observability", "data")
    service = BDRService(dataset_source=dataset_definitions, plan_source=plan_definitions, storage=storage)
    context = IAMContext(actor="svc", roles=["backup:run", "restore:execute"], scopes=["backup:run", "restore:execute"])
    service.run_backup(context, "bp_policy_store")
    request = RestoreRequest(
        dataset_ids=["ds_policy_store"],
        target_env="prod",
        mode=RestoreMode.IN_PLACE,
        restore_point=RestorePoint(type="latest"),
    )
    with pytest.raises(BDRServiceError):
        service.request_restore(context, request)

