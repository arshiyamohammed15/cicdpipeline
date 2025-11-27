"""
FastAPI application entrypoint for MMM Engine.
"""

from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import router, get_service
from .middleware import IAMAuthMiddleware
from .service_registry import initialize_services
from .integrations.pm3_stream import PM3EventStream

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    initialize_services()

    app = FastAPI(
        title=settings.service_name,
        version=settings.service_version,
        description="Mirror-Mentor-Multiplier decision engine",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(IAMAuthMiddleware)
    app.include_router(router)

    pm3_stream = PM3EventStream(handler=get_service().ingest_signal)

    @app.on_event("startup")
    async def start_stream() -> None:
        await pm3_stream.start()

    @app.on_event("shutdown")
    async def stop_stream() -> None:
        await pm3_stream.stop()

    logger.info("MMM Engine service initialized")
    return app


app = create_app()


