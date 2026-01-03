"""
Domain models for Signal Ingestion & Normalization (SIN) Module.

What: Pydantic models for SignalEnvelope, ProducerRegistration, payloads, and related data structures
Why: Type safety, validation, and standardized data contracts per PRD v1.0
Reads/Writes: Request/response validation, no file I/O
Contracts: PRD §4.1 (F1), §4.2 (F2), §5 Data & API Contracts
Risks: Model validation failures may expose internal error details if not handled properly
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ============================================================================
# Enums
# ============================================================================

class SignalKind(str, Enum):
    """Signal kind enumeration per F1.1."""
    EVENT = "event"
    METRIC = "metric"
    LOG = "log"
    TRACE = "trace"


class Plane(str, Enum):
    """Plane enumeration per §3.2."""
    EDGE = "edge"
    TENANT_CLOUD = "tenant_cloud"
    PRODUCT_CLOUD = "product_cloud"
    SHARED_SERVICES = "shared_services"


class Environment(str, Enum):
    """Environment enumeration."""
    DEV = "dev"
    STAGE = "stage"
    PROD = "prod"


class MetricType(str, Enum):
    """Metric type enumeration per F1.2."""
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"


class Severity(str, Enum):
    """Event severity enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogLevel(str, Enum):
    """Log level enumeration per F1.2."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SpanStatus(str, Enum):
    """Trace span status enumeration per F1.2."""
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


class IngestStatus(str, Enum):
    """Signal ingestion status."""
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DLQ = "dlq"


class ErrorCode(str, Enum):
    """Error code enumeration for validation and DLQ."""
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    GOVERNANCE_VIOLATION = "GOVERNANCE_VIOLATION"
    PRODUCER_NOT_REGISTERED = "PRODUCER_NOT_REGISTERED"
    SIGNAL_TYPE_NOT_ALLOWED = "SIGNAL_TYPE_NOT_ALLOWED"
    TENANT_ISOLATION_VIOLATION = "TENANT_ISOLATION_VIOLATION"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NORMALIZATION_ERROR = "NORMALIZATION_ERROR"
    ROUTING_ERROR = "ROUTING_ERROR"
    DOWNSTREAM_ERROR = "DOWNSTREAM_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"


class RoutingClass(str, Enum):
    """Routing class enumeration per F6."""
    REALTIME_DETECTION = "realtime_detection"
    EVIDENCE_STORE = "evidence_store"
    ANALYTICS_STORE = "analytics_store"
    COST_OBSERVABILITY = "cost_observability"


# ============================================================================
# Payload Models (F1.2)
# ============================================================================

class EventPayload(BaseModel):
    """Event payload model per F1.2."""
    event_name: str = Field(..., description="Event name")
    severity: Severity = Field(..., description="Event severity")
    tags: Optional[Dict[str, str]] = Field(None, description="Event tags")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Event attributes (key-value)")


class MetricPayload(BaseModel):
    """Metric payload model per F1.2."""
    metric_name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Metric unit")
    metric_type: MetricType = Field(..., description="Metric type (gauge, counter, histogram)")


class LogPayload(BaseModel):
    """Log payload model per F1.2."""
    log_level: LogLevel = Field(..., description="Log level")
    message_template: str = Field(..., description="Log message template")
    structured_fields: Optional[Dict[str, Any]] = Field(None, description="Structured log fields")


class TracePayload(BaseModel):
    """Trace payload model per F1.2."""
    span_name: str = Field(..., description="Span name")
    duration_ms: float = Field(..., description="Span duration in milliseconds")
    status: SpanStatus = Field(..., description="Span status")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Span attributes")


# ============================================================================
# Resource Model
# ============================================================================

class Resource(BaseModel):
    """Resource context model per F1.1."""
    service_name: Optional[str] = Field(None, description="Service name")
    repository: Optional[str] = Field(None, description="Repository (org/repo)")
    branch: Optional[str] = Field(None, description="Branch name")
    commit: Optional[str] = Field(None, description="Commit hash")
    module: Optional[str] = Field(None, description="Module name")
    plane: Optional[Plane] = Field(None, description="Plane")
    file_path: Optional[str] = Field(None, description="File path (if allowed)")
    pr_id: Optional[int] = Field(None, description="Pull request ID")
    environment: Optional[str] = Field(None, description="Environment")
    deployment_id: Optional[str] = Field(None, description="Deployment ID")


# ============================================================================
# SignalEnvelope Model (F1.1)
# ============================================================================

class SignalEnvelope(BaseModel):
    """Canonical SignalEnvelope model per F1.1."""
    signal_id: str = Field(..., description="Global unique ID")
    tenant_id: str = Field(..., description="Tenant ID")
    environment: Environment = Field(..., description="Environment (dev/stage/prod)")
    producer_id: str = Field(..., description="Component / integration ID")
    actor_id: Optional[str] = Field(None, description="Human or AI agent ID")
    signal_kind: SignalKind = Field(..., description="Signal kind (event, metric, log, trace)")
    signal_type: str = Field(..., description="Signal type (e.g., pr_opened, test_failed)")
    occurred_at: datetime = Field(..., description="When the signal occurred")
    ingested_at: datetime = Field(..., description="When the signal was ingested")
    trace_id: Optional[str] = Field(None, description="Trace ID (when available)")
    span_id: Optional[str] = Field(None, description="Span ID (when available)")
    correlation_id: Optional[str] = Field(None, description="Correlation ID (when available)")
    resource: Optional[Resource] = Field(None, description="Resource context")
    payload: Dict[str, Any] = Field(..., description="Type-specific normalized payload")
    schema_version: str = Field(..., description="Schema version for forward/backward compatibility")
    sequence_no: Optional[int] = Field(None, description="Sequence number for ordering (when available)")

    # Note: Payload validation is done by the validation engine, not at model level
    # This allows invalid signals to be created and then validated/routed to DLQ


# ============================================================================
# Producer Registration Models (F2.1)
# ============================================================================

class ProducerRegistration(BaseModel):
    """Producer registration model per F2.1."""
    producer_id: str = Field(..., description="Producer identifier")
    name: str = Field(..., description="Producer name")
    plane: Plane = Field(..., description="Plane where producer operates")
    owner: str = Field(..., description="Producer owner")
    allowed_signal_kinds: List[SignalKind] = Field(..., description="Allowed signal kinds")
    allowed_signal_types: List[str] = Field(..., description="Allowed signal types")
    contract_versions: Dict[str, str] = Field(..., description="Contract versions per signal_type")
    max_rate_per_minute: Optional[int] = Field(None, description="Max rate per minute (from policy)")
    schema_version: Optional[str] = Field(None, description="Schema version producer emits")


# ============================================================================
# Data Contract Models (F2.2)
# ============================================================================

class DataContract(BaseModel):
    """Data contract model per F2.2."""
    signal_type: str = Field(..., description="Signal type")
    contract_version: str = Field(..., description="Contract version")
    required_fields: List[str] = Field(..., description="Required fields")
    optional_fields: List[str] = Field(default_factory=list, description="Optional fields")
    allowed_value_ranges: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Allowed value ranges")
    allowed_units: Optional[Dict[str, List[str]]] = Field(None, description="Allowed units per field")
    enum_values: Optional[Dict[str, List[str]]] = Field(None, description="Enum values per field")
    pii_flags: Optional[Dict[str, bool]] = Field(None, description="PII flags per field")
    secrets_flags: Optional[Dict[str, bool]] = Field(None, description="Secrets flags per field")
    redaction_rules: Optional[Dict[str, str]] = Field(None, description="Redaction rules per field")
    classification: Optional[str] = Field(None, description="Classification (sensitivity, residency)")
    disallowed_fields: Optional[List[str]] = Field(None, description="Disallowed fields")


# ============================================================================
# Ingestion Request/Response Models
# ============================================================================

class IngestRequest(BaseModel):
    """Request model for signal ingestion."""
    signals: List[SignalEnvelope] = Field(..., description="List of signals to ingest", min_length=1, max_length=1000)


class SignalIngestResult(BaseModel):
    """Result for a single signal ingestion."""
    # Allow construction from objects with attributes (e.g., service mocks)
    model_config = ConfigDict(from_attributes=True)
    signal_id: str = Field(..., description="Signal ID")
    status: IngestStatus = Field(..., description="Ingestion status")
    error_code: Optional[ErrorCode] = Field(None, description="Error code if rejected")
    error_message: Optional[str] = Field(None, description="Error message if rejected")
    dlq_id: Optional[str] = Field(None, description="DLQ entry ID if routed to DLQ")
    warnings: List[str] = Field(default_factory=list, description="Warnings (e.g., coercion)")


class IngestResponse(BaseModel):
    """Response model for signal ingestion per §5.3."""
    results: List[SignalIngestResult] = Field(..., description="Per-signal results")
    summary: Dict[str, int] = Field(..., description="Summary: total, accepted, rejected, dlq")


# ============================================================================
# DLQ Models (F8)
# ============================================================================

class DLQEntry(BaseModel):
    """Dead Letter Queue entry model per F8."""
    dlq_id: str = Field(..., description="DLQ entry ID")
    signal_id: str = Field(..., description="Original signal ID")
    tenant_id: str = Field(..., description="Tenant ID")
    producer_id: str = Field(..., description="Producer ID")
    signal_type: str = Field(..., description="Signal type")
    original_signal: Dict[str, Any] = Field(..., description="Original signal (already redacted)")
    error_code: ErrorCode = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    first_failure_timestamp: datetime = Field(..., description="First failure timestamp")
    retry_count: int = Field(..., description="Retry count")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="DLQ entry creation timestamp")


class DLQInspectionRequest(BaseModel):
    """Request model for DLQ inspection."""
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")
    producer_id: Optional[str] = Field(None, description="Filter by producer ID")
    signal_type: Optional[str] = Field(None, description="Filter by signal type")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of entries")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class DLQInspectionResponse(BaseModel):
    """Response model for DLQ inspection."""
    entries: List[DLQEntry] = Field(..., description="DLQ entries")
    total: int = Field(..., description="Total number of entries matching filters")


# ============================================================================
# Producer Registration Request/Response Models
# ============================================================================

class ProducerRegistrationRequest(BaseModel):
    """Request model for producer registration."""
    producer: ProducerRegistration = Field(..., description="Producer registration data")


class ProducerRegistrationResponse(BaseModel):
    """Response model for producer registration."""
    producer_id: str = Field(..., description="Producer ID")
    status: str = Field(..., description="Registration status")
    message: Optional[str] = Field(None, description="Status message")


# ============================================================================
# Error Models
# ============================================================================

class ValidationError(BaseModel):
    """Validation error model."""
    error_code: ErrorCode = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    field_path: Optional[str] = Field(None, description="Field path where error occurred")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class CoercionWarning(BaseModel):
    """Coercion warning model for recoverable errors."""
    field_path: str = Field(..., description="Field path where coercion occurred")
    original_value: Any = Field(..., description="Original value")
    coerced_value: Any = Field(..., description="Coerced value")
    warning_message: str = Field(..., description="Warning message")


# ============================================================================
# Health Check Models (F9)
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")


class ReadinessResponse(BaseModel):
    """Readiness check response model."""
    ready: bool = Field(..., description="Ready status")
    checks: Dict[str, bool] = Field(..., description="Individual readiness checks")
    timestamp: Optional[datetime] = Field(None, description="Check timestamp")

