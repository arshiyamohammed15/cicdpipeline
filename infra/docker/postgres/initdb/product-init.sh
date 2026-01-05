#!/usr/bin/env bash
set -euo pipefail

# Product plane database initialization
# Creates app schema, enables pgvector extension, and revokes CREATE on public schema

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  -- Enable pgvector extension for vector search
  CREATE EXTENSION IF NOT EXISTS vector;

  -- Create a dedicated schema for application tables
  CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION $POSTGRES_USER;

  -- Basic least-privilege: prevent random users from creating tables in public schema
  REVOKE CREATE ON SCHEMA public FROM PUBLIC;

  -- Ensure the app user can use its schema (ownership already implies full control)
  GRANT USAGE ON SCHEMA app TO $POSTGRES_USER;
EOSQL

