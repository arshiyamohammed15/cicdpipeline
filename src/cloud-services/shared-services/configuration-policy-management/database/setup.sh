#!/bin/bash
# Database setup script for Configuration & Policy Management Module (M23)
# Per PRD: Automated database setup for development and production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Configuration & Policy Management Database Setup${NC}"
echo "=========================================="

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}Warning: DATABASE_URL not set. Using default.${NC}"
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/configuration_policy_management"
fi

# Check if PostgreSQL is available
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql command not found. Please install PostgreSQL client.${NC}"
    exit 1
fi

# Parse DATABASE_URL
DB_URL=$DATABASE_URL
DB_NAME=$(echo $DB_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

echo -e "${GREEN}Setting up database: ${DB_NAME}${NC}"

# Run init_db.py
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
python3 "$SCRIPT_DIR/init_db.py" --database-url "$DATABASE_URL"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database setup completed successfully!${NC}"
else
    echo -e "${RED}Database setup failed!${NC}"
    exit 1
fi
