-- ZeroUI Core Schema Pack v001 (Postgres)
-- Contract: infra/db/schema_pack/canonical_schema_contract.json

BEGIN;

-- Ensure pgvector extension available across all planes
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;

-- meta schema tracking (no schema namespace)
CREATE SCHEMA IF NOT EXISTS meta;

CREATE TABLE IF NOT EXISTS meta.schema_version (
  schema_pack_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- core schema
CREATE SCHEMA IF NOT EXISTS core;

CREATE TABLE IF NOT EXISTS core.tenant (
  tenant_id TEXT PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.repo (
  repo_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id) ON DELETE RESTRICT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.actor (
  actor_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id) ON DELETE RESTRICT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.receipt_index (
  receipt_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES core.tenant(tenant_id) ON DELETE RESTRICT,
  repo_id TEXT NOT NULL REFERENCES core.repo(repo_id) ON DELETE RESTRICT,
  gate_id TEXT NOT NULL,
  receipt_type TEXT NOT NULL,
  outcome TEXT NOT NULL,
  policy_snapshot_hash TEXT NULL,
  emitted_at TIMESTAMPTZ NOT NULL,
  zu_root_relpath TEXT NOT NULL,
  payload_sha256 TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_receipt_lookup
  ON core.receipt_index (tenant_id, repo_id, gate_id, emitted_at DESC);

CREATE INDEX IF NOT EXISTS idx_receipt_policy_hash
  ON core.receipt_index (policy_snapshot_hash);

-- Background Knowledge Graph (BKG) Edge - Phase 0 Stub
-- Status: Planned (not fully implemented yet)
-- Purpose: Schema placeholder for BKG edges to enable Functional Modules to write receipts/events without ambiguity
CREATE TABLE IF NOT EXISTS core.bkg_edge (
  edge_id TEXT PRIMARY KEY,
  source_entity_type TEXT NOT NULL,
  source_entity_id TEXT NOT NULL,
  target_entity_type TEXT NOT NULL,
  target_entity_id TEXT NOT NULL,
  edge_type TEXT NOT NULL,
  metadata JSONB NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_bkg_edge_source
  ON core.bkg_edge (source_entity_type, source_entity_id);
CREATE INDEX IF NOT EXISTS idx_bkg_edge_target
  ON core.bkg_edge (target_entity_type, target_entity_id);
CREATE INDEX IF NOT EXISTS idx_bkg_edge_type
  ON core.bkg_edge (edge_type);
CREATE INDEX IF NOT EXISTS idx_bkg_edge_source_target
  ON core.bkg_edge (source_entity_type, source_entity_id, target_entity_type, target_entity_id);

-- Record schema version (idempotent upsert)
INSERT INTO meta.schema_version (schema_pack_id, schema_version)
VALUES ('zeroui_core_schema_pack', '001')
ON CONFLICT (schema_pack_id)
DO UPDATE SET schema_version = EXCLUDED.schema_version, applied_at = now();

COMMIT;

