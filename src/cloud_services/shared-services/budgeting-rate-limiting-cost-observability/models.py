"""
Pydantic models for Budgeting, Rate-Limiting & Cost Observability (EPC-13).

What: Defines Pydantic v2 models for request/response validation per PRD v3.0.0
Why: Ensures type safety, input validation, and standardized API contracts
Reads/Writes: Reads request data, writes response data (no file I/O)
Contracts: EPC-13 API contract (all endpoints), receipt schemas per PRD
Risks: Model validation failures may expose internal error details if not handled properly
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Health & Metrics Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response model per PRD."""

    status: str = Field(..., description="Service status", pattern="^(UP|DOWN|DEGRADED)$")
    version: str = Field(..., description="Module version")
    timestamp: str = Field(..., description="Health check timestamp (ISO 8601)")
    dependencies: Dict[str, Dict[str, Any]] = Field(..., description="Dependency health status")
    degraded_reasons: List[str] = Field(default_factory=list, description="Reasons for degraded status")


class MetricsResponse(BaseModel):
    """Metrics snapshot response model."""

    metrics: str = Field(..., description="Metrics in ZeroUI-standard / OpenTelemetry-compatible format")


# ============================================================================
# Error Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response model per PRD (lines 695-715)."""

    error_code: str = Field(
        ...,
        description="Error code",
        pattern="^(BUDGET_EXCEEDED|RATE_LIMIT_VIOLATED|QUOTA_EXHAUSTED|COST_CALCULATION_ERROR|VALIDATION_ERROR|NOT_FOUND|UNAUTHORIZED|FORBIDDEN|INTERNAL_ERROR)$"
    )
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    correlation_id: str = Field(..., description="Correlation ID (UUID)")
    retriable: Optional[bool] = Field(default=False, description="Whether request is retriable")
    suggested_action: Optional[str] = Field(default=None, description="Suggested action")
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier (UUID)")


# ============================================================================
# Pagination Models
# ============================================================================

class PaginationMeta(BaseModel):
    """Pagination metadata model per PRD (lines 717-734)."""

    page: int = Field(..., description="Page number", ge=1)
    page_size: int = Field(..., description="Items per page", ge=1, le=1000)
    total_count: int = Field(..., description="Total number of items", ge=0)
    total_pages: Optional[int] = Field(default=None, description="Total number of pages")
    next_page_token: Optional[str] = Field(default=None, description="Token for next page")
    prev_page_token: Optional[str] = Field(default=None, description="Token for previous page")


# ============================================================================
# Alert Models
# ============================================================================

class Alert(BaseModel):
    """Alert model per PRD (lines 736-774)."""

    alert_id: str = Field(..., description="Alert identifier (UUID)")
    alert_type: str = Field(
        ...,
        description="Alert type",
        pattern="^(budget_threshold_exceeded|rate_limit_violated|cost_anomaly_detected|quota_exhausted)$"
    )
    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    severity: str = Field(..., description="Severity", pattern="^(info|warning|critical)$")
    status: str = Field(..., description="Status", pattern="^(active|acknowledged|resolved)$")
    title: Optional[str] = Field(default=None, description="Alert title")
    message: Optional[str] = Field(default=None, description="Alert message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Alert details")
    resource_id: Optional[str] = Field(default=None, description="Resource identifier (UUID)")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    acknowledged_at: Optional[str] = Field(default=None, description="Acknowledgment timestamp (ISO 8601)")
    resolved_at: Optional[str] = Field(default=None, description="Resolution timestamp (ISO 8601)")


# ============================================================================
# Budget Models
# ============================================================================

