-- Alembic-ready SQL for Signal Ingestion Normalization initial schema
-- Matches docs/design/ddl_signal_ingestion_normalization.sql

CREATE TABLE sin_producer (
  producer_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  plane TEXT NOT NULL,
  owner TEXT,
  allowed_signal_kinds TEXT[] NOT NULL,
  allowed_signal_types TEXT[] NOT NULL,
  contract_versions JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_sin_producer_tenant ON sin_producer (tenant_id);


CREATE TABLE sin_signal (
  signal_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  environment TEXT NOT NULL,
  producer_id TEXT NOT NULL REFERENCES sin_producer(producer_id),
  signal_kind TEXT NOT NULL,
  signal_type TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL,
  ingested_at TIMESTAMPTZ NOT NULL,
  payload JSONB NOT NULL,
  schema_version TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_sin_signal_tenant ON sin_signal (tenant_id, producer_id);


CREATE TABLE sin_dlq_entry (
  dlq_id UUID PRIMARY KEY,
  signal_id TEXT,
  tenant_id TEXT,
  producer_id TEXT,
  signal_type TEXT,
  error_code TEXT,
  error_message TEXT,
  retry_count INT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload JSONB
);
CREATE INDEX ix_sin_dlq_filter ON sin_dlq_entry (tenant_id, producer_id, signal_type, created_at);
