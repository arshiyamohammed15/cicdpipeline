"""
Test fixtures for Alerting Notification Service.

Provides lightweight async DB sessions and FastAPI TestClient so the
alerting_notification_service tests can run without external services.
"""
from __future__ import annotations

import asyncio
import os
import sys
import warnings
from pathlib import Path
from typing import AsyncGenerator

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

# Ensure package path is present
MODULE_ROOT = Path(__file__).resolve().parents[3] / "src" / "cloud_services" / "shared-services" / "alerting-notification-service"
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

pytestmark = pytest.mark.filterwarnings("ignore::ResourceWarning")

# FastAPI TestClient on AnyIO can emit noisy resource warnings for its in-process
# memory streams; suppress them to keep the suite output clean.
warnings.filterwarnings("ignore", message=r"Unclosed <MemoryObject.*", category=ResourceWarning)
warnings.simplefilter("ignore", ResourceWarning)
warnings.filterwarnings("ignore", category=ResourceWarning, module=r"anyio\.streams\.memory")

# Import models so SQLModel.metadata is populated before create_all
from alerting_notification_service import models as _models  # noqa: E402,F401
from alerting_notification_service.main import app  # noqa: E402
from alerting_notification_service.dependencies import get_session as prod_get_session  # noqa: E402
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
    return engine, session_factory


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

    app.dependency_overrides[prod_get_session] = _get_session_override
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