class BudgetDefinition(BaseModel):
    """Budget Definition model per PRD (lines 776-844)."""

    budget_id: str = Field(..., description="Budget identifier (UUID)")
    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    budget_name: str = Field(..., description="Budget name", max_length=255)
    budget_type: str = Field(..., description="Budget type", pattern="^(tenant|project|user|feature)$")
    budget_amount: Decimal = Field(..., description="Budget amount", ge=0)
    currency: str = Field(default="USD", description="Currency code", pattern="^[A-Z]{3}$")
    period_type: str = Field(..., description="Period type", pattern="^(monthly|quarterly|yearly|custom)$")
    start_date: str = Field(..., description="Start date (ISO 8601)")
    end_date: Optional[str] = Field(default=None, description="End date (ISO 8601)")
    allocated_to_type: str = Field(..., description="Allocated to type", pattern="^(tenant|project|user|feature)$")
    allocated_to_id: str = Field(..., description="Allocated to identifier (UUID)")
    enforcement_action: str = Field(..., description="Enforcement action", pattern="^(hard_stop|soft_limit|throttle|escalate)$")
    thresholds: Optional[Dict[str, Any]] = Field(default=None, description="Threshold configuration")
    notifications: Optional[Dict[str, Any]] = Field(default=None, description="Notification configuration")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp (ISO 8601)")
    created_by: Optional[str] = Field(default=None, description="Creator identifier (UUID)")


class CheckBudgetRequest(BaseModel):
    """Request model for budget check per PRD (lines 866-883)."""

    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    resource_type: str = Field(..., description="Resource type")
    estimated_cost: Decimal = Field(..., description="Estimated cost", ge=0)
    operation_context: Optional[Dict[str, Any]] = Field(default=None, description="Operation context")
    allocated_to_type: Optional[str] = Field(default=None, description="Allocated to type", pattern="^(tenant|project|user|feature)$")
    allocated_to_id: Optional[str] = Field(default=None, description="Allocated to identifier (UUID)")


class CheckBudgetResponse(BaseModel):
    """Response model for budget check per PRD (lines 896-916)."""

    allowed: bool = Field(..., description="Whether operation is allowed")
    remaining_budget: Decimal = Field(..., description="Remaining budget amount")
    budget_id: str = Field(..., description="Budget identifier (UUID)")
    enforcement_action: Optional[str] = Field(default=None, description="Enforcement action", pattern="^(hard_stop|soft_limit|throttle|escalate)$")
    message: Optional[str] = Field(default=None, description="Status message")
    utilization_ratio: Optional[float] = Field(default=None, description="Budget utilization ratio", ge=0, le=1)
    requires_approval: Optional[bool] = Field(default=False, description="Whether an approval workflow is required")
    approval_id: Optional[str] = Field(default=None, description="Approval request identifier (UUID)")
    correlation_id: str = Field(..., description="Correlation ID (UUID)")


# ============================================================================
# Rate Limit Models
# ============================================================================

class RateLimitPolicy(BaseModel):
    """Rate Limit Policy model per PRD (lines 846-882)."""

    policy_id: str = Field(..., description="Policy identifier (UUID)")
    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    scope_type: str = Field(..., description="Scope type", pattern="^(tenant|user|project|feature)$")
    scope_id: str = Field(..., description="Scope identifier (UUID)")
    resource_type: str = Field(..., description="Resource type")
    limit_value: int = Field(..., description="Limit value", ge=1)
    time_window_seconds: int = Field(..., description="Time window in seconds", ge=1)
    algorithm: str = Field(..., description="Algorithm", pattern="^(token_bucket|leaky_bucket|fixed_window|sliding_window_log)$")
    burst_capacity: Optional[int] = Field(default=None, description="Burst capacity", ge=0)
    overrides: Optional[Dict[str, Any]] = Field(default=None, description="Policy overrides")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp (ISO 8601)")


class CheckRateLimitRequest(BaseModel):
    """Request model for rate limit check per PRD (lines 1177-1187)."""

    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    resource_type: str = Field(..., description="Resource type")
    request_count: int = Field(default=1, description="Request count", ge=1)
    priority: Optional[str] = Field(default=None, description="Request priority", pattern="^(low|normal|high|critical)$")
    resource_key: Optional[str] = Field(default=None, description="Resource key")


