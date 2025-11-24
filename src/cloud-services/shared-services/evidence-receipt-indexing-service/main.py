"""
Main FastAPI application for Evidence & Receipt Indexing Service (ERIS).

What: FastAPI application entry point with middleware, routes, and health checks
Why: Orchestrates service components, provides HTTP server for ERIS operations
Reads/Writes: Reads configuration, writes HTTP responses
Contracts: FastAPI application contract, CORS middleware
Risks: Service unavailability if dependencies fail, CORS misconfiguration
"""

import asyncio
import json
import logging
import os
import socket
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .models import HealthResponse
from .middleware import RequestLoggingMiddleware, RateLimitingMiddleware, IAMAuthMiddleware
from .database.session import SessionLocal
from .services import RetentionManagementService

# Service metadata
SERVICE_NAME = "evidence-receipt-indexing-service"
SERVICE_VERSION = "1.0.0"
SERVICE_ENV = os.getenv("ENVIRONMENT", "development")
SERVICE_HOST = socket.gethostname()

# Configure logging per Rule 173 - JSON format
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)


async def retention_re_evaluation_task():
    """
    Background task for periodic retention policy re-evaluation per FR-7.
    
    Runs daily to re-evaluate retention policies for all tenants.
    """
    # Get retention evaluation interval from environment (default: 24 hours)
    interval_hours = int(os.getenv("RETENTION_RE_EVAL_INTERVAL_HOURS", "24"))
    interval_seconds = interval_hours * 3600
    
    logger.info("Retention re-evaluation task started (interval: %d hours)", interval_hours)
    
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            
            logger.info("Starting retention policy re-evaluation...")
            db = SessionLocal()
            try:
                retention_service = RetentionManagementService(db)
                
                # Get all unique tenant IDs from receipts
                from .database.models import Receipt
                tenant_ids = db.query(Receipt.tenant_id).distinct().all()
                tenant_ids = [tid[0] for tid in tenant_ids]
                
                total_evaluated = 0
                total_archived = 0
                total_expired = 0
                
                for tenant_id in tenant_ids:
                    try:
                        result = await retention_service.evaluate_retention(tenant_id)
                        total_evaluated += result.get("evaluated", 0)
                        total_archived += result.get("archived", 0)
                        total_expired += result.get("expired", 0)
                    except Exception as exc:
                        logger.error("Failed to evaluate retention for tenant %s: %s", tenant_id, exc)
                
                logger.info("Retention re-evaluation completed: evaluated=%d, archived=%d, expired=%d",
                           total_evaluated, total_archived, total_expired)
            finally:
                db.close()
        except asyncio.CancelledError:
            logger.info("Retention re-evaluation task cancelled")
            break
        except Exception as exc:
            logger.error("Error in retention re-evaluation task: %s", exc)
            # Continue running even if there's an error
            await asyncio.sleep(60)  # Wait 1 minute before retrying


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI startup/shutdown events.
    """
    logger.info("Starting Evidence & Receipt Indexing Service...")
    logger.info(f"Service: {SERVICE_NAME}, Version: {SERVICE_VERSION}")

    # Start background task for retention re-evaluation per FR-7
    retention_task = asyncio.create_task(retention_re_evaluation_task())
    
    yield
    
    # Cancel background task on shutdown
    retention_task.cancel()
    try:
        await retention_task
    except asyncio.CancelledError:
        pass

    logger.info("Shutting down Evidence & Receipt Indexing Service...")


app = FastAPI(
    title="ZeroUI Evidence & Receipt Indexing Service",
    version="1.0.0",
    description="Evidence & Receipt Indexing Service for ZeroUI ecosystem (ERIS PM-7)",
    lifespan=lifespan
)

# Request logging middleware (must be first per Rule 173)
app.add_middleware(RequestLoggingMiddleware)

# IAM authentication middleware
app.add_middleware(IAMAuthMiddleware)

# Rate limiting middleware
app.add_middleware(RateLimitingMiddleware)

# CORS middleware - configure via CORS_ORIGINS environment variable
cors_origins_env = os.getenv("CORS_ORIGINS", "*" if SERVICE_ENV == "development" else "")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",")] if cors_origins_env else []

if SERVICE_ENV == "production":
    if "*" in cors_origins or not cors_origins:
        logger.error("CORS_ORIGINS must be set to specific origins in production.")
        raise ValueError("CORS_ORIGINS must be set to specific origins in production.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else (["*"] if SERVICE_ENV == "development" else []),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/v1/evidence", tags=["evidence-receipt-indexing"])


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Root health check endpoint.

    Returns:
        HealthResponse with service status
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )

