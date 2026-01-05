-- Tenant Plane: Receipts index table (metadata only; raw receipts remain JSONL on disk)
-- This table indexes receipt metadata for querying; the source of truth is JSONL files in ZU_ROOT/tenant/{tenant-id}/{region}/evidence/data/

CREATE TABLE IF NOT EXISTS app.receipts_index (
    receipt_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    repo_id TEXT,
    receipt_path TEXT NOT NULL,  -- Path to JSONL file relative to ZU_ROOT
    receipt_hash TEXT NOT NULL,   -- SHA-256 hash of receipt content
    timestamp_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_receipts_tenant_timestamp ON app.receipts_index(tenant_id, timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_receipts_repo ON app.receipts_index(repo_id) WHERE repo_id IS NOT NULL;

COMMENT ON TABLE app.receipts_index IS 'Index table for tenant receipts. Raw receipts stored as JSONL in ZU_ROOT/tenant/{tenant-id}/{region}/evidence/data/';

