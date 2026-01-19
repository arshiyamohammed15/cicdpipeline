#!/usr/bin/env bash
set -euo pipefail

# IDE plane database initialization
# Creates core and meta schemas and revokes CREATE on public schema

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  -- Create meta schema for schema version tracking
  CREATE SCHEMA IF NOT EXISTS meta AUTHORIZATION $POSTGRES_USER;

  -- Create core schema for core tables
  CREATE SCHEMA IF NOT EXISTS core AUTHORIZATION $POSTGRES_USER;

  -- Basic least-privilege: prevent random users from creating tables in public schema
  REVOKE CREATE ON SCHEMA public FROM PUBLIC;

  -- Ensure the user can use its schemas (ownership already implies full control)
  GRANT USAGE ON SCHEMA meta TO $POSTGRES_USER;
  GRANT USAGE ON SCHEMA core TO $POSTGRES_USER;
EOSQL