class CheckRateLimitResponse(BaseModel):
    """Response model for rate limit check per PRD (lines 1189-1208)."""

    allowed: bool = Field(..., description="Whether request is allowed")
    remaining_requests: int = Field(..., description="Remaining requests in window")
    reset_time: str = Field(..., description="Reset time (ISO 8601)")
    limit_value: Optional[int] = Field(default=None, description="Limit value")
    retry_after: Optional[int] = Field(default=None, description="Retry after seconds")
    policy_id: Optional[str] = Field(default=None, description="Policy identifier (UUID)")
    correlation_id: str = Field(..., description="Correlation ID (UUID)")


# ============================================================================
# Cost Tracking Models
# ============================================================================

class CostRecord(BaseModel):
    """Cost Record model per PRD (lines 656-700)."""

    cost_id: str = Field(..., description="Cost record identifier (UUID)")
    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    resource_id: str = Field(..., description="Resource identifier (UUID)")
    resource_type: str = Field(..., description="Resource type")
    cost_amount: Decimal = Field(..., description="Cost amount", ge=0)
    currency: str = Field(default="USD", description="Currency code", pattern="^[A-Z]{3}$")
    usage_quantity: Optional[Decimal] = Field(default=None, description="Usage quantity")
    usage_unit: Optional[str] = Field(default=None, description="Usage unit")
    timestamp: str = Field(..., description="Timestamp (ISO 8601)")
    attributed_to_type: str = Field(..., description="Attributed to type", pattern="^(tenant|user|project|feature)$")
    attributed_to_id: str = Field(..., description="Attributed to identifier (UUID)")
    service_name: str = Field(..., description="Service name")
    region: Optional[str] = Field(default=None, description="Region")
    tags: Optional[Dict[str, Any]] = Field(default=None, description="Tags")


class RecordCostRequest(BaseModel):
    """Request model for cost recording per PRD (lines 1438-1451)."""

    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    resource_type: str = Field(..., description="Resource type")
    cost_amount: Decimal = Field(..., description="Cost amount", ge=0)
    usage_quantity: Decimal = Field(..., description="Usage quantity")
    usage_unit: Optional[str] = Field(default=None, description="Usage unit")
    resource_id: Optional[str] = Field(default=None, description="Resource identifier (UUID)")
    service_name: Optional[str] = Field(default=None, description="Service name")
    attributed_to_type: Optional[str] = Field(default=None, description="Attributed to type", pattern="^(tenant|user|project|feature)$")
    attributed_to_id: Optional[str] = Field(default=None, description="Attributed to identifier (UUID)")
    region: Optional[str] = Field(default=None, description="Region")
    tags: Optional[Dict[str, Any]] = Field(default=None, description="Tags")


class RecordCostResponse(BaseModel):
    """Response model for cost recording per PRD (lines 1463-1468)."""

    record_id: str = Field(..., description="Record identifier (UUID)")
    recorded_at: str = Field(..., description="Recording timestamp (ISO 8601)")
    correlation_id: str = Field(..., description="Correlation ID (UUID)")


class CostReportRequest(BaseModel):
    """Request model for cost report generation per PRD (lines 1603-1633)."""

    report_type: str = Field(
        ...,
        description="Report type",
        pattern="^(summary|detailed|by_resource|by_service|by_user|by_feature|by_time_period)$"
    )
    start_time: str = Field(..., description="Start time (ISO 8601)")
    end_time: str = Field(..., description="End time (ISO 8601)")
    group_by: Optional[List[str]] = Field(default=None, description="Group by dimensions")
    format: Optional[str] = Field(default="json", description="Report format", pattern="^(json|csv)$")


