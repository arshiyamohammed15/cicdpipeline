# Alerting & Notification Service Migrations

The default persistence layer for Alerting & Notification Service uses SQLite (`sqlite+aiosqlite:///./alerting.db`).  
Phase 1 added new columns across every core table. Apply `001_extend_schema.sql`
before deploying the updated service against an existing database.

## Applying to the default SQLite database
Run the helper script from repo root:
```bash
python scripts/db/apply_alerting_notification_service_migration.py --db alerting.db
```
Or manually:
```bash
cd src/cloud_services/shared-services/alerting-notification-service/database
sqlite3 ../../../../../../alerting.db < migrations/001_extend_schema.sql
```

## Applying to another RDBMS
Translate the `ALTER TABLE ... ADD COLUMN` statements in
`001_extend_schema.sql` to your database dialect (e.g., PostgreSQL) using
the equivalents for JSON/TEXT columns.

## Verification checklist
1. Backup the existing database (or apply in staging first).
2. Run the SQL script.
3. Restart the service so SQLModel metadata reflects the new columns.
4. Run the alerting service test suite:
   `python -m pytest src/cloud_services/shared-services/alerting-notification-service/tests`.

