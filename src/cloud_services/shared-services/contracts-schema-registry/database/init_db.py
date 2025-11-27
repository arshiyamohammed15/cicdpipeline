#!/usr/bin/env python3
"""
Database initialization script for Contracts & Schema Registry Module (M34).

What: Initializes PostgreSQL database with schema from schema.sql
Why: Automated database setup for development and production
Usage: python init_db.py [--database-url DATABASE_URL]
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_database_url(database_url: str) -> dict:
    """
    Parse PostgreSQL connection URL into components.

    Args:
        database_url: PostgreSQL connection string

    Returns:
        Dictionary with connection parameters
    """
    # Remove postgresql:// or postgres:// prefix
    url = database_url.replace('postgresql://', '').replace('postgres://', '')

    # Split into parts
    if '@' in url:
        auth_part, host_part = url.split('@', 1)
        if ':' in auth_part:
            user, password = auth_part.split(':', 1)
        else:
            user = auth_part
            password = ''
    else:
        user = 'postgres'
        password = ''
        host_part = url

    if '/' in host_part:
        host_port, database = host_part.rsplit('/', 1)
    else:
        host_port = host_part
        database = 'postgres'

    if ':' in host_port:
        host, port = host_port.split(':', 1)
        port = int(port)
    else:
        host = host_port
        port = 5432

    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'database': database
    }


def read_schema_file() -> str:
    """
    Read schema.sql file.

    Returns:
        SQL schema content
    """
    script_dir = Path(__file__).parent
    schema_file = script_dir / 'schema.sql'

    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    with open(schema_file, 'r', encoding='utf-8') as f:
        return f.read()


def create_database_if_not_exists(conn_params: dict) -> None:
    """
    Create database if it doesn't exist.

    Args:
        conn_params: Connection parameters
    """
    db_name = conn_params['database']

    # Connect to postgres database to create target database
    create_params = conn_params.copy()
    create_params['database'] = 'postgres'

    try:
        conn = psycopg2.connect(**create_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()

        if not exists:
            logger.info(f"Creating database: {db_name}")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            logger.info(f"Database {db_name} created successfully")
        else:
            logger.info(f"Database {db_name} already exists")

        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        logger.error(f"Error creating database: {e}")
        raise


def initialize_schema(database_url: str, force: bool = False) -> None:
    """
    Initialize database schema.

    Args:
        database_url: PostgreSQL connection string
        force: If True, drop existing tables before creating
    """
    logger.info("Starting database initialization...")

    # Parse database URL
    conn_params = parse_database_url(database_url)

    # Create database if it doesn't exist
    create_database_if_not_exists(conn_params)

    # Read schema file
    schema_sql = read_schema_file()

    # Connect to target database
    try:
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        if force:
            logger.warning("Force mode: Dropping existing tables...")
            cursor.execute("""
                DROP TABLE IF EXISTS schema_analytics CASCADE;
                DROP TABLE IF EXISTS schema_dependencies CASCADE;
                DROP TABLE IF EXISTS contracts CASCADE;
                DROP TABLE IF EXISTS schemas CASCADE;
                DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
            """)
            logger.info("Existing tables dropped")

        # Execute schema SQL
        logger.info("Executing schema SQL...")
        cursor.execute(schema_sql)
        logger.info("Schema initialized successfully")

        # Verify tables were created
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        logger.info(f"Created tables: {[t[0] for t in tables]}")

        # Verify extensions
        cursor.execute("""
            SELECT extname
            FROM pg_extension
            WHERE extname IN ('uuid-ossp', 'pg_trgm');
        """)
        extensions = cursor.fetchall()
        logger.info(f"Enabled extensions: {[e[0] for e in extensions]}")

        cursor.close()
        conn.close()

        logger.info("Database initialization completed successfully")

    except psycopg2.Error as e:
        logger.error(f"Error initializing schema: {e}")
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Initialize Contracts & Schema Registry database'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        default=os.getenv('DATABASE_URL'),
        help='PostgreSQL connection URL (default: from DATABASE_URL env var)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Drop existing tables before creating (WARNING: Destructive)'
    )

    args = parser.parse_args()

    if not args.database_url:
        logger.error("DATABASE_URL not provided. Set environment variable or use --database-url")
        sys.exit(1)

    if not args.database_url.startswith(('postgresql://', 'postgres://')):
        logger.error("DATABASE_URL must start with postgresql:// or postgres://")
        sys.exit(1)

    try:
        initialize_schema(args.database_url, force=args.force)
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
