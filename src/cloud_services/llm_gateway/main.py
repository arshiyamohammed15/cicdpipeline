"""
FastAPI entrypoint for the LLM Gateway & Safety Enforcement module.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Use absolute import to avoid resolution issues when package shims are used in tests.
from cloud_services.llm_gateway.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="LLM Gateway & Safety Enforcement",
        version="2.0.0",
        description="Central gateway for ZeroUI LLM traffic with safety enforcement.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "healthy"}

    return app


app = create_app()
