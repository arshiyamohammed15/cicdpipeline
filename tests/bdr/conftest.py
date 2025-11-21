import pytest

from bdr.models import IAMContext, RestoreMode, RestorePoint, RestoreRequest
from bdr.service import BDRService
from bdr.storage import InMemoryBackupStorage


@pytest.fixture(scope="module")
def dataset_definitions():
    return [
        {
            "dataset_id": "ds_policy_store",
            "name": "Policy Store",
            "plane": "product_cloud",
            "store_type": "postgres",
            "criticality": "tier0",
            "data_classification": "restricted",
            "rpo_target_ref": "PT15M",
            "rto_target_ref": "PT30M",
            "eligibility": "backed_up",
        },
        {
            "dataset_id": "ds_observability",
            "name": "Observability Logs",
            "plane": "shared_services",
            "store_type": "object_store",
            "criticality": "tier1",
            "data_classification": "internal",
            "rpo_target_ref": "PT30M",
            "rto_target_ref": "PT60M",
            "eligibility": "backed_up",
        },
    ]


@pytest.fixture(scope="module")
def plan_definitions():
    return [
        {
            "plan_id": "bp_policy_store",
            "name": "Policy Store Backup",
            "dataset_ids": ["ds_policy_store"],
            "plane": "product_cloud",
            "backup_frequency": "PT15M",
            "target_rpo": "PT15M",
            "target_rto": "PT30M",
            "retention": {"min_versions": 30, "min_duration": "P30D"},
            "storage_profiles": ["hot", "archive"],
            "redundancy_profile": "tier0_multi_site",
            "encryption_key_ref": "kid:backup-core-01",
            "verification": {
                "checksum_required": True,
                "periodic_restore_test_required": True,
            },
        },
        {
            "plan_id": "bp_observability",
            "name": "Observability Backup",
            "dataset_ids": ["ds_observability"],
            "plane": "shared_services",
            "backup_frequency": "PT30M",
            "target_rpo": "PT30M",
            "target_rto": "PT60M",
            "retention": {"min_versions": 7, "min_duration": "P7D"},
            "storage_profiles": ["hot"],
            "redundancy_profile": "tier1_dual_zone",
            "encryption_key_ref": "kid:backup-core-02",
            "verification": {
                "checksum_required": True,
                "periodic_restore_test_required": False,
            },
        },
    ]


@pytest.fixture
def storage_backend():
    backend = InMemoryBackupStorage()
    backend.seed_dataset("ds_policy_store", "policy-data")
    backend.seed_dataset("ds_observability", "observability-data")
    return backend


@pytest.fixture
def iam_context():
    return IAMContext(actor="svc_bdr", roles=["bdr:backup:run", "bdr:restore:execute"], scopes=["backup:run", "restore:execute", "dr:admin", "dr:execute"])


@pytest.fixture
def bdr_service(dataset_definitions, plan_definitions, storage_backend):
    return BDRService(
        dataset_source=dataset_definitions,
        plan_source=plan_definitions,
        storage=storage_backend,
    )


@pytest.fixture
def restore_request():
    return RestoreRequest(
        dataset_ids=["ds_policy_store"],
        target_env="staging",
        mode=RestoreMode.SIDE_BY_SIDE,
        restore_point=RestorePoint(type="latest"),
    )

