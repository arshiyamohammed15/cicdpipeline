"""
Database connection management for UBI Module (EPC-9).

What: PostgreSQL connection with SQLAlchemy, connection pooling per PRD NFR-3
Why: Provides database connectivity with proper connection pool configuration
Reads/Writes: Reads DATABASE_URL env var, writes connection pool
Contracts: SQLAlchemy engine interface, health check contract
Risks: Connection pool exhaustion, database unavailability
"""

import logging
import os
from typing import Optional, Generator
from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import QueuePool, StaticPool

from .models import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None
_scoped_session: Optional[scoped_session] = None
_use_mock: bool = False

# Connection pool configuration per PRD NFR-3 (Scalability)
# Optimized for high-throughput event processing: 1000 events/second
MAX_CONNECTIONS = int(os.getenv("UBI_DB_MAX_CONNECTIONS", "200"))
MIN_CONNECTIONS = int(os.getenv("UBI_DB_MIN_CONNECTIONS", "20"))
CONNECTION_TIMEOUT = int(os.getenv("UBI_DB_CONNECTION_TIMEOUT", "30"))
IDLE_TIMEOUT = int(os.getenv("UBI_DB_IDLE_TIMEOUT", "600"))  # 10 minutes


def get_database_url() -> str:
    """
    Get database URL from environment or use mock fallback.

    Per DB Plane Contract Option A: Product Plane services use ZEROUI_PRODUCT_DB_URL.
    Falls back to UBI_DATABASE_URL and DATABASE_URL for backward compatibility.

    Returns:
        Database connection string
    """
    # Use canonical plane-specific env var per DB Plane Contract Option A
    database_url = os.getenv("ZEROUI_PRODUCT_DB_URL")

    # Fallback to legacy env vars for backward compatibility
    if not database_url:
        database_url = os.getenv("UBI_DATABASE_URL")
    if not database_url:
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        logger.warning("ZEROUI_PRODUCT_DB_URL, UBI_DATABASE_URL, and DATABASE_URL not set, using in-memory SQLite mock")
        return "sqlite:///:memory:"

    return database_url


def create_database_engine() -> Engine:
    """
    Create SQLAlchemy engine with connection pooling per PRD NFR-3.

    Per PRD NFR-3: Optimized for high-throughput (1000 events/second).
    Connection pool configuration:
    - pool_size: MIN_CONNECTIONS (default: 20)
    - max_overflow: MAX_CONNECTIONS - MIN_CONNECTIONS (default: 180)
    - pool_timeout: CONNECTION_TIMEOUT (default: 30 seconds)
    - pool_pre_ping: True (verify connections before using)
    - pool_recycle: IDLE_TIMEOUT (default: 600 seconds / 10 minutes)

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
        # PostgreSQL configuration per PRD NFR-3
        _use_mock = False
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=MIN_CONNECTIONS,
            max_overflow=MAX_CONNECTIONS - MIN_CONNECTIONS,
            pool_timeout=CONNECTION_TIMEOUT,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=IDLE_TIMEOUT,  # Recycle connections after idle timeout
            echo=False,
            # PostgreSQL-specific optimizations
            connect_args={
                "connect_timeout": CONNECTION_TIMEOUT,
                "application_name": "ubi_module"
            }
        )

    # Add connection event listeners for logging
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Set SQLite pragmas for better compatibility."""
        if _use_mock:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Log connection checkout for monitoring."""
        logger.debug("Database connection checked out")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Log connection checkin for monitoring."""
        logger.debug("Database connection checked in")

    # Auto-create schema when using in-memory SQLite (test/development)
    if _use_mock:
        Base.metadata.create_all(engine)

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
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get or create session factory (singleton).

    Returns:
        SQLAlchemy sessionmaker instance
    """
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False
        )
    return _session_factory


def get_scoped_session() -> scoped_session:
    """
    Get or create scoped session for thread-local sessions.

    Returns:
        SQLAlchemy scoped_session instance
    """
    global _scoped_session
    if _scoped_session is None:
        session_factory = get_session_factory()
        _scoped_session = scoped_session(session_factory)
    return _scoped_session


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session (FastAPI dependency).

    Yields:
        Database session
    """
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database schema.

    Creates all tables defined in models.
    """
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("UBI database schema initialized")


def health_check() -> dict:
    """
    Health check for database connectivity.

    Returns:
        Health status dictionary
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {
            "status": "healthy",
            "pool_size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

