"""Domain models for the BDR backend service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
import re
from typing import Any, Dict, Iterable, List, Literal, Optional, Sequence, Tuple

from pydantic import BaseModel, Field, field_validator, model_validator

ISO_DURATION_PATTERN = re.compile(
    r"^P(?:(?P<weeks>\d+)W|(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?"
    r"(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?)$"
)


def validate_iso_duration(value: str) -> str:
    """Validate an ISO-8601 duration string."""
    if not value:
        msg = "Duration string cannot be empty"
        raise ValueError(msg)
    if ISO_DURATION_PATTERN.fullmatch(value) is None:
        msg = (
            "Duration must match simplified ISO-8601 "
            "format (e.g., PT15M, PT2H, P1DT30M, P1W)"
        )
        raise ValueError(msg)
    return value


def duration_to_timedelta(value: str) -> timedelta:
    match = ISO_DURATION_PATTERN.fullmatch(value)
    if match is None:
        msg = f"Cannot parse duration value: {value}"
        raise ValueError(msg)
    weeks = int(match.group("weeks") or 0)
    days = int(match.group("days") or 0)
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)


class Plane(str, Enum):
    EDGE = "edge"
    TENANT_CLOUD = "tenant_cloud"
    PRODUCT_CLOUD = "product_cloud"
    SHARED_SERVICES = "shared_services"


class BackupEligibility(str, Enum):
    BACKED_UP = "backed_up"
    RECONSTRUCTED = "reconstructed"
    EXCLUDED = "excluded"


class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    SUSPECT = "suspect"


class RestoreMode(str, Enum):
    IN_PLACE = "in_place"
    SIDE_BY_SIDE = "side_by_side"
    EXPORT_ONLY = "export_only"


class DRStrategy(str, Enum):
    BACKUP_AND_RESTORE = "backup_and_restore"
    FAILOVER_TO_STANDBY = "failover_to_standby"
    CONTROLLED_SHUTDOWN = "controlled_shutdown"


class DecisionType(str, Enum):
    BACKUP_RUN_COMPLETED = "backup_run_completed"
    RESTORE_COMPLETED = "restore_completed"
    DR_EVENT_COMPLETED = "dr_event_completed"
    VALIDATION_ERROR = "validation_error"


class Dataset(BaseModel):
    dataset_id: str
    name: str
    plane: Plane
    store_type: str
    criticality: Literal["tier0", "tier1", "tier2", "tier3"]
    data_classification: str
    rpo_target_ref: str = Field(description="Reference key in GSMD for RPO target")
    rto_target_ref: str = Field(description="Reference key in GSMD for RTO target")
    eligibility: BackupEligibility = BackupEligibility.BACKED_UP
    derived_from: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_eligibility(self) -> "Dataset":
        if self.eligibility == BackupEligibility.RECONSTRUCTED and not self.derived_from:
            msg = "Reconstructed datasets must specify derived_from references"
            raise ValueError(msg)
        if self.eligibility == BackupEligibility.EXCLUDED and not self.notes:
            msg = "Excluded datasets must provide justification via notes"
            raise ValueError(msg)
        return self


class RetentionPolicy(BaseModel):
    min_versions: int = Field(ge=1)
    min_duration: str = Field(default="P1D")

    model_config = {"extra": "forbid"}

    @field_validator("min_duration")
    @classmethod
    def _validate_duration(cls, value: str) -> str:
        return validate_iso_duration(value)


class VerificationPolicy(BaseModel):
    checksum_required: bool = True
    periodic_restore_test_required: bool = True

    model_config = {"extra": "forbid"}


class BackupPlan(BaseModel):
    plan_id: str
    name: str
    dataset_ids: List[str]
    plane: Plane
    backup_frequency: str = Field(description="Cron expression or policy reference")
    target_rpo: str = Field(description="ISO duration string reference")
    target_rto: str = Field(description="ISO duration string reference")
    retention: RetentionPolicy
    storage_profiles: List[str]
    redundancy_profile: str
    encryption_key_ref: str
    verification: VerificationPolicy = Field(default_factory=VerificationPolicy)

    model_config = {"extra": "forbid"}

    @field_validator("target_rpo", "target_rto", mode="before")
    @classmethod
    def _validate_targets(cls, value: str) -> str:
        return validate_iso_duration(value)

    @model_validator(mode="after")
    def validate_dataset_ids(self) -> "BackupPlan":
        if not self.dataset_ids:
            msg = "BackupPlan must reference at least one dataset"
            raise ValueError(msg)
        return self


class BackupRun(BaseModel):
    backup_id: str
    plan_id: str
    dataset_ids: List[str]
    started_at: datetime
    finished_at: datetime
    backup_type: BackupType
    status: BackupStatus
    storage_locations: List[str]
    checksums: Dict[str, str] = Field(default_factory=dict)
    verification_status: VerificationStatus = VerificationStatus.SUSPECT
    verification_details: Optional[str] = None

    model_config = {"extra": "forbid"}


class RestorePoint(BaseModel):
    type: Literal["latest", "latest_before", "backup_id"]
    timestamp: Optional[datetime] = None
    backup_id: Optional[str] = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_restore_point(self) -> "RestorePoint":
        if self.type == "latest":
            return self
        if self.type == "latest_before" and self.timestamp is None:
            msg = "latest_before restore point requires timestamp"
            raise ValueError(msg)
        if self.type == "backup_id" and not self.backup_id:
            msg = "backup_id restore point requires backup_id value"
            raise ValueError(msg)
        return self


class RestoreRequest(BaseModel):
    dataset_ids: List[str]
    target_env: str
    mode: RestoreMode
    restore_point: RestorePoint

    model_config = {"extra": "forbid"}


class RestoreOutcome(BaseModel):
    restore_id: str
    dataset_ids: List[str]
    backup_ids: List[str]
    target_env: str
    mode: RestoreMode
    started_at: datetime
    finished_at: datetime
    status: BackupStatus
    notes: Optional[str] = None

    model_config = {"extra": "forbid"}


class DRRunbookStep(BaseModel):
    name: str
    description: str
    automated: bool = False
    depends_on: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class DRScenario(BaseModel):
    scenario_id: str
    name: str
    trigger: str
    strategy: DRStrategy
    rpo_target: str
    rto_target: str
    runbook: List[DRRunbookStep]

    model_config = {"extra": "forbid"}

    @field_validator("rpo_target", "rto_target", mode="before")
    @classmethod
    def _validate_dr_durations(cls, value: str) -> str:
        return validate_iso_duration(value)


class DrillResult(BaseModel):
    scenario_id: str
    started_at: datetime
    finished_at: datetime
    achieved_rpo: str
    achieved_rto: str
    status: BackupStatus
    issues: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class DecisionReceipt(BaseModel):
    decision_type: DecisionType
    operation_id: str
    plan_id: Optional[str] = None
    dataset_ids: List[str] = Field(default_factory=list)
    backup_id: Optional[str] = None
    restore_id: Optional[str] = None
    scenario_id: Optional[str] = None
    result: Optional[BackupStatus] = None
    policy_snapshot_hash: Optional[str] = None
    policy_version_ids: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"extra": "forbid"}


class IAMContext(BaseModel):
    actor: str
    roles: List[str]
    scopes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ApprovalDecision(BaseModel):
    approver: str
    approved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    comment: Optional[str] = None

    model_config = {"extra": "forbid"}


class ApprovalRecord(BaseModel):
    approvals: List[ApprovalDecision]
    required_count: int

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_approvals(self) -> "ApprovalRecord":
        if len(self.approvals) < self.required_count:
            msg = "Not enough approvals collected"
            raise ValueError(msg)
        return self


class AuditEvent(BaseModel):
    event_type: str
    actor: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"extra": "forbid"}


class BackupVerificationRecord(BaseModel):
    backup_id: str
    verified_at: datetime
    status: VerificationStatus
    details: Optional[str] = None

    model_config = {"extra": "forbid"}


class PlanTestMetadata(BaseModel):
    plan_id: str
    last_tested_at: Optional[datetime] = None
    last_drill_result: Optional[DrillResult] = None
    stale: bool = False

    model_config = {"extra": "forbid"}


def ensure_unique_ids(items: Sequence[BaseModel], attr: str) -> None:
    seen: Dict[Any, BaseModel] = {}
    for item in items:
        value = getattr(item, attr)
        if value in seen:
            msg = f"Duplicate {attr} detected: {value}"
            raise ValueError(msg)
        seen[value] = item


def window_from_backups(backups: Iterable[BackupRun]) -> Tuple[datetime, datetime]:
    backups_list = list(backups)
    if not backups_list:
        msg = "No backups provided to derive restore window"
        raise ValueError(msg)
    timestamps = [run.finished_at for run in backups_list]
    return (min(timestamps), max(timestamps))

