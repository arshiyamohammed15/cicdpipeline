"""
Pydantic models for Contracts & Schema Registry (EPC-12).

What: Defines Pydantic v2 models for request/response validation per PRD v1.2.0
Why: Ensures type safety, input validation, and standardized API contracts
Reads/Writes: Reads request data, writes response data (no file I/O)
Contracts: PRD API contract, error model, data schemas
Risks: Model validation failures may expose internal error details if not handled properly
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID


# ============================================================================
# Request Models
# ============================================================================

class RegisterSchemaRequest(BaseModel):
    """Request model for schema registration."""

    schema_type: str = Field(..., description="Schema type", pattern="^(json_schema|avro|protobuf)$")
    schema_definition: Dict[str, Any] = Field(..., description="Schema definition")
    compatibility: str = Field(..., description="Compatibility mode", pattern="^(backward|forward|full|none)$")
    name: str = Field(..., description="Schema name", min_length=1, max_length=255)
    namespace: str = Field(..., description="Schema namespace", min_length=1, max_length=255)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class UpdateSchemaRequest(BaseModel):
    """Request model for schema update (creates new version)."""

    schema_definition: Dict[str, Any] = Field(..., description="Updated schema definition")
    compatibility: str = Field(..., description="Compatibility mode", pattern="^(backward|forward|full|none)$")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class ValidateDataRequest(BaseModel):
    """Request model for data validation."""

    schema_id: str = Field(..., description="Schema identifier (UUID)", pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    version: Optional[str] = Field(None, description="Schema version (optional)")
    data: Dict[str, Any] = Field(..., description="Data to validate")


class CheckCompatibilityRequest(BaseModel):
    """Request model for compatibility checking."""

    source_schema: Dict[str, Any] = Field(..., description="Source schema definition")
    target_schema: Dict[str, Any] = Field(..., description="Target schema definition")
    compatibility_mode: Optional[str] = Field(None, description="Compatibility mode", pattern="^(backward|forward|full)$")


class TransformDataRequest(BaseModel):
    """Request model for data transformation."""

    source_schema_id: str = Field(..., description="Source schema identifier (UUID)", pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    source_version: Optional[str] = Field(None, description="Source schema version")
    target_schema_id: str = Field(..., description="Target schema identifier (UUID)", pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    target_version: Optional[str] = Field(None, description="Target schema version")
    data: Dict[str, Any] = Field(..., description="Data to transform")


class CreateContractRequest(BaseModel):
    """Request model for contract creation."""

    name: str = Field(..., description="Contract name", min_length=1, max_length=255)
    type: str = Field(..., description="Contract type", pattern="^(api|event|data)$")
    schema_id: str = Field(..., description="Schema identifier (UUID)", pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    validation_rules: List[Dict[str, Any]] = Field(..., description="Validation rules", min_length=1)
    enforcement_level: str = Field(..., description="Enforcement level", pattern="^(strict|warning|advisory)$")
    violation_actions: List[str] = Field(..., description="Violation actions", min_length=1)


class UpdateContractRequest(BaseModel):
    """Request model for contract update."""

    validation_rules: Optional[List[Dict[str, Any]]] = Field(None, description="Updated validation rules")
    enforcement_level: Optional[str] = Field(None, description="Enforcement level", pattern="^(strict|warning|advisory)$")
    violation_actions: Optional[List[str]] = Field(None, description="Violation actions")


class BulkRegisterSchemasRequest(BaseModel):
    """Request model for bulk schema registration."""

    schemas: List[Dict[str, Any]] = Field(..., description="List of schemas to register", min_length=1, max_length=100)
    validate_only: bool = Field(False, description="Only validate, do not register")
    publish: bool = Field(True, description="Publish schemas after registration")


class BulkValidateRequest(BaseModel):
    """Request model for bulk validation."""

    validations: List[Dict[str, Any]] = Field(..., description="List of validations", min_length=1, max_length=500)


class CreateTemplateRequest(BaseModel):
    """Request model for template creation."""

    name: str = Field(..., description="Template name", min_length=1)
    description: str = Field(..., description="Template description", min_length=1)
    schema_definition: Dict[str, Any] = Field(..., description="Template schema definition")
    required_fields: Optional[List[str]] = Field(None, description="Required fields")
    optional_fields: Optional[List[str]] = Field(None, description="Optional fields")
    validation_rules: Optional[List[Dict[str, Any]]] = Field(None, description="Validation rules")


class InstantiateTemplateRequest(BaseModel):
    """Request model for template instantiation."""

    name: str = Field(..., description="Schema name", min_length=1)
    namespace: str = Field(..., description="Schema namespace", min_length=1)
    compatibility: str = Field(..., description="Compatibility mode", pattern="^(backward|forward|full|none)$")
    overrides: Optional[Dict[str, Any]] = Field(None, description="Schema definition overrides")


# ============================================================================
# Response Models
# ============================================================================

class SchemaMetadata(BaseModel):
    """Schema metadata model per PRD."""

    schema_id: str = Field(..., description="Schema identifier (UUID)")
    name: str = Field(..., description="Schema name")
    namespace: str = Field(..., description="Schema namespace")
    schema_type: str = Field(..., description="Schema type", pattern="^(json_schema|avro|protobuf)$")
    schema_definition: Dict[str, Any] = Field(..., description="Schema definition")
    version: str = Field(..., description="Schema version")
    compatibility: str = Field(..., description="Compatibility mode", pattern="^(backward|forward|full|none)$")
    status: str = Field(..., description="Schema status", pattern="^(draft|published|deprecated)$")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Update timestamp (ISO 8601)")
    created_by: str = Field(..., description="Creator identifier (UUID)")
    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    dependencies: Optional[List[str]] = Field(None, description="Dependent schema IDs")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ContractDefinition(BaseModel):
    """Contract definition model per PRD."""

    contract_id: str = Field(..., description="Contract identifier (UUID)")
    name: str = Field(..., description="Contract name")
    type: str = Field(..., description="Contract type", pattern="^(api|event|data)$")
    schema_id: str = Field(..., description="Schema identifier (UUID)")
    validation_rules: List[Dict[str, Any]] = Field(..., description="Validation rules")
    enforcement_level: str = Field(..., description="Enforcement level", pattern="^(strict|warning|advisory)$")
    violation_actions: List[str] = Field(..., description="Violation actions")
    version: str = Field(..., description="Contract version")
    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Update timestamp (ISO 8601)")
    created_by: str = Field(..., description="Creator identifier (UUID)")


class ValidationError(BaseModel):
    """Validation error detail."""

    field: str = Field(..., description="Field path")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ValidationResult(BaseModel):
    """Validation result model."""

    valid: bool = Field(..., description="Whether validation passed")
    errors: List[ValidationError] = Field(default_factory=list, description="Validation errors")


class CompatibilityResult(BaseModel):
    """Compatibility check result model."""

    compatible: bool = Field(..., description="Whether schemas are compatible")
    breaking_changes: List[str] = Field(default_factory=list, description="List of breaking changes")
    warnings: Optional[List[str]] = Field(None, description="Compatibility warnings")


class TransformationResult(BaseModel):
    """Data transformation result model."""

    transformed_data: Dict[str, Any] = Field(..., description="Transformed data")
    transformation_applied: bool = Field(..., description="Whether transformation was applied")
    warnings: List[str] = Field(default_factory=list, description="Transformation warnings")


class BulkOperationItem(BaseModel):
    """Bulk operation item result."""

    index: int = Field(..., description="Item index")
    success: bool = Field(..., description="Whether operation succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")
    result: Optional[Dict[str, Any]] = Field(None, description="Result data if succeeded")


class BulkOperationResponse(BaseModel):
    """Bulk operation response model."""

    operation_id: str = Field(..., description="Operation identifier (UUID)")
    status: str = Field(..., description="Operation status", pattern="^(accepted|processing|completed|failed)$")
    total_items: int = Field(..., description="Total number of items")
    succeeded: int = Field(..., description="Number of succeeded items")
    failed: int = Field(..., description="Number of failed items")
    items: Optional[List[BulkOperationItem]] = Field(None, description="Individual item results")


class TemplateResponse(BaseModel):
    """Template response model."""

    template_id: str = Field(..., description="Template identifier (UUID)")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    schema_definition: Dict[str, Any] = Field(..., description="Template schema definition")
    required_fields: List[str] = Field(default_factory=list, description="Required fields")
    optional_fields: List[str] = Field(default_factory=list, description="Optional fields")
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list, description="Validation rules")
    version: str = Field(..., description="Template version")


class HealthCheck(BaseModel):
    """Health check item model."""

    name: str = Field(..., description="Check name")
    status: str = Field(..., description="Check status", pattern="^(pass|fail|warn)$")
    detail: Optional[str] = Field(None, description="Check detail")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Overall health status", pattern="^(healthy|degraded|unhealthy)$")
    timestamp: str = Field(..., description="Timestamp (ISO 8601)")
    checks: Optional[List[HealthCheck]] = Field(None, description="Health checks")


class MetricsResponse(BaseModel):
    """Metrics response model."""

    schema_validation_count: int = Field(..., description="Total schema validations", ge=0)
    contract_enforcement_count: int = Field(..., description="Total contract enforcements", ge=0)
    compatibility_check_count: int = Field(..., description="Total compatibility checks", ge=0)
    schema_registration_count: int = Field(..., description="Total schema registrations", ge=0)
    average_validation_latency_ms: float = Field(..., description="Average validation latency (ms)", ge=0.0)
    average_contract_latency_ms: float = Field(..., description="Average contract enforcement latency (ms)", ge=0.0)
    average_compatibility_latency_ms: float = Field(..., description="Average compatibility check latency (ms)", ge=0.0)
    cache_hit_rate: float = Field(..., description="Cache hit rate", ge=0.0, le=1.0)
    error_rate: float = Field(..., description="Error rate", ge=0.0, le=1.0)
    timestamp: str = Field(..., description="Metrics timestamp (ISO 8601)")


class ConfigResponse(BaseModel):
    """Configuration response model."""

    module_id: str = Field(..., description="Module identifier")
    version: str = Field(..., description="Module version")
    api_endpoints: Dict[str, str] = Field(..., description="API endpoints")
    performance_requirements: Dict[str, Any] = Field(..., description="Performance requirements")
    timestamp: str = Field(..., description="Config timestamp (ISO 8601)")


class ErrorDetail(BaseModel):
    """Error detail model per PRD."""

    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message", min_length=1)
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    correlation_id: str = Field(..., description="Correlation identifier (UUID)")
    retriable: bool = Field(..., description="Whether error is retriable")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier (UUID)")


class ErrorResponse(BaseModel):
    """Error response model per PRD."""

    error: ErrorDetail = Field(..., description="Error information")


# ============================================================================
# Internal Models
# ============================================================================

class ValidationReceipt(BaseModel):
    """Validation receipt model per PRD."""

    receipt_id: str = Field(..., description="Receipt identifier (UUID)")
    ts: str = Field(..., description="Timestamp (ISO 8601)")
    module: str = Field(default="REGISTRY", description="Module identifier")
    operation: str = Field(..., description="Operation type", pattern="^(schema_validated|contract_enforced|compatibility_checked)$")
    registry_context: Dict[str, Any] = Field(..., description="Registry context")
    requesting_module: str = Field(..., description="Requesting module ID")
    signature: Optional[str] = Field(None, description="Ed25519 signature")


class SchemaVersion(BaseModel):
    """Schema version model."""

    schema_id: str = Field(..., description="Schema identifier (UUID)")
    version: str = Field(..., description="Version string")
    schema_definition: Dict[str, Any] = Field(..., description="Schema definition")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    created_by: str = Field(..., description="Creator identifier (UUID)")


class ContractViolation(BaseModel):
    """Contract violation model."""

    contract_id: str = Field(..., description="Contract identifier (UUID)")
    field: str = Field(..., description="Violated field")
    rule_type: str = Field(..., description="Rule type")
    message: str = Field(..., description="Violation message")
    severity: str = Field(..., description="Severity", pattern="^(strict|warning|advisory)$")


class AnalyticsMetrics(BaseModel):
    """Analytics metrics model."""

    validation_requests: int = Field(..., description="Number of validation requests", ge=0)
    validation_success_rate: float = Field(..., description="Validation success rate", ge=0.0, le=1.0)
    average_validation_time_ms: float = Field(..., description="Average validation time (ms)", ge=0.0)
    unique_consumers: int = Field(..., description="Number of unique consumers", ge=0)
    contract_violations: int = Field(..., description="Number of contract violations", ge=0)


# ============================================================================
# List Response Models
# ============================================================================

class SchemaListResponse(BaseModel):
    """Schema list response model."""

    schemas: List[SchemaMetadata] = Field(..., description="List of schemas")
    total: int = Field(..., description="Total count", ge=0)
    limit: int = Field(..., description="Limit", ge=0)
    offset: int = Field(..., description="Offset", ge=0)


class ContractListResponse(BaseModel):
    """Contract list response model."""

    contracts: List[ContractDefinition] = Field(..., description="List of contracts")
    total: int = Field(..., description="Total count", ge=0)
    limit: int = Field(..., description="Limit", ge=0)
    offset: int = Field(..., description="Offset", ge=0)


class VersionListResponse(BaseModel):
    """Version list response model."""

    versions: List[SchemaMetadata] = Field(..., description="List of versions")
    total: int = Field(..., description="Total count", ge=0)


class TemplateListResponse(BaseModel):
    """Template list response model."""

    templates: List[TemplateResponse] = Field(..., description="List of templates")
