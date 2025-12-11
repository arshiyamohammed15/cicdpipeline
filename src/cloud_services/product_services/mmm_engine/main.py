"""
FastAPI application entrypoint for MMM Engine.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

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

    pm3_stream = PM3EventStream(handler=get_service().ingest_signal)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await pm3_stream.start()
        yield
        await pm3_stream.stop()

    app = FastAPI(
        title=settings.service_name,
        version=settings.service_version,
        description="Mirror-Mentor-Multiplier decision engine",
        lifespan=lifespan,
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

    logger.info("MMM Engine service initialized")
    return app


app = create_app()

