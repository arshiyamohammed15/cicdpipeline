-- Version: 1.0.0
-- ERIS Database Schema per PRD Section 8

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Receipts Table (PRD Section 8.1)
CREATE TABLE IF NOT EXISTS receipts (
    -- Canonical Receipt Fields
    receipt_id UUID PRIMARY KEY,
    gate_id VARCHAR(255) NOT NULL,
    schema_version VARCHAR(50) NOT NULL,
    policy_version_ids TEXT[] NOT NULL,
    snapshot_hash VARCHAR(255) NOT NULL,
    timestamp_utc TIMESTAMPTZ NOT NULL,
    timestamp_monotonic_ms BIGINT NOT NULL,
    evaluation_point VARCHAR(50) NOT NULL,
    inputs JSONB NOT NULL,
    decision_status VARCHAR(50) NOT NULL,
    decision_rationale TEXT NOT NULL,
    decision_badges TEXT[],
    result JSONB,
    actor_repo_id VARCHAR(255) NOT NULL,
    actor_machine_fingerprint VARCHAR(255),
    actor_type VARCHAR(50),
    evidence_handles JSONB,
    degraded BOOLEAN DEFAULT FALSE,
    signature TEXT NOT NULL,
    
    -- ERIS-Specific Indexing Fields
    tenant_id VARCHAR(255) NOT NULL,
    plane VARCHAR(100),
    environment VARCHAR(50),
    module_id VARCHAR(255),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    severity VARCHAR(50),
    risk_score DECIMAL(10, 2),
    
    -- Cryptographic Integrity
    hash VARCHAR(255) NOT NULL,
    prev_hash VARCHAR(255),
    chain_id VARCHAR(500) NOT NULL,
    signature_algo VARCHAR(50),
    kid VARCHAR(255),
    signature_verification_status VARCHAR(50),
    
    -- Receipt Linking
    parent_receipt_id UUID,
    related_receipt_ids UUID[],
    
    -- Source
    emitter_service VARCHAR(255),
    ingest_source VARCHAR(100),
    
    -- Time Partitioning
    dt DATE NOT NULL,
    
    -- Retention
    retention_state VARCHAR(50) DEFAULT 'active',
    legal_hold BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Courier Batches Table (PRD Section 8.3)
CREATE TABLE IF NOT EXISTS courier_batches (
    batch_id UUID PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    emitter_service VARCHAR(255) NOT NULL,
    merkle_root VARCHAR(255) NOT NULL,
    sequence_numbers TEXT[] NOT NULL,
    receipt_count INTEGER NOT NULL,
    leaf_hashes TEXT[] NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Meta Receipts Table (FR-9 Access Audit)
CREATE TABLE IF NOT EXISTS meta_receipts (
    access_event_id UUID PRIMARY KEY,
    requester_actor_id VARCHAR(255) NOT NULL,
    actor_type VARCHAR(50) NOT NULL,
    requester_role VARCHAR(100),
    tenant_ids TEXT[] NOT NULL,
    plane VARCHAR(100),
    environment VARCHAR(50),
    timestamp TIMESTAMPTZ NOT NULL,
    query_scope TEXT,
    decision VARCHAR(50) NOT NULL,
    receipt_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Export Jobs Table (FR-11 Export Tracking)
CREATE TABLE IF NOT EXISTS export_jobs (
    export_id UUID PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    export_format VARCHAR(50) NOT NULL,
    compression VARCHAR(50),
    filters JSONB,
    download_url TEXT,
    receipt_count INTEGER,
    file_size BIGINT,
    checksum VARCHAR(255),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Indexes per PRD Section 8.2

-- Primary Index
CREATE UNIQUE INDEX IF NOT EXISTS idx_receipts_tenant_id_receipt_id
    ON receipts (tenant_id, receipt_id);

CREATE INDEX IF NOT EXISTS idx_receipts_tenant_timestamp_receipt
    ON receipts (tenant_id, timestamp_utc, receipt_id);

-- Secondary Indexes
CREATE INDEX IF NOT EXISTS idx_receipts_tenant_dt_plane_env
    ON receipts (tenant_id, dt, plane, environment);

CREATE INDEX IF NOT EXISTS idx_receipts_tenant_gate_dt
    ON receipts (tenant_id, gate_id, dt);

CREATE INDEX IF NOT EXISTS idx_receipts_tenant_module_dt
    ON receipts (tenant_id, module_id, dt) WHERE module_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_receipts_tenant_actor_repo_dt
    ON receipts (tenant_id, actor_repo_id, dt);

CREATE INDEX IF NOT EXISTS idx_receipts_tenant_resource_dt
    ON receipts (tenant_id, resource_type, resource_id, dt)
    WHERE resource_type IS NOT NULL AND resource_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_receipts_tenant_decision_severity_dt
    ON receipts (tenant_id, decision_status, severity, dt)
    WHERE severity IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_receipts_tenant_chain_timestamp
    ON receipts (tenant_id, chain_id, timestamp_utc);

CREATE INDEX IF NOT EXISTS idx_receipts_parent_receipt_id
    ON receipts (parent_receipt_id) WHERE parent_receipt_id IS NOT NULL;

-- GIN Index for Array Fields
CREATE INDEX IF NOT EXISTS idx_receipts_policy_version_ids_gin
    ON receipts USING GIN (policy_version_ids);

CREATE INDEX IF NOT EXISTS idx_receipts_related_receipt_ids_gin
    ON receipts USING GIN (related_receipt_ids) WHERE related_receipt_ids IS NOT NULL;

-- Courier Batch Indexes
CREATE INDEX IF NOT EXISTS idx_courier_batches_tenant_timestamp
    ON courier_batches (tenant_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_courier_batches_status
    ON courier_batches (status);

-- Meta Receipt Indexes
CREATE INDEX IF NOT EXISTS idx_meta_receipts_tenant_timestamp
    ON meta_receipts USING GIN (tenant_ids);

CREATE INDEX IF NOT EXISTS idx_meta_receipts_requester_timestamp
    ON meta_receipts (requester_actor_id, timestamp);

-- Export Job Indexes
CREATE INDEX IF NOT EXISTS idx_export_jobs_tenant_status
    ON export_jobs (tenant_id, status);

CREATE INDEX IF NOT EXISTS idx_export_jobs_created_at
    ON export_jobs (created_at);

-- DLQ Entries Table (FR-2 Dead Letter Queue)
CREATE TABLE IF NOT EXISTS dlq_entries (
    dlq_entry_id UUID PRIMARY KEY,
    tenant_id VARCHAR(255),
    receipt JSONB NOT NULL,
    rejection_reason TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dlq_entries_tenant_timestamp
    ON dlq_entries (tenant_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_dlq_entries_expires_at
    ON dlq_entries (expires_at);

