import asyncio
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.append(str(PACKAGE_ROOT))

from ..database import models  # noqa: F401 ensures metadata registration
from ..dependencies import get_session
from ..main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def engine(event_loop):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async def init():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    event_loop.run_until_complete(init())
    yield engine
    event_loop.run_until_complete(engine.dispose())


@pytest_asyncio.fixture()
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as db_session:
        yield db_session


@pytest.fixture()
def test_client(engine):
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_session():
        async with session_maker() as db_session:
            yield db_session

    app.dependency_overrides[get_session] = _override_session
    client = TestClient(app)
    client.headers.update(
        {
            "X-Tenant-ID": "tenant-integration",
            "X-Actor-ID": "test-user",
            "X-Roles": "tenant_user",
        }
    )
    yield client
    app.dependency_overrides.clear()

