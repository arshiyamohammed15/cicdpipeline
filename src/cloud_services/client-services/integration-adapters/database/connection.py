"""
Database connection and session management for Integration Adapters Module.

What: SQLAlchemy session management with PostgreSQL/SQLite compatibility
Why: Centralized database connection handling
Reads/Writes: Database connections and sessions
Contracts: Standard SQLAlchemy session patterns
Risks: Connection leaks, transaction handling errors
"""

from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base

# Database URL from environment or default to SQLite for testing
import os
DATABASE_URL = os.getenv(
    "INTEGRATION_ADAPTERS_DATABASE_URL",
    "sqlite:///./integration_adapters_test.db"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all database tables (for testing)."""
    Base.metadata.drop_all(bind=engine)

