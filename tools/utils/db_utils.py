"""
Database utility functions for tools.

This module provides common database operations to eliminate duplication
across tools scripts.
"""

import logging
from pathlib import Path
from typing import List, Callable, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection(db_path: Optional[str] = None):
    """
    Get a database connection context manager.

    Args:
        db_path: Optional path to database file. Defaults to config/constitution_rules.db

    Yields:
        Database connection object

    Example:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM constitution_rules")
    """
    from config.constitution.database import ConstitutionRulesDB

    if db_path is None:
        db_path = str(Path(__file__).parent.parent.parent / "config" / "constitution_rules.db")

    db = ConstitutionRulesDB(db_path)
    try:
        with db.get_connection() as conn:
            yield conn
    finally:
        db.close()


def execute_db_operation(operation: Callable, db_path: Optional[str] = None) -> Any:
    """
    Execute a database operation with proper connection management.

    Args:
        operation: Function that takes a connection and returns a result
        db_path: Optional path to database file

    Returns:
        Result of the operation

    Example:
        def get_rule_count(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM constitution_rules")
            return cursor.fetchone()[0]

        count = execute_db_operation(get_rule_count)
    """
    with get_db_connection(db_path) as conn:
        return operation(conn)


def get_all_rule_numbers(db_path: Optional[str] = None) -> List[int]:
    """
    Get all rule numbers from the database.

    Args:
        db_path: Optional path to database file

    Returns:
        List of rule numbers
    """
    def _get_rule_numbers(conn):
        cursor = conn.cursor()
        cursor.execute("SELECT rule_number FROM constitution_rules")
        return [row[0] for row in cursor.fetchall()]

    return execute_db_operation(_get_rule_numbers, db_path)

