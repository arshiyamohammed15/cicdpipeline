import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alerting_notification_service.database import session as db_session
from alerting_notification_service.dependencies import get_engine, get_session as dep_get_session, on_shutdown, on_startup


@pytest.mark.asyncio
async def test_session_initialization_and_dependencies(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    monkeypatch.setattr(db_session, "engine", engine, raising=False)
    monkeypatch.setattr(db_session, "SessionLocal", session_maker, raising=False)

    from alerting_notification_service import dependencies as deps

    monkeypatch.setattr(deps, "engine", engine, raising=False)
    monkeypatch.setattr(deps, "init_db", db_session.init_db, raising=False)

    await db_session.init_db()
    assert get_engine() is engine

    db_gen = db_session.get_session()
    session = await db_gen.__anext__()
    assert isinstance(session, AsyncSession)
    await db_gen.aclose()

    dep_gen = dep_get_session()
    dep_session = await dep_gen.__anext__()
    assert dep_session.bind is not None
    await dep_gen.aclose()

    await on_startup()
    await on_shutdown()

    await engine.dispose()

