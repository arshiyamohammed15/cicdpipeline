from datetime import datetime, timedelta, timezone

import pytest

from bdr.models import BackupPlan, RetentionPolicy, VerificationPolicy
from bdr.scheduler import BackupScheduler, SchedulerError


def _plan(plan_id: str, frequency: str = "PT15M") -> BackupPlan:
    return BackupPlan(
        plan_id=plan_id,
        name="plan",
        dataset_ids=["ds"],
        plane="product_cloud",
        backup_frequency=frequency,
        target_rpo="PT15M",
        target_rto="PT30M",
        retention=RetentionPolicy(min_versions=1, min_duration="P1D"),
        storage_profiles=["hot"],
        redundancy_profile="tier0",
        encryption_key_ref="kid:test",
        verification=VerificationPolicy(),
    )


def test_scheduler_due_flow():
    scheduler = BackupScheduler()
    now = datetime.now(timezone.utc)
    scheduler.register_plan(_plan("p1"), now)
    due = scheduler.due(now + timedelta(minutes=16))
    assert due == ["p1"]
    scheduler.mark_executed("p1", now + timedelta(minutes=16))
    assert scheduler.due(now + timedelta(minutes=17)) == []
    scheduler.remove_plan("p1")
    assert scheduler.due(now + timedelta(minutes=17)) == []


def test_scheduler_rejects_invalid_plan():
    scheduler = BackupScheduler()
    with pytest.raises(SchedulerError):
        scheduler.register_plan(_plan("p2", frequency="weekly"), datetime.now(timezone.utc))
    scheduler.register_plan(_plan("p3"), datetime.now(timezone.utc))
    scheduler.remove_plan("p3")
    with pytest.raises(SchedulerError):
        scheduler.mark_executed("p3", datetime.now(timezone.utc))
    with pytest.raises(SchedulerError):
        scheduler.mark_executed("unknown", datetime.now(timezone.utc))
    scheduler.register_plan(_plan("p4"), datetime.now(timezone.utc))
    scheduler._entries["p4"]["interval"] = "invalid"  # type: ignore[index]
    with pytest.raises(SchedulerError):
        scheduler.mark_executed("p4", datetime.now(timezone.utc))

