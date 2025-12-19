"""
API routes for Contracts & Schema Registry (EPC-12).

What: FastAPI route handlers for all endpoints per PRD v1.2.0
Why: Provides HTTP API endpoints for schema and contract operations
Reads/Writes: Reads HTTP request bodies, writes HTTP responses
Contracts: PRD API contract, error envelope per spec
Risks: Input validation failures, service unavailability, error message exposure
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Depends, Request, status, Query
from fastapi.responses import Response

from .models import (
    RegisterSchemaRequest, UpdateSchemaRequest, ValidateDataRequest,
    CheckCompatibilityRequest, TransformDataRequest, CreateContractRequest,
    UpdateContractRequest, BulkRegisterSchemasRequest, BulkValidateRequest,
    CreateTemplateRequest, InstantiateTemplateRequest,
    SchemaMetadata, ContractDefinition, ValidationResult, CompatibilityResult,
    TransformationResult, BulkOperationResponse, TemplateResponse,
    SchemaListResponse, ContractListResponse, VersionListResponse,
    TemplateListResponse, HealthResponse, MetricsResponse, ConfigResponse,
    ErrorResponse
)
from .services import (
    SchemaService, ValidationService, ContractService,
    CompatibilityService, TransformationService
)
from .errors import ErrorCode, create_error_response, get_http_status
from .dependencies import MockM21IAM  # EPC-1 (Identity & Access Management) - legacy class name
from .services import _metrics_collector
from .templates.manager import TemplateManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service instances
_schema_service: Optional[SchemaService] = None
_validation_service: Optional[ValidationService] = None
_contract_service: Optional[ContractService] = None
_compatibility_service: Optional[CompatibilityService] = None
_transformation_service: Optional[TransformationService] = None
_iam: Optional[MockM21IAM] = None


def get_schema_service() -> SchemaService:
    """Get SchemaService instance."""
    global _schema_service
    if _schema_service is None:
        _schema_service = SchemaService()
    return _schema_service


def get_validation_service() -> ValidationService:
    """Get ValidationService instance."""
    global _validation_service
    if _validation_service is None:
        _validation_service = ValidationService()
    return _validation_service


def get_contract_service() -> ContractService:
    """Get ContractService instance."""
    global _contract_service
    if _contract_service is None:
        _contract_service = ContractService()
    return _contract_service


def get_compatibility_service() -> CompatibilityService:
    """Get CompatibilityService instance."""
    global _compatibility_service
    if _compatibility_service is None:
        _compatibility_service = CompatibilityService()
    return _compatibility_service


def get_transformation_service() -> TransformationService:
    """Get TransformationService instance."""
    global _transformation_service
    if _transformation_service is None:
        _transformation_service = TransformationService()
    return _transformation_service


def get_tenant_context(request: Request) -> Dict[str, str]:
    """Extract tenant context from request."""
    return {
        "tenant_id": getattr(request.state, "tenant_id", "dev-tenant"),
        "user_id": getattr(request.state, "user_id", "unknown"),
        "module_id": getattr(request.state, "module_id", "M34")
    }


# Health & Metrics Endpoints

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    from .database.connection import health_check as db_health_check
    db_health = db_health_check()

    checks = [
        {"name": "service", "status": "pass", "detail": "Service is running"},
        {"name": "database", "status": "pass" if db_health["connected"] else "fail", "detail": db_health.get("error", "Database connected")}
    ]

    overall_status = "healthy"
    if any(c["status"] == "fail" for c in checks):
        overall_status = "unhealthy"
    elif any(c["status"] == "warn" for c in checks):
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        checks=checks
    )


@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe."""
    from .database.connection import health_check as db_health_check
    db_health = db_health_check()
    if not db_health["connected"]:
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Prometheus metrics endpoint."""
    metrics = _metrics_collector.get_metrics()
    return MetricsResponse(
        schema_validation_count=metrics["schema_validation_count"],
        contract_enforcement_count=metrics["contract_enforcement_count"],
        compatibility_check_count=metrics["compatibility_check_count"],
        schema_registration_count=metrics["schema_registration_count"],
        average_validation_latency_ms=metrics["average_validation_latency_ms"],
        average_contract_latency_ms=metrics["average_contract_latency_ms"],
        average_compatibility_latency_ms=metrics["average_compatibility_latency_ms"],
        cache_hit_rate=metrics["cache_hit_rate"],
        error_rate=metrics["error_rate"],
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get effective configuration."""
    return ConfigResponse(
        module_id="EPC-12",
        version="1.2.0",
        api_endpoints={
            "health": "/registry/v1/health",
            "metrics": "/registry/v1/metrics",
            "config": "/registry/v1/config",
            "schemas": "/registry/v1/schemas",
            "contracts": "/registry/v1/contracts",
            "validate": "/registry/v1/validate",
            "compatibility": "/registry/v1/compatibility",
            "transform": "/registry/v1/transform",
            "versions": "/registry/v1/versions",
            "templates": "/registry/v1/templates",
            "bulk": "/registry/v1/bulk"
        },
        performance_requirements={
            "schema_validation_ms_max": 100,
            "contract_enforcement_ms_max": 50,
            "schema_registration_ms_max": 200,
            "compatibility_check_ms_max": 150
        },
        timestamp=datetime.utcnow().isoformat()
    )