class CostReportResponse(BaseModel):
    """Response model for cost report per PRD (lines 1645-1654)."""

    report_id: str = Field(..., description="Report identifier (UUID)")
    report_type: str = Field(..., description="Report type")
    period: Dict[str, str] = Field(..., description="Time period")
    total_cost: Decimal = Field(..., description="Total cost")
    currency: str = Field(..., description="Currency code")
    breakdown: Optional[List[Dict[str, Any]]] = Field(default=None, description="Cost breakdown")
    correlation_id: str = Field(..., description="Correlation ID (UUID)")


# ============================================================================
# Quota Models
# ============================================================================

class QuotaAllocation(BaseModel):
    """Quota Allocation model per PRD (lines 884-919)."""

    quota_id: str = Field(..., description="Quota identifier (UUID)")
    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    resource_type: str = Field(..., description="Resource type")
    allocated_amount: Decimal = Field(..., description="Allocated amount", ge=0)
    used_amount: Decimal = Field(default=0, description="Used amount", ge=0)
    period_start: str = Field(..., description="Period start (ISO 8601)")
    period_end: str = Field(..., description="Period end (ISO 8601)")
    allocation_type: str = Field(..., description="Allocation type", pattern="^(tenant|project|user|feature)$")
    max_burst_amount: Optional[Decimal] = Field(default=None, description="Max burst amount", ge=0)
    auto_renew: bool = Field(default=True, description="Auto renew flag")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp (ISO 8601)")


class AllocateQuotaRequest(BaseModel):
    """Request model for quota allocation per PRD (lines 1680-1690)."""

    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    resource_type: str = Field(..., description="Resource type")
    allocated_amount: Decimal = Field(..., description="Allocated amount", ge=0)
    period_start: str = Field(..., description="Period start (ISO 8601)")
    period_end: str = Field(..., description="Period end (ISO 8601)")
    allocation_type: str = Field(..., description="Allocation type", pattern="^(tenant|project|user|feature)$")
    max_burst_amount: Optional[Decimal] = Field(default=None, description="Max burst amount", ge=0)
    auto_renew: bool = Field(default=True, description="Auto renew flag")


class AllocateQuotaResponse(BaseModel):
    """Response model for quota allocation per PRD (lines 1702-1707)."""

    quota_id: str = Field(..., description="Quota identifier (UUID)")
    allocated_at: str = Field(..., description="Allocation timestamp (ISO 8601)")
    correlation_id: str = Field(..., description="Correlation ID (UUID)")


# ============================================================================
# Batch Operation Models
# ============================================================================

class BatchCostRecord(BaseModel):
    """Single cost record in batch request."""

    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    resource_type: str = Field(..., description="Resource type")
    cost_amount: Decimal = Field(..., description="Cost amount", ge=0)
    usage_quantity: Decimal = Field(..., description="Usage quantity")
    usage_unit: Optional[str] = Field(default=None, description="Usage unit")
    resource_id: Optional[str] = Field(default=None, description="Resource identifier (UUID)")
    service_name: Optional[str] = Field(default=None, description="Service name")
    attributed_to_type: Optional[str] = Field(default=None, description="Attributed to type", pattern="^(tenant|user|project|feature)$")
    attributed_to_id: Optional[str] = Field(default=None, description="Attributed to identifier (UUID)")
    region: Optional[str] = Field(default=None, description="Region")
    tags: Optional[Dict[str, Any]] = Field(default=None, description="Tags")
    idempotency_key: str = Field(..., description="Idempotency key (UUID)")


class RecordCostBatchRequest(BaseModel):
    """Request model for batch cost recording per PRD (lines 2433-2455)."""

    records: List[BatchCostRecord] = Field(..., description="Cost records", min_length=1, max_length=1000)


class RecordCostBatchResponse(BaseModel):
    """Response model for batch cost recording per PRD (lines 2467-2474)."""

    batch_id: str = Field(..., description="Batch identifier (UUID)")
    processed_count: int = Field(..., description="Number of processed records", ge=0)
    failed_count: int = Field(..., description="Number of failed records", ge=0)
    failures: Optional[List[Dict[str, Any]]] = Field(default=None, description="Failure details")
    correlation_id: str = Field(..., description="Correlation ID (UUID)")


