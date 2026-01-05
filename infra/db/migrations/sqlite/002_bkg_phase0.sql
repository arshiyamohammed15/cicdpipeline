-- Background Knowledge Graph (BKG) - Phase 0 Stub (SQLite)
-- Status: Planned (not fully implemented yet)
-- Purpose: Schema placeholder for BKG edges to enable Functional Modules to write receipts/events without ambiguity
--
-- BKG edges connect entities (tenant, repo, actor, receipt, policy, etc.) to form a knowledge graph.
-- Full graph logic (traversal, querying, inference) is not yet implemented.
-- This stub provides the schema contract so FMs can reference BKG edges in receipts/events.

-- BKG Edge (using core__ prefix for schema emulation)
-- Stores directed edges between entities in the knowledge graph
CREATE TABLE IF NOT EXISTS core__bkg_edge (
    edge_id TEXT PRIMARY KEY,
    source_entity_type TEXT NOT NULL,  -- e.g., 'tenant', 'repo', 'actor', 'receipt', 'policy'
    source_entity_id TEXT NOT NULL,    -- ID of source entity
    target_entity_type TEXT NOT NULL,  -- e.g., 'tenant', 'repo', 'actor', 'receipt', 'policy'
    target_entity_id TEXT NOT NULL,    -- ID of target entity
    edge_type TEXT NOT NULL,            -- e.g., 'owns', 'contains', 'triggers', 'references', 'depends_on'
    metadata TEXT NULL,                 -- Optional: edge-specific metadata (JSON stored as TEXT in SQLite)
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_bkg_edge_source ON core__bkg_edge(source_entity_type, source_entity_id);
CREATE INDEX IF NOT EXISTS idx_bkg_edge_target ON core__bkg_edge(target_entity_type, target_entity_id);
CREATE INDEX IF NOT EXISTS idx_bkg_edge_type ON core__bkg_edge(edge_type);
CREATE INDEX IF NOT EXISTS idx_bkg_edge_source_target ON core__bkg_edge(source_entity_type, source_entity_id, target_entity_type, target_entity_id);

