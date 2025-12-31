"""
Test fixtures for Alerting Notification Service.

Provides lightweight async DB sessions and FastAPI TestClient so the
alerting_notification_service tests can run without external services.
"""
from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
import warnings
from pathlib import Path
from typing import AsyncGenerator

import httpx
from fastapi import HTTPException, Request, status
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Ensure package path is present for the hyphenated service directory
MODULE_ROOT = SRC_ROOT / "cloud_services" / "shared-services" / "alerting-notification-service"
spec = importlib.util.spec_from_loader("alerting_notification_service", loader=None, is_package=True)
module = importlib.util.module_from_spec(spec)
module.__path__ = [str(MODULE_ROOT)]
sys.modules["alerting_notification_service"] = module

pytestmark = pytest.mark.filterwarnings("ignore::ResourceWarning")

# FastAPI TestClient on AnyIO can emit noisy resource warnings for its in-process
# memory streams; suppress them to keep the suite output clean.
warnings.filterwarnings("ignore", message=r"Unclosed <MemoryObject.*", category=ResourceWarning)
warnings.simplefilter("ignore", ResourceWarning)
warnings.filterwarnings("ignore", category=ResourceWarning, module=r"anyio\.streams\.memory")

# Import models so SQLModel.metadata is populated before create_all
from alerting_notification_service import models as _models  # noqa: E402,F401
from alerting_notification_service.main import app  # noqa: E402
from alerting_notification_service.dependencies import (
    get_request_context as prod_get_request_context,  # noqa: E402
    get_session as prod_get_session,  # noqa: E402
    RequestContext,  # noqa: E402
)  # noqa: E402
from alerting_notification_service.config import get_settings  # noqa: E402
from alerting_notification_service.database import session as db_session  # noqa: E402


@pytest.fixture(scope="session")
def alerting_engine(tmp_path_factory: pytest.TempPathFactory):
    """Create an isolated sqlite engine for tests."""
    db_path = tmp_path_factory.mktemp("alerting_db") / "alerting.db"
    os.environ["ALERTING_DB_PATH"] = str(db_path)
    get_settings.cache_clear()  # type: ignore[attr-defined]

    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    asyncio.run(init_models())
    default_loop = None
    try:
        default_loop = asyncio.get_event_loop_policy().get_event_loop()
    except RuntimeError:
        default_loop = None

    yield engine, session_factory

    async def dispose_engine():
        await engine.dispose()

    asyncio.run(dispose_engine())
    if default_loop is not None and not default_loop.is_running():
        if not default_loop.is_closed():
            default_loop.close()
    asyncio.set_event_loop(None)


@pytest.fixture
async def session(alerting_engine) -> AsyncGenerator[AsyncSession, None]:
    """AsyncSession scoped per-test."""
    _, session_factory = alerting_engine
    async with session_factory() as sess:
        yield sess
        await sess.rollback()


@pytest.fixture
async def test_client(alerting_engine) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTPX ASGI client wired to the test DB session factory."""
    engine, session_factory = alerting_engine

    async def _get_session_override() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as sess:
            yield sess

    async def _get_ctx_override(request: Request) -> RequestContext:
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing X-Tenant-ID header",
            )
        actor_id = request.headers.get("X-Actor-ID", "tester")
        roles = [role.strip() for role in request.headers.get("X-Roles", "").split(",") if role.strip()]
        allowed_tenants = [
            tenant.strip() for tenant in request.headers.get("X-Allow-Tenants", tenant_id).split(",") if tenant.strip()
        ]
        return RequestContext(
            tenant_id=tenant_id,
            actor_id=actor_id,
            roles=roles,
            allowed_tenants=allowed_tenants,
            token_sub=actor_id,
        )

    app.dependency_overrides[prod_get_session] = _get_session_override
    app.dependency_overrides[prod_get_request_context] = _get_ctx_override
    # Keep global session helpers aligned with the test engine
    db_session.engine = engine
    db_session.SessionLocal = session_factory

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Provide default auth/tenant headers expected by the service
        client.headers.update(
            {
                "X-Tenant-ID": "tenant-integration",
                "X-Actor-ID": "tester",
                "X-Roles": "global_admin",
                "X-Allow-Tenants": "tenant-integration",
            }
        )
        yield client
