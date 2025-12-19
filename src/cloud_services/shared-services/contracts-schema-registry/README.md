# Contracts & Schema Registry Module (EPC-12)

**Version:** 1.2.0
**Module ID:** M34 (code identifier for EPC-12)
**Description:** Centralized schema management, validation, and contract enforcement for ZeroUI ecosystem

## Overview

The Contracts & Schema Registry Module provides centralized schema management, validation, and contract enforcement capabilities. It supports JSON Schema, Avro, and Protobuf schema formats with compatibility checking, data transformation, and comprehensive analytics.

## Features

- **Schema Lifecycle Management**: Draft → Validation → Registration → Versioning → Evolution → Deprecation
- **Contract Definition & Enforcement**: OpenAPI, AsyncAPI, and custom contract definitions
- **Compatibility & Evolution**: Backward/forward compatibility checking and data transformation
- **Multi-Format Support**: JSON Schema, Avro, and Protobuf
- **Analytics & Governance**: Schema usage analytics, dependency mapping, impact analysis

## Prerequisites

- **Python 3.11+**
- **PostgreSQL 14+** (with JSONB support)
- **Redis 6+** (optional, for caching)
- **Docker & Docker Compose** (for local development)

## Quick Start

### 1. Local Development with Docker

The easiest way to get started is using Docker Compose:

```bash
# Navigate to module directory
cd src/cloud-services/shared-services/contracts-schema-registry

# Copy environment file
cp env.example .env

# Start PostgreSQL database
docker-compose up -d postgres

# Wait for database to be ready (check health)
docker-compose ps

# Initialize database schema
python database/init_db.py

# Or use the shell script
chmod +x database/setup.sh
./database/setup.sh
```

### 2. Manual PostgreSQL Setup

If you have PostgreSQL installed locally:

```bash
# Set environment variable
export DATABASE_URL="postgresql://username:password@localhost:5432/contracts_schema_registry"

# Initialize database
python database/init_db.py

# Or using psql directly
psql $DATABASE_URL -f database/schema.sql
```

### 3. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or install from project root
pip install -e .
```

### 4. Run the Application

```bash
# Set environment variables
export DATABASE_URL="postgresql://zeroui:zeroui_password@localhost:5432/contracts_schema_registry"

# Run FastAPI application
python -m contracts_schema_registry.main

# Or using uvicorn directly
uvicorn contracts_schema_registry.main:app --host 0.0.0.0 --port 8000
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
DATABASE_URL=postgresql://user:password@host:port/database

# Optional
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
SERVICE_PORT=8000
```

See `env.example` for all available configuration options.

### Database Configuration

The module requires PostgreSQL 14+ with the following extensions:
- `uuid-ossp` - For UUID generation
- `pg_trgm` - For GIN trigram indexes (full-text search)

These extensions are automatically enabled when running `database/schema.sql`.

## Database Setup

### Production Deployment

For production, use the provided SQL schema file:

```bash
# Using init script (recommended)
python database/init_db.py --database-url "postgresql://user:pass@host:port/dbname"

# Or using shell script
export DATABASE_URL="postgresql://user:pass@host:port/dbname"
./database/setup.sh

# Or manually with psql
psql "postgresql://user:pass@host:port/dbname" -f database/schema.sql
```

### Database Migrations

For development, use Alembic migrations:

```bash
# Navigate to migrations directory
cd database/migrations

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

## API Endpoints

Once running, the service exposes the following endpoints:

- **Health**: `GET /health`, `GET /registry/v1/health/live`, `GET /registry/v1/health/ready`
- **Metrics**: `GET /registry/v1/metrics`
- **Config**: `GET /registry/v1/config`
- **Schemas**: `GET /registry/v1/schemas`, `POST /registry/v1/schemas`, etc.
- **Contracts**: `GET /registry/v1/contracts`, `POST /registry/v1/contracts`, etc.
- **Validation**: `POST /registry/v1/validate`
- **Compatibility**: `POST /registry/v1/compatibility`
- **Transformation**: `POST /registry/v1/transform`

See the PRD document for complete API specification: `docs/architecture/modules/CONTRACTS_SCHEMA_REGISTRY_MODULE.md`

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/test_contracts_schema_registry.py tests/test_contracts_schema_registry_api.py -v

