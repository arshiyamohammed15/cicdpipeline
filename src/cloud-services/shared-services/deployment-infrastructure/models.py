"""
Pydantic models for Deployment & Infrastructure (EPC-8) service.

What: Defines Pydantic v2 models for request/response validation per deployment API contract
Why: Ensures type safety, input validation, and standardized API contracts
Reads/Writes: Reads request data, writes response data (no file I/O)
Contracts: Deployment API contract, error envelope per Rule 4171
Risks: Model validation failures may expose internal error details if not handled properly
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class DeployRequest(BaseModel):
    """Request model for deployment operation."""

    environment: str = Field(..., description="Target environment", pattern="^(development|staging|production)$")
    target: str = Field(..., description="Deployment target", pattern="^(local|cloud|hybrid)$")
    service: Optional[str] = Field(default=None, description="Specific service to deploy (optional)")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Deployment configuration overrides")


class DeployResponse(BaseModel):
    """Response model for deployment operation."""

    deployment_id: str = Field(..., description="Deployment identifier")
    status: str = Field(..., description="Deployment status", pattern="^(pending|in_progress|completed|failed)$")
    environment: str = Field(..., description="Target environment")
    target: str = Field(..., description="Deployment target")
    started_at: datetime = Field(..., description="Deployment start time (ISO 8601)")
    estimated_completion: Optional[datetime] = Field(default=None, description="Estimated completion time")


class EnvironmentParityRequest(BaseModel):
    """Request model for environment parity verification."""

    source_environment: str = Field(..., description="Source environment", pattern="^(development|staging|production)$")
    target_environment: str = Field(..., description="Target environment", pattern="^(development|staging|production)$")
    check_resources: Optional[List[str]] = Field(default=None, description="Specific resources to check (optional)")


class EnvironmentParityResponse(BaseModel):
    """Response model for environment parity verification."""

    source_environment: str = Field(..., description="Source environment")
    target_environment: str = Field(..., description="Target environment")
    parity_status: str = Field(..., description="Parity status", pattern="^(match|mismatch|partial)$")
    differences: List[Dict[str, Any]] = Field(default_factory=list, description="List of differences found")
    checked_at: datetime = Field(..., description="Check timestamp (ISO 8601)")


class InfrastructureStatusRequest(BaseModel):
    """Request model for infrastructure status check."""

    environment: Optional[str] = Field(default=None, description="Environment to check (optional)")
    resource_type: Optional[str] = Field(default=None, description="Resource type to check (optional)")


class InfrastructureStatusResponse(BaseModel):
    """Response model for infrastructure status check."""

    environment: str = Field(..., description="Environment")
    resources: List[Dict[str, Any]] = Field(..., description="List of infrastructure resources")
    status_summary: Dict[str, int] = Field(..., description="Status summary by resource state")
    checked_at: datetime = Field(..., description="Check timestamp (ISO 8601)")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status", pattern="^(healthy|unhealthy|degraded)$")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Environment")
    timestamp: datetime = Field(..., description="Check timestamp (ISO 8601)")


class ErrorDetail(BaseModel):
    """Error detail model per Rule 4171."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Error response model per Rule 4171."""

    error: ErrorDetail = Field(..., description="Error information")
