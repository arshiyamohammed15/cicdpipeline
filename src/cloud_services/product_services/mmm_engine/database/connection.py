"""
Database connection management for MMM Engine.
"""

from __future__ import annotations

import logging
import os
from typing import Generator, Optional

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import QueuePool, StaticPool

from .models import Base

logger = logging.getLogger(__name__)

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None
_scoped_session: Optional[scoped_session] = None
_use_sqlite = False

MAX_CONNECTIONS = int(os.getenv("MMM_DB_MAX_CONNECTIONS", "50"))
MIN_CONNECTIONS = int(os.getenv("MMM_DB_MIN_CONNECTIONS", "5"))
CONNECTION_TIMEOUT = int(os.getenv("MMM_DB_CONNECTION_TIMEOUT", "30"))
IDLE_TIMEOUT = int(os.getenv("MMM_DB_IDLE_TIMEOUT", "600"))


def get_database_url() -> str:
    """
    Get database URL from environment or use mock fallback.

    Per DB Plane Contract Option A: Product Plane services use ZEROUI_PRODUCT_DB_URL.
    Falls back to MMM_DATABASE_URL and DATABASE_URL for backward compatibility.
    """
    # Use canonical plane-specific env var per DB Plane Contract Option A
    url = os.getenv("ZEROUI_PRODUCT_DB_URL")

    # Fallback to legacy env vars for backward compatibility
    if not url:
        url = os.getenv("MMM_DATABASE_URL")
    if not url:
        url = os.getenv("DATABASE_URL")

    if not url:
        logger.warning("ZEROUI_PRODUCT_DB_URL, MMM_DATABASE_URL, and DATABASE_URL not set, using in-memory SQLite")
        return "sqlite:///:memory:"
    return url


def create_database_engine() -> Engine:
    global _use_sqlite

    database_url = get_database_url()
    if database_url.startswith("sqlite"):
        _use_sqlite = True
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    else:
        _use_sqlite = False
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=MIN_CONNECTIONS,
            max_overflow=MAX_CONNECTIONS - MIN_CONNECTIONS,
            pool_timeout=CONNECTION_TIMEOUT,
            pool_pre_ping=True,
            pool_recycle=IDLE_TIMEOUT,
            echo=False,
        )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):  # pragma: no cover
        if _use_sqlite:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    if _use_sqlite:
        Base.metadata.create_all(engine)

    return engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_database_engine()
    return _engine


def get_session_factory() -> sessionmaker:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=get_engine(),
        )
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def health_check() -> dict:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception as exc:  # pragma: no cover
        return {"status": "unhealthy", "error": str(exc)}


