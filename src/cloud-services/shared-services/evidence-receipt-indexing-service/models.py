"""
Pydantic models for Evidence & Receipt Indexing Service (ERIS) API contracts.

What: Request/response models for all ERIS API endpoints
Why: Type-safe API contracts, validation, serialization
Reads/Writes: Used by FastAPI for request/response validation
Contracts: ERIS API contract per PRD Section 9
Risks: Schema mismatches, validation failures
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseModel, Field


# Sub-feature 2.1: Health, Metrics, Config, Error Models

class HealthResponse(BaseModel):
    """Health check response model per PRD Section 9.8."""
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DependencyStatus(BaseModel):
    """Dependency health status."""
    storage: str = Field(..., description="Storage status")
    iam: str = Field(..., description="IAM status")
    data_governance: str = Field(..., description="Data Governance status")
    contracts_schema_registry: str = Field(..., description="Contracts & Schema Registry status")
    kms: str = Field(..., description="KMS status")


class HealthResponseDetailed(BaseModel):
    """Detailed health check response with dependencies."""
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: DependencyStatus = Field(..., description="Dependency status")


class MetricsResponse(BaseModel):
    """Metrics response model per PRD Section 9.8."""
    metrics: str = Field(..., description="Prometheus-format metrics")


class ConfigResponse(BaseModel):
    """Configuration response model per PRD Section 9.8."""
    module_id: str = Field(default="PM-7", description="Module identifier")
    module_name: str = Field(default="Evidence & Receipt Indexing Service (ERIS)", description="Module name")
    version: str = Field(..., description="Service version")
    capabilities: List[str] = Field(..., description="Supported capabilities")
    supported_schema_versions: List[str] = Field(..., description="Supported receipt schema versions")
    rate_limits: Dict[str, Any] = Field(..., description="Rate limit configuration")
    storage_config: Dict[str, Any] = Field(..., description="Storage configuration")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorDetail(BaseModel):
    """Error detail model per PRD Section 9.9."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    retryable: bool = Field(default=False, description="Whether error is retryable")
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model per PRD Section 9.9."""
    error: ErrorDetail = Field(..., description="Error details")


# Sub-feature 2.2: Receipt Data Models

class DecisionStatus(str, Enum):
    """Decision status enum per canonical schema."""
    PASS = "pass"
    WARN = "warn"
    SOFT_BLOCK = "soft_block"
    HARD_BLOCK = "hard_block"


class EvaluationPoint(str, Enum):
    """Evaluation point enum per canonical schema."""
    PRE_COMMIT = "pre-commit"
    PRE_MERGE = "pre-merge"
    PRE_DEPLOY = "pre-deploy"
    POST_DEPLOY = "post-deploy"


class ActorType(str, Enum):
    """Actor type enum per canonical schema."""
    HUMAN = "human"
    AI_AGENT = "ai_agent"
    SERVICE = "service"


class DecisionBlock(BaseModel):
    """Decision block per canonical schema."""
    status: DecisionStatus = Field(..., description="Decision status")
    rationale: str = Field(..., description="Human-readable explanation")
    badges: List[str] = Field(default_factory=list, description="Array of badge strings")


class ActorBlock(BaseModel):
    """Actor block per canonical schema."""
    repo_id: str = Field(..., description="Repository identifier")
    machine_fingerprint: Optional[str] = Field(None, description="Machine fingerprint")
    type: Optional[ActorType] = Field(None, description="Actor type")


class ReceiptIngestionRequest(BaseModel):
    """Receipt ingestion request per PRD Section 9.1."""
    receipt_id: str = Field(..., description="Unique receipt identifier (UUID)")
    gate_id: str = Field(..., description="Gate identifier")
    policy_version_ids: List[str] = Field(..., description="Array of policy version IDs")
    snapshot_hash: str = Field(..., description="SHA256 hash of policy snapshot")
    timestamp_utc: datetime = Field(..., description="ISO 8601 UTC timestamp")
    timestamp_monotonic_ms: int = Field(..., description="Hardware monotonic timestamp")
    evaluation_point: EvaluationPoint = Field(..., description="Evaluation point")
    inputs: Dict[str, Any] = Field(..., description="Metadata-only JSON object")
    decision: DecisionBlock = Field(..., description="Decision block")
    result: Optional[Dict[str, Any]] = Field(None, description="Metadata-only JSON object")
    actor: ActorBlock = Field(..., description="Actor block")
    evidence_handles: Optional[List[Dict[str, Any]]] = Field(None, description="Evidence references")
    degraded: bool = Field(default=False, description="Degraded mode flag")
    signature: str = Field(..., description="Cryptographic signature")
    schema_version: str = Field(..., description="Schema version identifier")


class ReceiptIngestionResponse(BaseModel):
    """Receipt ingestion response per PRD Section 9.1."""
    receipt_id: str = Field(..., description="Receipt identifier")
    status: str = Field(..., description="Ingestion status")
    signature_verification_status: Optional[str] = Field(None, description="Signature verification status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReceiptSearchRequest(BaseModel):
    """Receipt search request per PRD Section 9.2."""
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    plane: Optional[str] = Field(None, description="Plane filter")
    environment: Optional[str] = Field(None, description="Environment filter")
    from_timestamp: Optional[datetime] = Field(None, description="Start time range")
    to_timestamp: Optional[datetime] = Field(None, description="End time range")
    gate_id: Optional[str] = Field(None, description="Gate ID filter")
    module_id: Optional[str] = Field(None, description="Module ID filter")
    policy_version_ids: Optional[List[str]] = Field(None, description="Policy version IDs filter")
    decision_status: Optional[DecisionStatus] = Field(None, description="Decision status filter")
    severity: Optional[str] = Field(None, description="Severity filter")
    actor_repo_id: Optional[str] = Field(None, description="Actor repo ID filter")
    actor_type: Optional[ActorType] = Field(None, description="Actor type filter")
    resource_type: Optional[str] = Field(None, description="Resource type filter")
    resource_id: Optional[str] = Field(None, description="Resource ID filter")
    chain_id: Optional[str] = Field(None, description="Chain ID filter")
    parent_receipt_id: Optional[str] = Field(None, description="Parent receipt ID filter")
    cursor: Optional[str] = Field(None, description="Pagination cursor")
    limit: int = Field(default=100, ge=1, le=1000, description="Page size limit")


class ReceiptSearchResponse(BaseModel):
    """Receipt search response per PRD Section 9.2."""
    receipts: List[Dict[str, Any]] = Field(..., description="Page of receipts")
    next_cursor: Optional[str] = Field(None, description="Next page cursor")
    total_count: Optional[int] = Field(None, description="Total matching receipts")


class ReceiptAggregateRequest(BaseModel):
    """Receipt aggregation request per PRD Section 9.2."""
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    group_by: List[str] = Field(..., description="Fields to group by")
    time_bucket: Optional[str] = Field(None, description="Time bucket (day, week, month)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")


class ReceiptAggregateResponse(BaseModel):
    """Receipt aggregation response per PRD Section 9.2."""
    aggregations: Dict[str, Any] = Field(..., description="Aggregation results")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Sub-feature 2.3: Courier Batch and Export Models

class CourierBatchRequest(BaseModel):
    """Courier batch ingestion request per PRD Section 9.4."""
    batch_id: str = Field(..., description="Unique batch identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    emitter_service: str = Field(..., description="Service that emitted the batch")
    sequence_numbers: List[str] = Field(..., description="Sequence numbers for deduplication")
    merkle_root: str = Field(..., description="Merkle root hash of the batch")
    receipts: List[Dict[str, Any]] = Field(..., description="Array of receipt JSON documents")
    timestamp: datetime = Field(..., description="Batch creation timestamp")


class CourierBatchResponse(BaseModel):
    """Courier batch ingestion response per PRD Section 9.4."""
    batch_id: str = Field(..., description="Batch identifier")
    status: str = Field(..., description="Ingestion status")
    receipt_count: int = Field(..., description="Number of receipts ingested")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MerkleProofResponse(BaseModel):
    """Merkle proof response per PRD Section 9.4."""
    batch_id: str = Field(..., description="Batch identifier")
    merkle_root: str = Field(..., description="Merkle root hash")
    leaf_hashes: List[str] = Field(..., description="Leaf hashes")
    path_to_root: List[str] = Field(..., description="Path to root")


class ExportFormat(str, Enum):
    """Export format enum per PRD Section 9.5."""
    JSONL = "jsonl"
    CSV = "csv"
    PARQUET = "parquet"


class CompressionFormat(str, Enum):
    """Compression format enum per PRD Section 9.5."""
    NONE = "none"
    GZIP = "gzip"
    ZIP = "zip"


class ExportRequest(BaseModel):
    """Export request per PRD Section 9.5."""
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    from_timestamp: Optional[datetime] = Field(None, description="Start time range")
    to_timestamp: Optional[datetime] = Field(None, description="End time range")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    chain_id: Optional[str] = Field(None, description="Chain ID filter")
    export_format: ExportFormat = Field(default=ExportFormat.JSONL, description="Export format")
    include_metadata: bool = Field(default=True, description="Include ERIS metadata")
    include_signatures: bool = Field(default=True, description="Include receipt signatures")
    compression: CompressionFormat = Field(default=CompressionFormat.GZIP, description="Compression format")


class ExportResponse(BaseModel):
    """Export response per PRD Section 9.5."""
    export_id: str = Field(..., description="Export job identifier")
    status: str = Field(..., description="Export status")
    download_url: Optional[str] = Field(None, description="Download URL when completed")
    export_metadata: Optional[Dict[str, Any]] = Field(None, description="Export metadata")


class ExportStatusResponse(BaseModel):
    """Export status response per PRD Section 9.5."""
    export_id: str = Field(..., description="Export job identifier")
    status: str = Field(..., description="Export status")
    download_url: Optional[str] = Field(None, description="Download URL when completed")
    export_metadata: Optional[Dict[str, Any]] = Field(None, description="Export metadata")
    created_at: datetime = Field(..., description="Export creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ChainDirection(str, Enum):
    """Chain traversal direction enum per PRD Section 9.6."""
    UP = "up"
    DOWN = "down"
    BOTH = "both"
    SIBLINGS = "siblings"


class ChainTraversalRequest(BaseModel):
    """Chain traversal request per PRD Section 9.6."""
    receipt_id: str = Field(..., description="Starting receipt identifier")
    direction: ChainDirection = Field(default=ChainDirection.BOTH, description="Traversal direction")
    max_depth: int = Field(default=10, ge=1, le=100, description="Maximum traversal depth")
    include_metadata: bool = Field(default=True, description="Include ERIS metadata")


class ChainTraversalResponse(BaseModel):
    """Chain traversal response per PRD Section 9.6."""
    receipts: List[Dict[str, Any]] = Field(..., description="Receipts in chain")
    traversal_depth: int = Field(..., description="Actual traversal depth")
    circular_references_detected: bool = Field(default=False, description="Circular references found")


class ChainQueryRequest(BaseModel):
    """Chain query request per PRD Section 9.6."""
    root_receipt_id: Optional[str] = Field(None, description="Root receipt identifier")
    flow_id: Optional[str] = Field(None, description="Flow identifier")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")


class ChainQueryResponse(BaseModel):
    """Chain query response per PRD Section 9.6."""
    receipts: List[Dict[str, Any]] = Field(..., description="Receipts in chain matching filters")
    chain_count: int = Field(..., description="Number of receipts in chain")

