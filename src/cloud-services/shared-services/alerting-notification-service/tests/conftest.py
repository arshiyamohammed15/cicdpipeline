import asyncio
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
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
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine


@pytest.fixture()
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session


@pytest.fixture()
def test_client(engine):
    async def _override_session():
        async with AsyncSession(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

