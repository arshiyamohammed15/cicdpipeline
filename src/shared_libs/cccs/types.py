"""
Typed data structures shared across CCCS services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, MutableMapping, Optional, Sequence


JSONDict = Dict[str, Any]


@dataclass(frozen=True)
class ActorContext:
    """Input required to resolve an actor block."""

    tenant_id: str
    device_id: str
    session_id: str
    user_id: str
    actor_type: str
    runtime_clock: datetime
    extras: JSONDict = field(default_factory=dict)


@dataclass(frozen=True)
class ActorBlock:
    actor_id: str
    actor_type: str
    session_id: str
    provenance_signature: str
    normalization_version: str
    warnings: Sequence[str] = field(default_factory=tuple)
    salt_version: str = ""  # EPC-1 salt version per PRD §9
    monotonic_counter: int = 0  # Provenance counter to defeat replay/downgrade per PRD §9


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    priority: int
    conditions: JSONDict
    decision: str
    rationale: str


@dataclass(frozen=True)
class PolicySnapshot:
    module_id: str
    version: str
    rules: Sequence[PolicyRule]
    signature: str
    snapshot_hash: str


@dataclass(frozen=True)
class PolicyDecision:
    decision: str
    rationale: str
    policy_version_ids: Sequence[str]
    policy_snapshot_hash: str


@dataclass(frozen=True)
class ConfigLayers:
    local: MutableMapping[str, Any]
    tenant: MutableMapping[str, Any]
    product: MutableMapping[str, Any]


@dataclass(frozen=True)
class ConfigResult:
    value: Any
    source_layers: Sequence[str]
    config_snapshot_hash: str
    warnings: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class ReceiptRecord:
    receipt_id: str
    courier_batch_id: str
    fsync_offset: int


@dataclass(frozen=True)
class BudgetDecision:
    allowed: bool
    reason: str
    remaining: float


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None


@dataclass(frozen=True)
class CanonicalError:
    canonical_code: str
    severity: str
    retryable: bool
    user_message: str
    debug_id: str


