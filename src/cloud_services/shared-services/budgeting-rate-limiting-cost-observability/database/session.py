"""
Database session management for M35.

What: Proper database session lifecycle management with dependency injection
Why: Ensures proper connection pooling, session scoping, and thread safety
Reads/Writes: Manages database connections and sessions
Contracts: SQLAlchemy session management best practices
Risks: Connection leaks, session management errors
"""

import os
import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool

from .models import Base

logger = logging.getLogger(__name__)

# Database URL from environment or default to in-memory SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

# Create engine with appropriate configuration
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
else:
    # PostgreSQL or other database configuration
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session for thread-local sessions
ScopedSession = scoped_session(SessionLocal)


def init_db():
    """Initialize database schema."""
    Base.metadata.create_all(engine)
    logger.info("Database schema initialized")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_scoped_db() -> Session:
    """
    Get scoped database session (thread-local).
    
    Returns:
        Scoped database session
    """
    return ScopedSession()

