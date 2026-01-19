-- Background Knowledge Graph (BKG) - Phase 0 Stub (SQLite)
-- Status: Planned (not fully implemented yet)
-- Purpose: Schema placeholder for BKG edges to enable Functional Modules to write receipts/events without ambiguity
--
-- BKG edges connect entities (tenant, repo, actor, receipt, policy, etc.) to form a knowledge graph.
-- Full graph logic (traversal, querying, inference) is not yet implemented.
-- This stub provides the schema contract so FMs can reference BKG edges in receipts/events.
-- SQLite: core.bkg_edge -> core__bkg_edge; JSONB -> TEXT; TIMESTAMPTZ/now() -> TEXT/datetime('now').

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

CREATE INDEX IF NOT EXISTS idx_bkg_edge_source ON core__bkg_edge(source_entity_type, source_entity_id);
CREATE INDEX IF NOT EXISTS idx_bkg_edge_target ON core__bkg_edge(target_entity_type, target_entity_id);
CREATE INDEX IF NOT EXISTS idx_bkg_edge_type ON core__bkg_edge(edge_type);
CREATE INDEX IF NOT EXISTS idx_bkg_edge_source_target ON core__bkg_edge(source_entity_type, source_entity_id, target_entity_type, target_entity_id);
