-- User Behaviour Intelligence (UBI) Module (EPC-9) - Database Schema
-- Version: 1.0.0
-- Per PRD: Complete SQL schema matching specification exactly

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For GIN trigram indexes

-- Behavioural Events Table (per PRD Section 10.1)
-- Partitioned by tenant_id and dt (date derived from timestamp_utc)
CREATE TABLE IF NOT EXISTS behavioural_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    actor_id VARCHAR(255),
    actor_type VARCHAR(50) NOT NULL CHECK (actor_type IN ('human', 'ai_agent', 'service')),
    source_system VARCHAR(255),
    event_type VARCHAR(255) NOT NULL,
    timestamp_utc TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}',
    privacy_tags JSONB NOT NULL DEFAULT '{}',
    schema_version VARCHAR(50) NOT NULL,
    trace_id VARCHAR(255),
    span_id VARCHAR(255),
    correlation_id VARCHAR(255),
    resource JSONB,
    -- Partitioning column (date derived from timestamp_utc)
    dt DATE NOT NULL GENERATED ALWAYS AS (DATE(timestamp_utc)) STORED,
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (dt);

-- Behavioural Features Table (per PRD Section 10.2)
CREATE TABLE IF NOT EXISTS behavioural_features (
    feature_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    actor_scope VARCHAR(50) NOT NULL CHECK (actor_scope IN ('actor', 'team', 'cohort')),
    actor_or_group_id VARCHAR(255) NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    value DECIMAL(20, 6) NOT NULL,
    dimension VARCHAR(50) NOT NULL,
    confidence DECIMAL(3, 2) NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    metadata JSONB NOT NULL DEFAULT '{}',
    -- Partitioning column
    dt DATE NOT NULL GENERATED ALWAYS AS (DATE(window_end)) STORED,
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (dt);

-- Behavioural Baselines Table (per PRD Section 10.3)
CREATE TABLE IF NOT EXISTS behavioural_baselines (
    baseline_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    actor_scope VARCHAR(50) NOT NULL CHECK (actor_scope IN ('actor', 'team', 'cohort')),
    actor_or_group_id VARCHAR(255) NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    window VARCHAR(50) NOT NULL,
    mean DECIMAL(20, 6) NOT NULL,
    std_dev DECIMAL(20, 6) NOT NULL,
    percentiles JSONB NOT NULL DEFAULT '{}',
    last_recomputed_at TIMESTAMPTZ NOT NULL,
    confidence DECIMAL(3, 2) NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    -- Partitioning column
    dt DATE NOT NULL GENERATED ALWAYS AS (DATE(last_recomputed_at)) STORED,
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (dt);

-- Behavioural Signals Table (per PRD Section 10.4)
CREATE TABLE IF NOT EXISTS behavioural_signals (
    signal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    actor_scope VARCHAR(50) NOT NULL CHECK (actor_scope IN ('actor', 'team', 'cohort', 'tenant')),
    actor_or_group_id VARCHAR(255) NOT NULL,
    dimension VARCHAR(50) NOT NULL,
    signal_type VARCHAR(50) NOT NULL CHECK (signal_type IN ('risk', 'opportunity', 'informational')),
    score DECIMAL(5, 2) NOT NULL CHECK (score >= 0.0 AND score <= 100.0),
    severity VARCHAR(50) NOT NULL CHECK (severity IN ('INFO', 'WARN', 'CRITICAL')),
    status VARCHAR(50) NOT NULL CHECK (status IN ('active', 'resolved')),
    evidence_refs JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ,
    -- Partitioning column
    dt DATE NOT NULL GENERATED ALWAYS AS (DATE(created_at)) STORED,
    -- Metadata
    created_at_meta TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (dt);

-- Tenant Configurations Table (per PRD FR-12)
CREATE TABLE IF NOT EXISTS tenant_configurations (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL UNIQUE,
    config_version VARCHAR(50) NOT NULL,
    enabled_event_categories TEXT[] NOT NULL DEFAULT '{}',
    feature_windows JSONB NOT NULL DEFAULT '{}',
    aggregation_thresholds JSONB NOT NULL DEFAULT '{}',
    enabled_signal_types TEXT[] NOT NULL DEFAULT '{}',
    privacy_settings JSONB NOT NULL DEFAULT '{}',
    anomaly_thresholds JSONB NOT NULL DEFAULT '{}',
    baseline_algorithm JSONB NOT NULL DEFAULT '{}',
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255)
);

-- Receipt Queue Table (per PRD FR-13 - local queue for ERIS unavailability)
CREATE TABLE IF NOT EXISTS receipt_queue (
    queue_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    receipt JSONB NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    next_retry_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Receipt DLQ Table (per PRD FR-13 - dead letter queue for failed receipts)
CREATE TABLE IF NOT EXISTS receipt_dlq (
    dlq_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    receipt JSONB NOT NULL,
    failure_reason TEXT NOT NULL,
    retry_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes per PRD NFR-3 (Scalability)

-- Behavioural Events Indexes
CREATE INDEX IF NOT EXISTS idx_behavioural_events_tenant_actor_timestamp
    ON behavioural_events (tenant_id, actor_id, timestamp_utc);

CREATE INDEX IF NOT EXISTS idx_behavioural_events_tenant_dt
    ON behavioural_events (tenant_id, dt);

CREATE INDEX IF NOT EXISTS idx_behavioural_events_tenant_event_type
    ON behavioural_events (tenant_id, event_type);

CREATE INDEX IF NOT EXISTS idx_behavioural_events_signal_id
    ON behavioural_events (event_id) WHERE event_id IS NOT NULL;

-- Behavioural Features Indexes
CREATE INDEX IF NOT EXISTS idx_behavioural_features_tenant_scope_group
    ON behavioural_features (tenant_id, actor_scope, actor_or_group_id);

CREATE INDEX IF NOT EXISTS idx_behavioural_features_tenant_feature_name
    ON behavioural_features (tenant_id, feature_name);

CREATE INDEX IF NOT EXISTS idx_behavioural_features_tenant_dimension
    ON behavioural_features (tenant_id, dimension);

CREATE INDEX IF NOT EXISTS idx_behavioural_features_tenant_dt
    ON behavioural_features (tenant_id, dt);

CREATE INDEX IF NOT EXISTS idx_behavioural_features_window
    ON behavioural_features (window_start, window_end);

-- Behavioural Baselines Indexes
CREATE INDEX IF NOT EXISTS idx_behavioural_baselines_tenant_scope_group
    ON behavioural_baselines (tenant_id, actor_scope, actor_or_group_id);

CREATE INDEX IF NOT EXISTS idx_behavioural_baselines_tenant_feature_name
    ON behavioural_baselines (tenant_id, feature_name);

CREATE INDEX IF NOT EXISTS idx_behavioural_baselines_tenant_dt
    ON behavioural_baselines (tenant_id, dt);

-- Behavioural Signals Indexes
CREATE INDEX IF NOT EXISTS idx_behavioural_signals_tenant_scope_group
    ON behavioural_signals (tenant_id, actor_scope, actor_or_group_id);

CREATE INDEX IF NOT EXISTS idx_behavioural_signals_tenant_dimension
    ON behavioural_signals (tenant_id, dimension);

CREATE INDEX IF NOT EXISTS idx_behavioural_signals_tenant_severity
    ON behavioural_signals (tenant_id, severity);

CREATE INDEX IF NOT EXISTS idx_behavioural_signals_tenant_status
    ON behavioural_signals (tenant_id, status);

CREATE INDEX IF NOT EXISTS idx_behavioural_signals_tenant_dt
    ON behavioural_signals (tenant_id, dt);

CREATE INDEX IF NOT EXISTS idx_behavioural_signals_created_at
    ON behavioural_signals (created_at);

-- Receipt Queue Indexes
CREATE INDEX IF NOT EXISTS idx_receipt_queue_tenant_next_retry
    ON receipt_queue (tenant_id, next_retry_at);

CREATE INDEX IF NOT EXISTS idx_receipt_queue_next_retry
    ON receipt_queue (next_retry_at);

-- Receipt DLQ Indexes
CREATE INDEX IF NOT EXISTS idx_receipt_dlq_tenant_created
    ON receipt_dlq (tenant_id, created_at);

-- GIN Indexes for JSONB fields
CREATE INDEX IF NOT EXISTS idx_behavioural_events_properties_gin
    ON behavioural_events USING GIN (properties);

CREATE INDEX IF NOT EXISTS idx_behavioural_events_privacy_tags_gin
    ON behavioural_events USING GIN (privacy_tags);

CREATE INDEX IF NOT EXISTS idx_behavioural_features_metadata_gin
    ON behavioural_features USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_behavioural_signals_evidence_refs_gin
    ON behavioural_signals USING GIN (evidence_refs);

-- Partition Management Function (for automatic partition creation)
-- Note: In production, partitions should be created proactively or via scheduled job
CREATE OR REPLACE FUNCTION create_partition_if_not_exists(
    table_name TEXT,
    partition_date DATE
) RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    partition_start DATE;
    partition_end DATE;
BEGIN
    partition_name := table_name || '_' || TO_CHAR(partition_date, 'YYYY_MM_DD');
    partition_start := DATE_TRUNC('month', partition_date);
    partition_end := partition_start + INTERVAL '1 month';
    
    -- Check if partition exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_class WHERE relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            table_name,
            partition_start,
            partition_end
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

