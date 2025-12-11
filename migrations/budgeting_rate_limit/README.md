# Budgeting / Rate-Limiting Alembic Usage

This directory provides Alembic scaffolding that applies the SQL from `0001_initial.sql`.

## Setup
1. Set `sqlalchemy.url` (env or alembic.ini) to your target database, e.g.:
   - Windows PowerShell:
     ```pwsh
     setx sqlalchemy.url "postgresql+psycopg2://user:pass@host:5432/dbname"
     ```
   - Or export in shell before running Alembic.

2. From the repo root:
   ```pwsh
   cd migrations/budgeting_rate_limit
   alembic upgrade head
   ```

The revision `0001_initial` executes the SQL file to create budget/rate-limit tables and indexes.
