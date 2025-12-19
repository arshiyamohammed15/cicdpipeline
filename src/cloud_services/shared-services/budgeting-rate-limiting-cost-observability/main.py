"""
Main FastAPI application for Budgeting, Rate-Limiting & Cost Observability (EPC-13).

What: FastAPI application entry point with middleware, routes, and health checks per PRD v3.0.0
Why: Orchestrates service components, provides HTTP server for EPC-13 operations
Reads/Writes: Reads configuration, writes HTTP responses
Contracts: FastAPI application contract, CORS middleware, request logging middleware
Risks: Service unavailability if dependencies fail, CORS misconfiguration, middleware errors
"""

import logging
import os
import socket
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .models import HealthResponse
from .middleware import RequestLoggingMiddleware, RateLimitingMiddleware, JWTValidationMiddleware
from .dependencies import MockM21IAM

# Service metadata per PRD
SERVICE_NAME = "budgeting-rate-limiting-cost-observability"
SERVICE_VERSION = "1.0.0"
SERVICE_ENV = os.getenv("ENVIRONMENT", "development")
SERVICE_HOST = socket.gethostname()

# Configure logging per ZeroUI standards - JSON format
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)

# Initialize mock dependencies
iam = MockM21IAM()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI startup/shutdown events.

    Per M35 PRD: Service initialization, dependency health checks.
    """
    logger.info("Starting Budgeting, Rate-Limiting & Cost Observability Service...")
    logger.info(f"Service: {SERVICE_NAME}, Version: {SERVICE_VERSION}")

    # Initialize services
    logger.info("Initialized M35 services")

    yield

    logger.info("Shutting down Budgeting, Rate-Limiting & Cost Observability Service...")


app = FastAPI(
    title="ZeroUI Budgeting, Rate-Limiting & Cost Observability",
    version="1.0.0",
    description="Enterprise-grade resource budgeting, rate-limiting enforcement, and cost transparency for ZeroUI ecosystem (M35)",
    lifespan=lifespan
)

# Request logging middleware (must be first to log all requests)
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting middleware per PRD lines 3100-3118
app.add_middleware(RateLimitingMiddleware)

# JWT validation middleware per PRD
app.add_middleware(JWTValidationMiddleware, iam=iam)

# CORS middleware - configure via CORS_ORIGINS environment variable
cors_origins_env = os.getenv("CORS_ORIGINS", "*" if SERVICE_ENV == "development" else "")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",")] if cors_origins_env else []

# Production CORS validation: reject wildcard in production
if SERVICE_ENV == "production":
    if "*" in cors_origins or not cors_origins:
        logger.error("CORS_ORIGINS must be set to specific origins in production. Wildcard '*' is not allowed.")
        raise ValueError("CORS_ORIGINS must be set to specific origins in production. Wildcard '*' is not allowed.")
elif not cors_origins and SERVICE_ENV != "development":
    logger.warning("CORS_ORIGINS not set in non-development environment - CORS disabled. Set CORS_ORIGINS environment variable.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else (["*"] if SERVICE_ENV == "development" else []),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/budget/v1", tags=["budget"])


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Root health check endpoint.

    Returns:
        HealthResponse with service status
    """
    checks = [
        {"name": "service", "status": "pass", "detail": "Service is running"},
        {"name": "database", "status": "pass", "detail": "Database connectivity check (mock)"},
        {"name": "cache", "status": "pass", "detail": "Cache available (mock)"},
        {"name": "m27_audit_ledger", "status": "pass", "detail": "M27 Audit Ledger available (mock)"},
        {"name": "m31_notification_engine", "status": "pass", "detail": "M31 Notification Engine available (mock)"},
        {"name": "m33_key_management", "status": "pass", "detail": "M33 Key Management available (mock)"}
    ]

    # Determine overall status
    status = "healthy"
    if any(check["status"] == "fail" for check in checks):
        status = "unhealthy"
    elif any(check["status"] == "warn" for check in checks):
        status = "degraded"

    return HealthResponse(
        status=status,
        version=SERVICE_VERSION,
        timestamp=datetime.utcnow().isoformat(),
        dependencies={
            "database": {"status": "UP", "latency_ms": 1},
            "cache": {"status": "UP", "latency_ms": 1},
            "m27_audit_ledger": {"status": "UP", "latency_ms": 1},
            "m31_notification_engine": {"status": "UP", "latency_ms": 1},
            "m33_key_management": {"status": "UP", "latency_ms": 1}
        },
        degraded_reasons=[]
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

