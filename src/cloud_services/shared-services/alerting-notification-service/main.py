"""FastAPI entrypoint for Alerting & Notification Service."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .config import get_settings
from .dependencies import get_session, on_shutdown, on_startup
from .observability.metrics import register_metrics
from .routes.v1 import router as v1_router
from .services.escalation_scheduler import EscalationScheduler
from .services.stream_service import get_stream_service

settings = get_settings()
logging.basicConfig(level=settings.service.log_level)
logger = logging.getLogger("alerting_service")

# Global escalation scheduler instance
escalation_scheduler: EscalationScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global escalation_scheduler
    
    logger.info("Starting Alerting & Notification Service", extra={"version": settings.service.version})
    await on_startup()
    register_metrics()
    
    # Start escalation scheduler for multi-step escalations with delays
    try:
        from sqlmodel.ext.asyncio import async_sessionmaker
        from .database.session import engine
        
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        escalation_scheduler = EscalationScheduler(session_factory=session_factory)
        await escalation_scheduler.start()
        logger.info("Escalation scheduler started")
    except Exception as exc:
        logger.warning("Failed to start escalation scheduler: %s", exc)
    
    yield
    
    # Stop escalation scheduler
    if escalation_scheduler:
        try:
            await escalation_scheduler.stop()
            logger.info("Escalation scheduler stopped")
        except Exception as exc:
            logger.warning("Error stopping escalation scheduler: %s", exc)
    
    await on_shutdown()
    logger.info("Stopping Alerting & Notification Service")


app = FastAPI(
    title=settings.service.name,
    version=settings.service.version,
    description="Implements Alerting & Notification Service",
    lifespan=lifespan,
)

origins = settings.service.allowed_origins or (["*"] if settings.service.environment == "dev" else [])
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/v1")


@app.get("/healthz")
async def healthz():
    return {
        "service": settings.service.name,
        "version": settings.service.version,
        "status": "UP",
        "stream_subscribers": get_stream_service().subscriber_count(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/metrics")
async def metrics_endpoint():
    payload = generate_latest()
    # Guard against empty payloads in test harnesses where startup hooks may not register collectors
    if not payload:
        payload = b"# metrics: no counters registered\n"
    return Response(payload, media_type=CONTENT_TYPE_LATEST)