class BatchBudgetCheck(BaseModel):
    """Single budget check in batch request."""

    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    resource_type: str = Field(..., description="Resource type")
    estimated_cost: Decimal = Field(..., description="Estimated cost", ge=0)
    operation_context: Optional[Dict[str, Any]] = Field(default=None, description="Operation context")
    allocated_to_type: Optional[str] = Field(default=None, description="Allocated to type", pattern="^(tenant|project|user|feature)$")
    allocated_to_id: Optional[str] = Field(default=None, description="Allocated to identifier (UUID)")


class CheckBudgetBatchRequest(BaseModel):
    """Request model for batch budget check per PRD (lines 2503-2519)."""

    checks: List[BatchBudgetCheck] = Field(..., description="Budget checks", min_length=1, max_length=500)


class CheckBudgetBatchResponse(BaseModel):
    """Response model for batch budget check per PRD (lines 2531-2545)."""

    results: List[Dict[str, Any]] = Field(..., description="Budget check results")
    correlation_id: str = Field(..., description="Correlation ID (UUID)")


class BatchQuotaAllocation(BaseModel):
    """Single quota allocation in batch request."""

    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    resource_type: str = Field(..., description="Resource type")
    allocated_amount: Decimal = Field(..., description="Allocated amount", ge=0)
    period_start: str = Field(..., description="Period start (ISO 8601)")
    period_end: str = Field(..., description="Period end (ISO 8601)")
    allocation_type: str = Field(..., description="Allocation type", pattern="^(tenant|project|user|feature)$")
    max_burst_amount: Optional[Decimal] = Field(default=None, description="Max burst amount", ge=0)
    auto_renew: bool = Field(default=True, description="Auto renew flag")
    idempotency_key: str = Field(..., description="Idempotency key (UUID)")


class AllocateQuotaBatchRequest(BaseModel):
    """Request model for batch quota allocation per PRD (lines 2568-2587)."""

    allocations: List[BatchQuotaAllocation] = Field(..., description="Quota allocations", min_length=1, max_length=100)


class AllocateQuotaBatchResponse(BaseModel):
    """Response model for batch quota allocation per PRD (lines 2599-2607)."""

    batch_id: str = Field(..., description="Batch identifier (UUID)")
    successful_count: int = Field(..., description="Number of successful allocations", ge=0)
    failed_count: int = Field(..., description="Number of failed allocations", ge=0)
    quotas: Optional[List[Dict[str, Any]]] = Field(default=None, description="Successful quota allocations")
    failures: Optional[List[Dict[str, Any]]] = Field(default=None, description="Failure details")
    correlation_id: str = Field(..., description="Correlation ID (UUID)")


# ============================================================================
# Event Subscription Models
# ============================================================================

class EventSubscription(BaseModel):
    """Event subscription model."""

    subscription_id: str = Field(..., description="Subscription identifier (UUID)")
    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    event_types: List[str] = Field(..., description="Event types to subscribe to")
    webhook_url: str = Field(..., description="Webhook URL")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Event filters")
    enabled: bool = Field(default=True, description="Subscription enabled flag")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp (ISO 8601)")


class CreateEventSubscriptionRequest(BaseModel):
    """Request model for creating event subscription per PRD (lines 1949-1956)."""

    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    event_types: List[str] = Field(
        ...,
        description="Event types",
        min_length=1
    )
    webhook_url: str = Field(..., description="Webhook URL")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Event filters")
    enabled: bool = Field(default=True, description="Subscription enabled flag")


class CreateEventSubscriptionResponse(BaseModel):
    """Response model for creating event subscription per PRD (lines 1968-1973)."""

    subscription_id: str = Field(..., description="Subscription identifier (UUID)")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    correlation_id: str = Field(..., description="Correlation ID (UUID)")