# Schema Management Endpoints

@router.get("/schemas", response_model=SchemaListResponse)
async def list_schemas(
    tenant_id: Optional[str] = Query(None),
    namespace: Optional[str] = Query(None),
    schema_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    request: Request = None,
    service: SchemaService = Depends(get_schema_service)
):
    """List schemas with filters."""
    context = get_tenant_context(request)
    tenant_id = tenant_id or context["tenant_id"]

    schemas, total = service.list_schemas(
        tenant_id=tenant_id,
        namespace=namespace,
        schema_type=schema_type,
        status=status,
        limit=limit,
        offset=offset
    )

    return SchemaListResponse(
        schemas=schemas,
        total=total,
        limit=limit,
        offset=offset
    )


@router.post("/schemas", response_model=SchemaMetadata, status_code=201)
async def register_schema(
    request_data: RegisterSchemaRequest,
    request: Request = None,
    service: SchemaService = Depends(get_schema_service)
):
    """Register a new schema."""
    context = get_tenant_context(request)

    try:
        schema = service.register_schema(
            request_data.model_dump(),
            context["tenant_id"],
            context["user_id"]
        )
        return schema
    except ValueError as e:
        error_response = create_error_response(
            ErrorCode.INVALID_SCHEMA_DEFINITION,
            str(e),
            tenant_id=context["tenant_id"]
        )
        raise HTTPException(
            status_code=get_http_status(ErrorCode.INVALID_SCHEMA_DEFINITION),
            detail=error_response.model_dump()
        )


@router.get("/schemas/{schema_id}", response_model=SchemaMetadata)
async def get_schema(
    schema_id: str,
    version: Optional[str] = Query(None),
    request: Request = None,
    service: SchemaService = Depends(get_schema_service)
):
    """Get schema by ID."""
    context = get_tenant_context(request)

    try:
        schema = service.get_schema(schema_id, context["tenant_id"], version)
    except ValueError as exc:
        error_response = create_error_response(
            ErrorCode.SCHEMA_NOT_FOUND,
            str(exc),
            tenant_id=context["tenant_id"]
        )
        raise HTTPException(
            status_code=get_http_status(ErrorCode.SCHEMA_NOT_FOUND),
            detail=error_response.model_dump()
        )
    if not schema:
        error_response = create_error_response(
            ErrorCode.SCHEMA_NOT_FOUND,
            tenant_id=context["tenant_id"]
        )
        raise HTTPException(
            status_code=get_http_status(ErrorCode.SCHEMA_NOT_FOUND),
            detail=error_response.model_dump()
        )

    return schema


@router.put("/schemas/{schema_id}", response_model=SchemaMetadata)
async def update_schema(
    schema_id: str,
    request_data: UpdateSchemaRequest,
    request: Request = None,
    service: SchemaService = Depends(get_schema_service)
):
    """Update schema (creates new version)."""
    context = get_tenant_context(request)

    try:
        schema = service.update_schema(
            schema_id,
            request_data.model_dump(),
            context["tenant_id"],
            context["user_id"]
        )
        return schema
    except ValueError as e:
        error_response = create_error_response(
            ErrorCode.SCHEMA_NOT_FOUND,
            str(e),
            tenant_id=context["tenant_id"]
        )
        raise HTTPException(
            status_code=get_http_status(ErrorCode.SCHEMA_NOT_FOUND),
            detail=error_response.model_dump()
        )


@router.delete("/schemas/{schema_id}", status_code=204)
async def delete_schema(
    schema_id: str,
    force: bool = Query(False),
    request: Request = None,
    service: SchemaService = Depends(get_schema_service)
):
    """Deprecate or delete schema."""
    context = get_tenant_context(request)

    try:
        service.deprecate_schema(schema_id, context["tenant_id"])
        return Response(status_code=204)
    except Exception as e:
        error_response = create_error_response(
            ErrorCode.SCHEMA_NOT_FOUND,
            str(e),
            tenant_id=context["tenant_id"]
        )
        raise HTTPException(
            status_code=get_http_status(ErrorCode.SCHEMA_NOT_FOUND),
            detail=error_response.model_dump()
        )


