-- Version: 1.0.0
-- Per PRD: Complete SQL schema matching specification exactly

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Data Classification Table
CREATE TABLE IF NOT EXISTS data_classification (
    data_id UUID PRIMARY KEY,
    data_location VARCHAR(500) NOT NULL,
    classification_level VARCHAR(50) NOT NULL,
    sensitivity_tags JSONB NOT NULL,
    classification_confidence DECIMAL(3,2),
    classified_at TIMESTAMPTZ NOT NULL,
    classified_by UUID NOT NULL,
    tenant_id UUID NOT NULL
);

-- Consent Records Table
CREATE TABLE IF NOT EXISTS consent_records (
    consent_id UUID PRIMARY KEY,
    data_subject_id UUID NOT NULL,
    purpose VARCHAR(255) NOT NULL,
    legal_basis VARCHAR(50) NOT NULL,
    granted_at TIMESTAMPTZ NOT NULL,
    granted_through VARCHAR(100) NOT NULL,
    withdrawal_at TIMESTAMPTZ,
    version VARCHAR(50) NOT NULL,
    tenant_id UUID NOT NULL
);

-- Data Lineage Table
CREATE TABLE IF NOT EXISTS data_lineage (
    lineage_id UUID PRIMARY KEY,
    source_data_id UUID NOT NULL,
    target_data_id UUID NOT NULL,
    transformation_type VARCHAR(100) NOT NULL,
    transformation_details JSONB,
    processed_at TIMESTAMPTZ NOT NULL,
    processed_by UUID NOT NULL,
    tenant_id UUID NOT NULL
);

-- Retention Policies Table
CREATE TABLE IF NOT EXISTS retention_policies (
    policy_id UUID PRIMARY KEY,
    data_category VARCHAR(100) NOT NULL,
    retention_period_months INTEGER NOT NULL,
    legal_hold BOOLEAN DEFAULT FALSE,
    auto_delete BOOLEAN DEFAULT TRUE,
    regulatory_basis VARCHAR(255),
    tenant_id UUID NOT NULL
);

-- Indexing Strategy
-- Primary Indexes / Constraints
CREATE UNIQUE INDEX IF NOT EXISTS idx_data_classification_data_tenant
    ON data_classification (data_id, tenant_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_consent_records_consent_subject
    ON consent_records (consent_id, data_subject_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_data_lineage_lineage_tenant
    ON data_lineage (lineage_id, tenant_id);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_classification_level_tenant
    ON data_classification (classification_level, tenant_id);

CREATE INDEX IF NOT EXISTS idx_consent_subject_purpose
    ON consent_records (data_subject_id, purpose);

CREATE INDEX IF NOT EXISTS idx_lineage_source_transformation
    ON data_lineage (source_data_id, transformation_type);

CREATE INDEX IF NOT EXISTS idx_retention_category_tenant
    ON retention_policies (data_category, tenant_id);

-- Search Indexes
CREATE INDEX IF NOT EXISTS idx_sensitivity_tags_gin
    ON data_classification USING GIN (sensitivity_tags);

CREATE INDEX IF NOT EXISTS idx_data_location_trgm
    ON data_classification USING GIN (data_location gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_regulatory_basis_trgm
    ON retention_policies USING GIN (regulatory_basis gin_trgm_ops);
