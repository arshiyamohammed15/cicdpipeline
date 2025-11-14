#!/bin/bash
# Database setup script for Contracts & Schema Registry Module (M34)
# Automated database initialization for production deployment

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    log_error "DATABASE_URL environment variable is not set"
    log_info "Set it using: export DATABASE_URL='postgresql://user:password@host:port/database'"
    exit 1
fi

# Check if psql is available
if ! command -v psql &> /dev/null; then
    log_warn "psql command not found. Attempting to use Python script instead..."
    if command -v python3 &> /dev/null; then
        log_info "Using Python initialization script..."
        python3 "$SCRIPT_DIR/init_db.py" --database-url "$DATABASE_URL"
        exit $?
    else
        log_error "Neither psql nor python3 is available. Please install PostgreSQL client tools."
        exit 1
    fi
fi

# Extract database connection details from DATABASE_URL
DB_URL="${DATABASE_URL#postgresql://}"
DB_URL="${DB_URL#postgres://}"

if [[ "$DB_URL" == *"@"* ]]; then
    AUTH="${DB_URL%%@*}"
    HOST_DB="${DB_URL#*@}"
    DB_USER="${AUTH%%:*}"
    DB_PASS="${AUTH#*:}"
else
    DB_USER="postgres"
    DB_PASS=""
    HOST_DB="$DB_URL"
fi

if [[ "$HOST_DB" == *"/"* ]]; then
    HOST_PORT="${HOST_DB%%/*}"
    DB_NAME="${HOST_DB#*/}"
else
    HOST_PORT="$HOST_DB"
    DB_NAME="postgres"
fi

if [[ "$HOST_PORT" == *":"* ]]; then
    DB_HOST="${HOST_PORT%%:*}"
    DB_PORT="${HOST_PORT#*:}"
else
    DB_HOST="$HOST_PORT"
    DB_PORT="5432"
fi

log_info "Connecting to PostgreSQL database..."
log_info "Host: $DB_HOST"
log_info "Port: $DB_PORT"
log_info "Database: $DB_NAME"
log_info "User: $DB_USER"

# Set PGPASSWORD if password is provided
if [ -n "$DB_PASS" ]; then
    export PGPASSWORD="$DB_PASS"
fi

# Check if database exists, create if not
log_info "Checking if database exists..."
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    log_info "Database $DB_NAME already exists"
else
    log_info "Creating database $DB_NAME..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE \"$DB_NAME\";"
    log_info "Database $DB_NAME created successfully"
fi

# Execute schema SQL
log_info "Initializing database schema..."
SCHEMA_FILE="$SCRIPT_DIR/schema.sql"

if [ ! -f "$SCHEMA_FILE" ]; then
    log_error "Schema file not found: $SCHEMA_FILE"
    exit 1
fi

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SCHEMA_FILE"

if [ $? -eq 0 ]; then
    log_info "Database schema initialized successfully"

    # Verify tables
    log_info "Verifying tables..."
    TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")
    log_info "Created $TABLE_COUNT tables"

    # List tables
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\dt"

    log_info "Database setup completed successfully!"
else
    log_error "Failed to initialize database schema"
    exit 1
fi
