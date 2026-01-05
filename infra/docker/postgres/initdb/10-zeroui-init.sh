#!/usr/bin/env bash
set -euo pipefail

# This script runs ONLY on first container init when the data directory is empty.
# It creates 3 databases and 3 users (Option A), plus an "app" schema in each DB.

psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "postgres" <<-EOSQL
  -- Roles (users)
  CREATE ROLE ${ZEROUI_TENANT_DB_USER}  LOGIN PASSWORD '${ZEROUI_TENANT_DB_PASSWORD}';
  CREATE ROLE ${ZEROUI_PRODUCT_DB_USER} LOGIN PASSWORD '${ZEROUI_PRODUCT_DB_PASSWORD}';
  CREATE ROLE ${ZEROUI_SHARED_DB_USER}  LOGIN PASSWORD '${ZEROUI_SHARED_DB_PASSWORD}';

  -- Databases owned by their respective users
  CREATE DATABASE ${ZEROUI_TENANT_DB_NAME}  OWNER ${ZEROUI_TENANT_DB_USER};
  CREATE DATABASE ${ZEROUI_PRODUCT_DB_NAME} OWNER ${ZEROUI_PRODUCT_DB_USER};
  CREATE DATABASE ${ZEROUI_SHARED_DB_NAME}  OWNER ${ZEROUI_SHARED_DB_USER};

  -- Ensure each user can connect to its DB (explicit)
  GRANT CONNECT ON DATABASE ${ZEROUI_TENANT_DB_NAME}  TO ${ZEROUI_TENANT_DB_USER};
  GRANT CONNECT ON DATABASE ${ZEROUI_PRODUCT_DB_NAME} TO ${ZEROUI_PRODUCT_DB_USER};
  GRANT CONNECT ON DATABASE ${ZEROUI_SHARED_DB_NAME}  TO ${ZEROUI_SHARED_DB_USER};
EOSQL

# Per-DB hardening + schema
init_one_db () {
  local db_name="$1"
  local db_user="$2"

  psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "${db_name}" <<-EOSQL
    -- Create a dedicated schema for application tables
    CREATE SCHEMA IF NOT EXISTS app AUTHORIZATION ${db_user};

    -- Basic least-privilege: prevent random users from creating tables in public schema
    REVOKE CREATE ON SCHEMA public FROM PUBLIC;

    -- Ensure the app user can use its schema (ownership already implies full control)
    GRANT USAGE ON SCHEMA app TO ${db_user};
EOSQL
}

init_one_db "${ZEROUI_TENANT_DB_NAME}"  "${ZEROUI_TENANT_DB_USER}"
init_one_db "${ZEROUI_PRODUCT_DB_NAME}" "${ZEROUI_PRODUCT_DB_USER}"
init_one_db "${ZEROUI_SHARED_DB_NAME}"  "${ZEROUI_SHARED_DB_USER}"

