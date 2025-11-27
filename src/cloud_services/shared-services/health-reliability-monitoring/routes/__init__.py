"""FastAPI routers for Health & Reliability Monitoring."""

from fastapi import APIRouter

from . import registry, health, safe_to_act

router = APIRouter()
router.include_router(registry.router, prefix="/v1/health", tags=["registry"])
router.include_router(health.router, prefix="/v1/health", tags=["health"])
router.include_router(safe_to_act.router, prefix="/v1/health", tags=["safe-to-act"])

