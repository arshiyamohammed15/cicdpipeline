# SIN Alembic Usage

This directory provides Alembic scaffolding that applies the SQL from `0001_initial.sql`.

## Setup
1. Set `sqlalchemy.url` to your target database (PostgreSQL assumed), e.g.:
   - Windows PowerShell:
     ```pwsh
     setx sqlalchemy.url "postgresql+psycopg2://user:pass@host:5432/dbname"
     ```

2. From the repo root:
   ```pwsh
   cd migrations/sin
   alembic upgrade head
   ```

The revision `0001_initial` executes the SQL file to create SIN producer/signal/DLQ tables and indexes.
