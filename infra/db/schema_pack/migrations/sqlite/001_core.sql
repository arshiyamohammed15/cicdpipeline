-- ZeroUI Core Schema Pack v001 (SQLite)
-- Contract: infra/db/schema_pack/canonical_schema_contract.json

BEGIN;

CREATE TABLE IF NOT EXISTS meta__schema_version (
  schema_pack_id TEXT PRIMARY KEY,
  schema_version TEXT NOT NULL,
  applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS core__tenant (
  tenant_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS core__repo (
  repo_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS core__actor (
  actor_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS core__receipt_index (
  receipt_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  repo_id TEXT NOT NULL,
  gate_id TEXT NOT NULL,
  receipt_type TEXT NOT NULL,
  outcome TEXT NOT NULL,
  policy_snapshot_hash TEXT NULL,
  emitted_at TEXT NOT NULL,
  zu_root_relpath TEXT NOT NULL,
  payload_sha256 TEXT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_receipt_lookup
  ON core__receipt_index (tenant_id, repo_id, gate_id, emitted_at);

CREATE INDEX IF NOT EXISTS idx_receipt_policy_hash
  ON core__receipt_index (policy_snapshot_hash);

-- Background Knowledge Graph (BKG) Edge - Phase 0 Stub
-- Status: Planned (not fully implemented yet)
-- Purpose: Schema placeholder for BKG edges to enable Functional Modules to write receipts/events without ambiguity
CREATE TABLE IF NOT EXISTS core__bkg_edge (
  edge_id TEXT PRIMARY KEY,
  source_entity_type TEXT NOT NULL,
  source_entity_id TEXT NOT NULL,
  target_entity_type TEXT NOT NULL,
  target_entity_id TEXT NOT NULL,
  edge_type TEXT NOT NULL,
  metadata TEXT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_bkg_edge_source
  ON core__bkg_edge (source_entity_type, source_entity_id);
CREATE INDEX IF NOT EXISTS idx_bkg_edge_target
  ON core__bkg_edge (target_entity_type, target_entity_id);
CREATE INDEX IF NOT EXISTS idx_bkg_edge_type
  ON core__bkg_edge (edge_type);
CREATE INDEX IF NOT EXISTS idx_bkg_edge_source_target
  ON core__bkg_edge (source_entity_type, source_entity_id, target_entity_type, target_entity_id);

INSERT INTO meta__schema_version (schema_pack_id, schema_version)
VALUES ('zeroui_core_schema_pack', '001')
ON CONFLICT(schema_pack_id)
DO UPDATE SET schema_version=excluded.schema_version, applied_at=datetime('now');

COMMIT;

