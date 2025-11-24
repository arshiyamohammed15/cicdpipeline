"""
Database session management for the Health & Reliability Monitoring module.

Uses SQLAlchemy 2.0 engine + scoped session for synchronous FastAPI dependencies.
"""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

from ..config import load_settings

settings = load_settings()

engine_kwargs = {
    "echo": settings.database.echo_sql,
    "future": True,
}

if settings.database.url.startswith("sqlite"):
    engine_kwargs.update(
        {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    )
else:
    engine_kwargs.update(
        {
            "pool_size": settings.database.pool_size,
            "max_overflow": settings.database.max_overflow,
        }
    )

engine = create_engine(settings.database.url, **engine_kwargs)

if settings.database.url.startswith("sqlite"):
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))

SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
)


@contextmanager
def session_scope():
    """Provide transactional scope around operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

