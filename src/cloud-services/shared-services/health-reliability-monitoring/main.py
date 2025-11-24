"""
FastAPI entrypoint for the Health & Reliability Monitoring capability.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .config import load_settings
from .routes import router as v1_router
from .service_container import get_settings, get_telemetry_worker

settings = load_settings()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("health_reliability_monitoring")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks."""
    logger.info(
        "Starting Health & Reliability Monitoring service",
        extra={"version": settings.service.version},
    )
    worker = get_telemetry_worker()
    await worker.start()
    yield
    await worker.stop()
    logger.info("Stopping Health & Reliability Monitoring service")


app = FastAPI(
    title="ZeroUI Health & Reliability Monitoring",
    version=settings.service.version,
    description="Implements FR-1..FR-11 & NFRs for the Health & Reliability Monitoring capability",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.service.environment == "development" else [],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(v1_router)


@app.get("/healthz")
async def healthz():
    """Base health endpoint for the service itself."""
    return {
        "service": settings.service.name,
        "version": settings.service.version,
        "status": "UP",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus scrape endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