@router.get("/schemas/{schema_id}/versions", response_model=VersionListResponse)
async def list_schema_versions(
    schema_id: str,
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    request: Request = None,
    service: SchemaService = Depends(get_schema_service)
):
    """List all versions of a schema."""
    context = get_tenant_context(request)

    # Get all versions (simplified - should query versions table)
    schemas, total = service.list_schemas(
        tenant_id=context["tenant_id"],
        limit=limit,
        offset=offset
    )

    # Filter by schema name (simplified)
    versions = [s for s in schemas if str(s.schema_id) == schema_id]

    return VersionListResponse(versions=versions, total=len(versions))


# Contract Management Endpoints

@router.get("/contracts", response_model=ContractListResponse)
async def list_contracts(
    tenant_id: Optional[str] = Query(None),
    schema_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    request: Request = None,
    service: ContractService = Depends(get_contract_service)
):
    """List contracts with filters."""
    context = get_tenant_context(request)
    tenant_id = tenant_id or context["tenant_id"]

    contracts, total = service.list_contracts(
        tenant_id=tenant_id,
        schema_id=schema_id,
        contract_type=type,
        limit=limit,
        offset=offset
    )

    return ContractListResponse(
        contracts=contracts,
        total=total,
        limit=limit,
        offset=offset
    )


@router.post("/contracts", response_model=ContractDefinition, status_code=201)
async def create_contract(
    request_data: CreateContractRequest,
    request: Request = None,
    service: ContractService = Depends(get_contract_service)
):
    """Create a new contract."""
    context = get_tenant_context(request)

    try:
        contract = service.create_contract(
            request_data.model_dump(),
            context["tenant_id"],
            context["user_id"]
        )
        return contract
    except ValueError as e:
        error_response = create_error_response(
            ErrorCode.SCHEMA_NOT_FOUND,
            str(e),
            tenant_id=context["tenant_id"]
        )
        raise HTTPException(
            status_code=get_http_status(ErrorCode.SCHEMA_NOT_FOUND),
            detail=error_response.model_dump()
        )


@router.get("/contracts/{contract_id}", response_model=ContractDefinition)
async def get_contract(
    contract_id: str,
    request: Request = None,
    service: ContractService = Depends(get_contract_service)
):
    """Get contract by ID."""
    context = get_tenant_context(request)

    contract = service.get_contract(contract_id, context["tenant_id"])
    if not contract:
        error_response = create_error_response(
            ErrorCode.CONTRACT_NOT_FOUND,
            tenant_id=context["tenant_id"]
        )
        raise HTTPException(
            status_code=get_http_status(ErrorCode.CONTRACT_NOT_FOUND),
            detail=error_response.model_dump()
        )

    return contract


# Validation Endpoint

@router.post("/validate", response_model=ValidationResult)
async def validate_data(
    request_data: ValidateDataRequest,
    request: Request = None,
    service: ValidationService = Depends(get_validation_service)
):
    """Validate data against schema."""
    context = get_tenant_context(request)

    result = service.validate_data(
        request_data.schema_id,
        request_data.data,
        context["tenant_id"],
        request_data.version
    )

    return result


# Compatibility & Transformation Endpoints

@router.post("/compatibility", response_model=CompatibilityResult)
async def check_compatibility(
    request_data: CheckCompatibilityRequest,
    service: CompatibilityService = Depends(get_compatibility_service)
):
    """Check schema compatibility."""
    result = service.check_compatibility(
        request_data.source_schema,
        request_data.target_schema,
        request_data.compatibility_mode or "backward"
    )

    return result


@router.post("/transform", response_model=TransformationResult)
async def transform_data(
    request_data: TransformDataRequest,
    request: Request = None,
    service: TransformationService = Depends(get_transformation_service)
):
    """Transform data between schema versions."""
    context = get_tenant_context(request)

    try:
        result = service.transform_data(
            request_data.source_schema_id,
            request_data.target_schema_id,
            request_data.data,
            context["tenant_id"],
            request_data.source_version,
            request_data.target_version
        )
        return result
    except ValueError as e:
        error_response = create_error_response(
            ErrorCode.SCHEMA_NOT_FOUND,
            str(e),
            tenant_id=context["tenant_id"]
        )
        raise HTTPException(
            status_code=get_http_status(ErrorCode.SCHEMA_NOT_FOUND),
            detail=error_response.model_dump()
        )


