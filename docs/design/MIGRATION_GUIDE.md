## Migration Guide (Budgeting/Rate-Limit and SIN)

This repository includes SQL migrations and OpenAPI/event schemas derived from the implemented services and tests. These artifacts are additive and do not change runtime behaviour unless applied to a database.

### Files
- `migrations/budgeting_rate_limit/0001_initial.sql` — BudgetDefinition/BudgetUtilization/RateLimitPolicy/RateLimitUsage tables.
- `migrations/sin/0001_initial.sql` — SIN producer/signal/DLQ tables.
- `docs/design/openapi_sin.yaml` — SIN FastAPI routes.
- `docs/design/openapi_validator.yaml` — Validator Flask routes.
- `docs/design/events_budget_threshold.json` — Budget threshold event schema.
- `docs/design/events_sin_dlq.json` — SIN DLQ event schema.

Validation helper:
- `tools/ci_validate_contracts.ps1` — validates OpenAPI YAML (swagger-cli if present, otherwise YAML parse) and JSON schemas.
- `tools/generate_clients.ps1` — generate typed clients from OpenAPI specs (requires openapi-generator CLI; default generator typescript-fetch).

### Applying SQL migrations (example with psql)
1) Ensure the target database is reachable (PostgreSQL assumed by schema).
2) Budgeting/Rate-Limit:
   ```
   psql "$DATABASE_URL" -f migrations/budgeting_rate_limit/0001_initial.sql
   ```
3) SIN:
   ```
   psql "$DATABASE_URL" -f migrations/sin/0001_initial.sql
   ```

### Alembic (optional)
If you prefer Alembic, you can point a service-specific Alembic environment at the corresponding `migrations/<service>/` directory and treat the SQL file as the first revision. A lightweight pattern:
- Set `script_location` to the service migrations directory.
- In `env.py`, read `DATABASE_URL` and execute the SQL file for the initial revision.

### Contracts
- Use the OpenAPI YAMLs to generate clients or to validate routes in CI.
- Use the JSON Schemas to validate emitted events (budget threshold, SIN DLQ) on the chosen message bus.

### Notes
- No runtime code depends on these files; applying them is a deploy-time decision.
- Retention/TTL, encryption, and isolation policies remain deployment-specific and must be configured per environment.
