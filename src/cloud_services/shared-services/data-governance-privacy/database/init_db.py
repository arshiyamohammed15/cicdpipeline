#!/usr/bin/env python3
"""
Database initialization script for Data Governance & Privacy Module (M22).

What: Applies schema.sql to target PostgreSQL database with optional force reset
Why: Guarantees database matches PRD specification before service startup
Usage: python init_db.py --database-url postgresql://user:pass@host:5432/dbname [--force]
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
LOGGER = logging.getLogger("m22.init_db")


def parse_database_url(database_url: str) -> dict:
    """
    Parse PostgreSQL connection URL into psycopg2 parameters.

    Args:
        database_url: PostgreSQL connection string

    Returns:
        Dictionary with psycopg2 connection parameters
    """
    stripped = database_url.replace("postgresql://", "").replace("postgres://", "")

    if "@" in stripped:
        auth_part, host_part = stripped.split("@", 1)
        if ":" in auth_part:
            user, password = auth_part.split(":", 1)
        else:
            user, password = auth_part, ""
    else:
        user, password = "postgres", ""
        host_part = stripped

    if "/" in host_part:
        host_port, database = host_part.rsplit("/", 1)
    else:
        host_port, database = host_part, "postgres"

    if ":" in host_port:
        host, port = host_port.split(":", 1)
        port = int(port)
    else:
        host, port = host_port, 5432

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
    }


def read_schema_file() -> str:
    """Return schema.sql contents."""
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    return schema_path.read_text(encoding="utf-8")


def ensure_database_exists(conn_params: dict) -> None:
    """Create target database if it does not already exist."""
    db_name = conn_params["database"]
    admin_params = conn_params.copy()
    admin_params["database"] = "postgres"

    conn = psycopg2.connect(**admin_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    exists = cursor.fetchone()
    if not exists:
        LOGGER.info("Creating database %s", db_name)
        cursor.execute(f'CREATE DATABASE "{db_name}"')
        LOGGER.info("Database %s created", db_name)
    else:
        LOGGER.info("Database %s already exists", db_name)
    cursor.close()
    conn.close()


def initialize_schema(database_url: str, force: bool = False) -> None:
    """
    Apply schema.sql to target database.

    Args:
        database_url: PostgreSQL connection string
        force: Drop existing tables before creation
    """
    LOGGER.info("Initializing Data Governance & Privacy database...")
    conn_params = parse_database_url(database_url)
    ensure_database_exists(conn_params)
    schema_sql = read_schema_file()

    conn = psycopg2.connect(**conn_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    try:
        if force:
            LOGGER.warning("Force flag enabled: dropping existing tables")
            cursor.execute(
                """
                DROP TABLE IF EXISTS data_classification CASCADE;
                DROP TABLE IF EXISTS consent_records CASCADE;
                DROP TABLE IF EXISTS data_lineage CASCADE;
                DROP TABLE IF EXISTS retention_policies CASCADE;
                """
            )

        LOGGER.info("Executing schema file...")
        cursor.execute(schema_sql)

        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
              AND table_name IN (
                'data_classification',
                'consent_records',
                'data_lineage',
                'retention_policies'
              )
            ORDER BY table_name;
            """
        )
        tables = [row[0] for row in cursor.fetchall()]
        LOGGER.info("Verified tables: %s", tables)

        cursor.execute(
            """
            SELECT extname
            FROM pg_extension
            WHERE extname IN ('uuid-ossp', 'pg_trgm')
            ORDER BY extname;
            """
        )
        extensions = [row[0] for row in cursor.fetchall()]
        LOGGER.info("Verified extensions: %s", extensions)
    finally:
        cursor.close()
        conn.close()
    LOGGER.info("Database initialization complete")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize Data Governance & Privacy database schema"
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("ZEROUI_SHARED_DB_URL") or os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/m22_privacy"),
        help="PostgreSQL connection string (uses ZEROUI_SHARED_DB_URL per DB Plane Contract Option A)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Drop existing tables before creating schema",
    )
    args = parser.parse_args()

    try:
        initialize_schema(args.database_url, args.force)
    except Exception as exc:  # pragma: no cover - CLI surface
        LOGGER.error("Database initialization failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