# Run with coverage
pytest --cov=contracts_schema_registry --cov-report=html
```

## Development

### Project Structure

```
contracts-schema-registry/
├── analytics/          # Analytics aggregation
├── cache/              # Cache management
├── compatibility/      # Compatibility checking and transformation
├── database/           # Database models, migrations, schema
│   ├── migrations/     # Alembic migrations
│   ├── schema.sql      # Production SQL schema
│   ├── init_db.py      # Database initialization script
│   └── setup.sh        # Database setup script
├── templates/          # Schema templates
├── validators/         # Schema validators (JSON, Avro, Protobuf)
├── main.py             # FastAPI application entry point
├── routes.py           # API routes
├── services.py         # Business logic
├── middleware.py       # Request middleware
├── models.py           # Pydantic models
├── errors.py           # Error handling
├── dependencies.py     # External service mocks
├── docker-compose.yml  # Local PostgreSQL setup
├── .env.example        # Environment variable template
└── README.md           # This file
```

### Adding New Features

1. **Schema Validators**: Add to `validators/` directory
2. **API Endpoints**: Add routes to `routes.py`
3. **Business Logic**: Add services to `services.py`
4. **Database Changes**: Create Alembic migration in `database/migrations/versions/`

## Production Deployment

### Infrastructure Requirements

Per PRD specification:

- **Database**: PostgreSQL 14+ with JSONB support, connection pooling, read replicas
- **Caching**: Redis 6+ cluster with SSL encryption
- **Networking**: Service mesh, TLS 1.3

### Deployment Steps

1. **Provision PostgreSQL Database**
   ```bash
   # Create database and user
   createdb contracts_schema_registry
   createuser zeroui
   ```

2. **Initialize Database Schema**
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:port/dbname"
   python database/init_db.py
   ```

3. **Configure Environment**
   ```bash
   cp env.example .env
   # Edit .env with production values
   ```

4. **Deploy Application**
   ```bash
   # Using Docker
   docker build -t contracts-schema-registry:1.2.0 .
   docker run -d --env-file .env contracts-schema-registry:1.2.0

   # Or using process manager (systemd, PM2, etc.)
   ```

5. **Run Database Migrations** (if using Alembic)
   ```bash
   alembic upgrade head
   ```

### Health Checks

The service provides health check endpoints for monitoring:

- **Liveness**: `GET /registry/v1/health/live` - Service is running
- **Readiness**: `GET /registry/v1/health/ready` - Service is ready (database connected)

### Monitoring

Monitor the following metrics:

- Database connection pool utilization
- Schema validation latency
- Contract enforcement latency
- Cache hit rates
- Error rates by error code

## Troubleshooting

### Database Connection Issues

```bash
# Test database connection
psql $DATABASE_URL -c "SELECT version();"

# Check if extensions are enabled
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm');"
```

### Schema Initialization Fails

```bash
# Check if database exists
psql -l | grep contracts_schema_registry

# Check PostgreSQL logs
docker-compose logs postgres

# Verify schema file is readable
cat database/schema.sql | head -20
```

### Application Won't Start

```bash
# Check environment variables
env | grep DATABASE_URL

# Check Python dependencies
pip list | grep -E "(fastapi|sqlalchemy|psycopg2)"

# Check logs
python -m contracts_schema_registry.main 2>&1 | tee app.log
```

## Integration

### With IAM Module (EPC-1)

The module integrates with IAM for access control. Configure:

```bash
IAM_SERVICE_URL=http://iam-service:8001
```

### With Key Management Service (EPC-11)

For schema signing, configure:

```bash
KMS_SERVICE_URL=http://kms-service:8002
```

## Support

For issues, questions, or contributions:

1. Check the PRD: `docs/architecture/modules/CONTRACTS_SCHEMA_REGISTRY_MODULE.md`
2. Review test files: `tests/test_contracts_schema_registry*.py`
3. Check logs and error messages

## License

Part of ZeroUI 2.0 project.

## Version History

- **v1.2.0**: Complete implementation with PostgreSQL support, comprehensive testing
- **v1.1.0**: Initial specification
