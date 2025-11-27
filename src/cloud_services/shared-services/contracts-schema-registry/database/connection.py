"""
Database connection management for Contracts & Schema Registry.

What: PostgreSQL connection with SQLAlchemy, mock fallback for development
Why: Provides database connectivity with graceful degradation
Reads/Writes: Reads DATABASE_URL env var, writes connection pool
Contracts: SQLAlchemy engine interface, health check contract
Risks: Connection pool exhaustion, database unavailability
"""

import logging
import os
from typing import Optional
from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None
_use_mock: bool = False


def get_database_url() -> str:
    """
    Get database URL from environment or use mock fallback.

    Returns:
        Database connection string
    """
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        logger.warning("DATABASE_URL not set, using in-memory SQLite mock")
        return "sqlite:///:memory:"

    return database_url


def create_database_engine() -> Engine:
    """
    Create SQLAlchemy engine with appropriate configuration.

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
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
        )
    else:
        # PostgreSQL configuration
        _use_mock = False
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
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

        return {
            "status": "healthy",
            "database_type": "sqlite" if _use_mock else "postgresql",
            "connected": True
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database_type": "sqlite" if _use_mock else "postgresql",
            "connected": False,
            "error": str(e)
        }
