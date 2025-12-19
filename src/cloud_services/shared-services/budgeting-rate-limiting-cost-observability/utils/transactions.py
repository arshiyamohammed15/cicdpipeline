"""
Transaction isolation utilities for EPC-13 per PRD lines 512-534.

What: Transaction isolation and concurrency control helpers
Why: Ensures data consistency and prevents race conditions
Reads/Writes: Manages database transaction isolation levels
Contracts: Transaction isolation requirements per PRD
Risks: Deadlocks, transaction timeouts
"""

import logging
from contextlib import contextmanager
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect

logger = logging.getLogger(__name__)


def _is_postgresql(db: Session) -> bool:
    """Check if database is PostgreSQL."""
    try:
        return 'postgresql' in str(db.bind.url).lower() or 'postgres' in str(db.bind.url).lower()
    except Exception:
        return False


@contextmanager
def serializable_transaction(db: Session):
    """
    Context manager for SERIALIZABLE transaction isolation per PRD.

    Used for: Budget checks, rate limit increments, quota allocations.
    
    Note: SQLite uses SERIALIZABLE by default, so we only set it explicitly for PostgreSQL.
    """
    is_pg = _is_postgresql(db)
    if is_pg:
        try:
            db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
        except Exception as e:
            logger.warning(f"Failed to set SERIALIZABLE isolation level: {e}")
    
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Serializable transaction failed: {e}")
        raise
    finally:
        if is_pg:
            try:
                db.execute(text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED"))
            except Exception as e:
                logger.warning(f"Failed to reset isolation level: {e}")


@contextmanager
def read_committed_transaction(db: Session):
    """
    Context manager for READ COMMITTED transaction isolation per PRD.

    Used for: Cost recording.
    
    Note: SQLite doesn't support READ COMMITTED, so we use default isolation for SQLite.
    """
    is_pg = _is_postgresql(db)
    if is_pg:
        try:
            db.execute(text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED"))
        except Exception as e:
            logger.warning(f"Failed to set READ COMMITTED isolation level: {e}")
    
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Read committed transaction failed: {e}")
        raise

