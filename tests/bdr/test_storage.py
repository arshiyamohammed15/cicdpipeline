from bdr.models import (
    BackupEligibility,
    BackupPlan,
    BackupType,
    Dataset,
    RestoreMode,
    RetentionPolicy,
    VerificationPolicy,
)
from bdr.storage import InMemoryBackupStorage


def _plan(plan_id: str) -> BackupPlan:
    return BackupPlan(
        plan_id=plan_id,
        name="plan",
        dataset_ids=["ds"],
        plane="product_cloud",
        backup_frequency="PT1H",
        target_rpo="PT1H",
        target_rto="PT2H",
        retention=RetentionPolicy(min_versions=1, min_duration="P1D"),
        storage_profiles=["hot"],
        redundancy_profile="tier0",
        encryption_key_ref="kid:test",
        verification=VerificationPolicy(),
    )


def test_in_memory_storage_round_trip():
    storage = InMemoryBackupStorage()
    storage.seed_dataset("ds", "data")
    dataset = Dataset(
        dataset_id="ds",
        name="Dataset",
        plane="product_cloud",
        store_type="postgres",
        criticality="tier1",
        data_classification="internal",
        rpo_target_ref="PT1H",
        rto_target_ref="PT2H",
        eligibility=BackupEligibility.BACKED_UP,
    )
    artifacts = storage.create_backup(_plan("p1"), [dataset], backup_type=BackupType.FULL)
    assert len(artifacts) == 1
    storage.restore(artifacts, mode=RestoreMode.IN_PLACE, target_env="staging")
    assert storage.restores[-1]["target_env"] == "staging"

