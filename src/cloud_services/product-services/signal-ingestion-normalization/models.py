"""Data models for the SIN stub service."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class SignalKind(str, Enum):
    EVENT = "event"
    METRIC = "metric"


class Environment(str, Enum):
    DEV = "dev"
    PROD = "prod"
    STAGE = "stage"


class Plane(str, Enum):
    EDGE = "edge"
    CLOUD = "cloud"


class RoutingClass(str, Enum):
    REALTIME_DETECTION = "realtime_detection"
    EVIDENCE_STORE = "evidence_store"
    DLQ = "dlq"


class IngestStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DLQ = "dlq"


class DataContract(BaseModel):
    signal_type: str
    contract_version: str
    required_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)
    pii_flags: Dict[str, bool] = Field(default_factory=dict)
    secrets_flags: Dict[str, bool] = Field(default_factory=dict)


class ProducerRegistration(BaseModel):
    producer_id: str
    name: str
    plane: Plane
    owner: str
    allowed_signal_kinds: List[SignalKind]
    allowed_signal_types: List[str]
    contract_versions: Dict[str, str]


class SignalEnvelope(BaseModel):
    signal_id: str
    tenant_id: str
    environment: Environment
    producer_id: str
    signal_kind: SignalKind
    signal_type: str
    occurred_at: datetime
    ingested_at: datetime
    payload: Dict[str, Any]
    schema_version: str

    @field_validator("payload")
    @classmethod
    def ensure_payload(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        return value or {}


class RoutingRule(BaseModel):
    routing_class: RoutingClass
    condition: Callable[[SignalEnvelope], bool]
    destination: str