# Version Management Endpoints

@router.get("/versions", response_model=VersionListResponse)
async def list_versions(
    tenant_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    request: Request = None,
    service: SchemaService = Depends(get_schema_service)
):
    """List all schema versions across all schemas."""
    context = get_tenant_context(request)
    tenant_id = tenant_id or context["tenant_id"]

    schemas, total = service.list_schemas(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset
    )

    return VersionListResponse(versions=schemas, total=total)


# Template Endpoints (simplified - full implementation in templates module)

@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    pattern: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=100)
):
    """List available schema templates."""
    template_manager = TemplateManager()
    templates = template_manager.list_templates(pattern=pattern)

    # Apply limit
    if limit < len(templates):
        templates = templates[:limit]

    return TemplateListResponse(templates=templates)


# Bulk Operations Endpoints

@router.post("/bulk/schemas", response_model=BulkOperationResponse, status_code=202)
async def bulk_register_schemas(
    request_data: BulkRegisterSchemasRequest,
    request: Request = None,
    service: SchemaService = Depends(get_schema_service)
):
    """Bulk schema registration."""
    context = get_tenant_context(request)
    operation_id = str(uuid.uuid4())

    # Process schemas synchronously (in production, this would be async)
    succeeded = 0
    failed = 0
    errors = []

    for schema_data in request_data.schemas:
        try:
            if not request_data.validate_only:
                service.register_schema(
                    schema_data,
                    context["tenant_id"],
                    context["user_id"]
                )
            succeeded += 1
        except Exception as e:
            failed += 1
            errors.append({
                "schema": schema_data.get("name", "unknown"),
                "error": str(e)
            })
            logger.error(f"Bulk schema registration failed: {e}")

    return BulkOperationResponse(
        operation_id=operation_id,
        status="completed" if failed == 0 else "partial",
        total_items=len(request_data.schemas),
        succeeded=succeeded,
        failed=failed
    )


@router.post("/bulk/validate", response_model=BulkOperationResponse, status_code=202)
async def bulk_validate(
    request_data: BulkValidateRequest,
    request: Request = None,
    service: ValidationService = Depends(get_validation_service)
):
    """Bulk data validation."""
    context = get_tenant_context(request)
    operation_id = str(uuid.uuid4())

    # Process validations synchronously (in production, this would be async)
    succeeded = 0
    failed = 0

    for validation in request_data.validations:
        try:
            result = service.validate_data(
                validation["schema_id"],
                validation["data"],
                context["tenant_id"],
                validation.get("version")
            )
            if result.valid:
                succeeded += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            logger.error(f"Bulk validation failed: {e}")

    return BulkOperationResponse(
        operation_id=operation_id,
        status="completed" if failed == 0 else "partial",
        total_items=len(request_data.validations),
        succeeded=succeeded,
        failed=failed
    )


@router.get("/bulk/export")
async def bulk_export(
    tenant_id: Optional[str] = Query(None),
    format: str = Query("jsonl", pattern="^(jsonl|json)$"),
    compression: str = Query("gzip", pattern="^(gzip|none)$"),
    request: Request = None,
    service: SchemaService = Depends(get_schema_service)
):
    """Export schemas in bulk."""
    context = get_tenant_context(request)
    tenant_id = tenant_id or context["tenant_id"]

    # Get all schemas for tenant
    schemas, total = service.list_schemas(
        tenant_id=tenant_id,
        limit=10000,  # Large limit for export
        offset=0
    )

    # Convert to export format
    export_data = []
    for schema in schemas:
        export_data.append(schema.model_dump())

    # Format response based on requested format
    if format == "jsonl":
        # JSONL format: one JSON object per line
        import json
        lines = [json.dumps(schema) for schema in export_data]
        content = "\n".join(lines)
        media_type = "application/x-ndjson"
    else:
        # JSON format: array of objects
        import json
        content = json.dumps(export_data, indent=2)
        media_type = "application/json"

    # Apply compression if requested (simplified - in production would use actual compression)
    if compression == "gzip":
        import gzip
        import io
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb') as f:
            f.write(content.encode('utf-8'))
        content_bytes = buffer.getvalue()
        return Response(
            content=content_bytes,
            media_type=media_type,
            headers={
                "Content-Encoding": "gzip",
                "Content-Disposition": f"attachment; filename=schemas_export.{format}.gz"
            }
        )
    else:
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename=schemas_export.{format}"
            }
        )
