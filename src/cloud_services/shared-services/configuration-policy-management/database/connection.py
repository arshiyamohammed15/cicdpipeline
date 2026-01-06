"""
Database connection management for Configuration & Policy Management.

What: PostgreSQL connection with SQLAlchemy, connection pooling per PRD
Why: Provides database connectivity with proper connection pool configuration
Reads/Writes: Reads DATABASE_URL env var, writes connection pool
Contracts: SQLAlchemy engine interface, health check contract
Risks: Connection pool exhaustion, database unavailability
"""

import logging
import os
import sys
from typing import Optional
from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool

try:
    # Local import allows us to create tables for SQLite test harnesses
    from .models import Base  # type: ignore
except Exception:  # pragma: no cover - fallback when models unavailable
    Base = None  # type: ignore

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None
_use_mock: bool = False

# Connection pool configuration per PRD (lines 802-808)
# max_connections: 200, min_connections: 20, connection_timeout: 30 seconds, idle_timeout: 10 minutes
MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", "200"))
MIN_CONNECTIONS = int(os.getenv("DB_MIN_CONNECTIONS", "20"))
CONNECTION_TIMEOUT = int(os.getenv("DB_CONNECTION_TIMEOUT", "30"))
IDLE_TIMEOUT = int(os.getenv("DB_IDLE_TIMEOUT", "600"))


def get_database_url() -> str:
    """
    Get database URL from environment or use mock fallback.

    Per DB Plane Contract Option A: Shared Plane services use ZEROUI_SHARED_DB_URL.
    Falls back to DATABASE_URL for backward compatibility, then to SQLite mock.

    Returns:
        Database connection string
    """
    # Use canonical plane-specific env var per DB Plane Contract Option A
    database_url = os.getenv("ZEROUI_SHARED_DB_URL")

    # Fallback to legacy DATABASE_URL for backward compatibility
    if not database_url:
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        logger.warning("ZEROUI_SHARED_DB_URL and DATABASE_URL not set, using in-memory SQLite mock")
        return "sqlite:///:memory:"

    return database_url


def create_database_engine() -> Engine:
    """
    Create SQLAlchemy engine with connection pooling per PRD.

    Per PRD lines 802-808: max_connections: 200, min_connections: 20,
    connection_timeout: 30 seconds, idle_timeout: 10 minutes

    Returns:
        SQLAlchemy engine instance
    """
    global _engine, _use_mock

    database_url = get_database_url()

    # Check if using mock (SQLite)
    if database_url.startswith("sqlite"):
        _use_mock = True
        engine = create_engine(
            database_url,
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
    else:
        # PostgreSQL configuration per PRD
        _use_mock = False
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=MIN_CONNECTIONS,
            max_overflow=MAX_CONNECTIONS - MIN_CONNECTIONS,
            pool_timeout=CONNECTION_TIMEOUT,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=IDLE_TIMEOUT,  # Recycle connections after idle timeout
            echo=False
        )

    # Add connection event listeners for logging
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Set SQLite pragmas for better compatibility."""
        if _use_mock:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def get_engine() -> Engine:
    """
    Get or create database engine (singleton).

    Returns:
        SQLAlchemy engine instance
    """
    global _engine
    if _engine is None:
        _engine = create_database_engine()
        _invoke_table_ensurer()
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get or create session factory (singleton).

    Returns:
        SQLAlchemy sessionmaker
    """
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return _session_factory


def get_session() -> Session:
    """
    Get a new database session.

    Returns:
        SQLAlchemy session
    """
    factory = get_session_factory()
    return factory()


def is_mock_mode() -> bool:
    """
    Check if using mock database (SQLite).

    Returns:
        True if using mock, False if using PostgreSQL
    """
    return _use_mock


def reset_connection_state() -> None:
    """
    Reset database connection global state for test isolation.

    This function disposes of existing engine and session factory,
    clearing all global state. Used by tests to ensure clean state
    between test runs.
    """
    global _engine, _session_factory, _use_mock

    # Dispose of existing engine if it exists
    if _engine is not None:
        try:
            _engine.dispose()
        except Exception:
            pass
        _engine = None

    # Reset session factory
    _session_factory = None

    # Reset mock flag
    _use_mock = False


def _invoke_table_ensurer() -> None:
    """
    Invoke table creation helper when running in SQLite mock mode.
    """
    module = sys.modules.get(__name__)
    ensure_tables = getattr(module, "_ensure_tables", None)
    if callable(ensure_tables):
        try:
            ensure_tables()
        except Exception:
            logger.exception("Failed to run custom _ensure_tables hook")


def _ensure_tables() -> None:
    """
    Default table creation logic for SQLite in-memory databases.

    Tests can override this function by assigning a different callable to
    configuration_policy_management.database.connection._ensure_tables.
    """
    if _engine is None:
        return
    if not _use_mock:
        return
    if Base is None or getattr(Base, "metadata", None) is None:
        return
    try:
        Base.metadata.create_all(bind=_engine)
    except Exception as exc:  # pragma: no cover - diagnostic only
        logger.warning("SQLite table creation failed: %s", exc)


def health_check() -> dict:
    """
    Perform database health check.

    Returns:
        Dictionary with health status and details
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")

        pool = engine.pool
        pool_status = {
            "size": pool.size() if hasattr(pool, 'size') else None,
            "checked_in": pool.checkedin() if hasattr(pool, 'checkedin') else None,
            "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else None,
            "overflow": pool.overflow() if hasattr(pool, 'overflow') else None
        }

        return {
            "status": "healthy",
            "database_type": "sqlite" if _use_mock else "postgresql",
            "connected": True,
            "pool": pool_status
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database_type": "sqlite" if _use_mock else "postgresql",
            "connected": False,
            "error": str(e)
        }
