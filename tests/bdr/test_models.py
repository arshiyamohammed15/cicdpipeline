import pytest

from datetime import datetime, timezone

import pytest

from bdr.models import (
    ApprovalDecision,
    ApprovalRecord,
    BackupEligibility,
    BackupPlan,
    BackupRun,
    BackupStatus,
    BackupType,
    Dataset,
    RetentionPolicy,
    RestorePoint,
    VerificationPolicy,
    duration_to_timedelta,
    ensure_unique_ids,
    validate_iso_duration,
    window_from_backups,
)


def test_validate_iso_duration_accepts_valid_values():
    assert validate_iso_duration("PT15M") == "PT15M"
    assert validate_iso_duration("P1DT2H") == "P1DT2H"


def test_validate_iso_duration_rejects_invalid_values():
    with pytest.raises(ValueError):
        validate_iso_duration("")
    with pytest.raises(ValueError):
        validate_iso_duration("15M")


def test_dataset_requires_rationale_for_exclusion():
    with pytest.raises(ValueError):
        Dataset(
            dataset_id="ds_x",
            name="Excluded",
            plane="edge",
            store_type="jsonl",
            criticality="tier2",
            data_classification="public",
            rpo_target_ref="PT1H",
            rto_target_ref="PT2H",
            eligibility=BackupEligibility.EXCLUDED,
        )


def test_restore_point_validation():
    with pytest.raises(ValueError):
        RestorePoint(type="latest_before")
    with pytest.raises(ValueError):
        RestorePoint(type="backup_id")
    assert RestorePoint(type="latest").type == "latest"


def test_duration_to_timedelta_parses_values():
    assert duration_to_timedelta("PT1H") == duration_to_timedelta("PT60M")
    with pytest.raises(ValueError):
        duration_to_timedelta("invalid")


def test_dataset_reconstructed_requires_sources():
    with pytest.raises(ValueError):
        Dataset(
            dataset_id="ds_y",
            name="Derived",
            plane="edge",
            store_type="jsonl",
            criticality="tier2",
            data_classification="public",
            rpo_target_ref="PT1H",
            rto_target_ref="PT2H",
            eligibility=BackupEligibility.RECONSTRUCTED,
        )


def test_backup_plan_requires_dataset_ids():
    with pytest.raises(ValueError):
        BackupPlan(
            plan_id="bp_empty",
            name="Empty",
            dataset_ids=[],
            plane="edge",
            backup_frequency="PT1H",
            target_rpo="PT1H",
            target_rto="PT2H",
            retention=RetentionPolicy(min_versions=1, min_duration="P1D"),
            storage_profiles=["hot"],
            redundancy_profile="tier1",
            encryption_key_ref="kid:test",
            verification=VerificationPolicy(),
        )


def test_ensure_unique_ids_detects_duplicates():
    datasets = [
        Dataset(
            dataset_id="dup",
            name="One",
            plane="edge",
            store_type="jsonl",
            criticality="tier2",
            data_classification="public",
            rpo_target_ref="PT1H",
            rto_target_ref="PT2H",
        ),
        Dataset(
            dataset_id="dup",
            name="Two",
            plane="edge",
            store_type="jsonl",
            criticality="tier2",
            data_classification="public",
            rpo_target_ref="PT1H",
            rto_target_ref="PT2H",
        ),
    ]
    with pytest.raises(ValueError):
        ensure_unique_ids(datasets, "dataset_id")


def test_approval_record_validation():
    decision = ApprovalDecision(approver="secops")
    record = ApprovalRecord(approvals=[decision], required_count=1)
    assert record.approvals[0].approver == "secops"
    with pytest.raises(ValueError):
        ApprovalRecord(approvals=[], required_count=1)


def test_window_from_backups_requires_data():
    now = datetime.now(timezone.utc)
    run = BackupRun(
        backup_id="bk",
        plan_id="plan",
        dataset_ids=["ds"],
        started_at=now,
        finished_at=now,
        backup_type=BackupType.FULL,
        status=BackupStatus.SUCCESS,
        storage_locations=["loc"],
        checksums={},
    )
    assert window_from_backups([run])[0] == run.finished_at
    with pytest.raises(ValueError):
        window_from_backups([])

