-- Contracts & Schema Registry Module (M34) - Production Database Schema
-- Version: 1.2.0
-- Per PRD: Complete SQL schema matching specification exactly

-- Enable required extensions for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For GIN trigram indexes

-- Schemas Table
CREATE TABLE schemas (
    schema_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    namespace VARCHAR(255) NOT NULL,
    schema_type VARCHAR(50) NOT NULL,
    schema_definition JSONB NOT NULL,
    version VARCHAR(50) NOT NULL,
    compatibility VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    tenant_id UUID NOT NULL,
    metadata JSONB
);

-- Contracts Table
CREATE TABLE contracts (
    contract_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    schema_id UUID REFERENCES schemas(schema_id),
    validation_rules JSONB NOT NULL,
    enforcement_level VARCHAR(20) NOT NULL,
    violation_actions JSONB NOT NULL,
    version VARCHAR(50) NOT NULL,
    tenant_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL
);

-- Schema Dependencies Table
CREATE TABLE schema_dependencies (
    parent_schema_id UUID REFERENCES schemas(schema_id),
    child_schema_id UUID REFERENCES schemas(schema_id),
    dependency_type VARCHAR(50) NOT NULL,
    PRIMARY KEY (parent_schema_id, child_schema_id)
);

-- Schema Analytics Table
CREATE TABLE schema_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_id UUID NOT NULL REFERENCES schemas(schema_id),
    tenant_id UUID NOT NULL,
    period VARCHAR(20) NOT NULL CHECK (period IN ('hourly', 'daily', 'weekly', 'monthly')),
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    metrics JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (schema_id, tenant_id, period, period_start)
);

-- Constraints per PRD
ALTER TABLE schemas ADD CONSTRAINT schemas_tenant_name_version_unique UNIQUE (tenant_id, name, version);
ALTER TABLE schemas ADD CONSTRAINT schemas_schema_type_check CHECK (schema_type IN ('json_schema', 'avro', 'protobuf'));
ALTER TABLE schemas ADD CONSTRAINT schemas_compatibility_check CHECK (compatibility IN ('backward', 'forward', 'full', 'none'));
ALTER TABLE schemas ADD CONSTRAINT schemas_status_check CHECK (status IN ('draft', 'published', 'deprecated'));
ALTER TABLE contracts ADD CONSTRAINT contracts_type_check CHECK (type IN ('api', 'event', 'data'));
ALTER TABLE contracts ADD CONSTRAINT contracts_enforcement_level_check CHECK (enforcement_level IN ('strict', 'warning', 'advisory'));

-- Search indexes per PRD
-- Note: GIN indexes require pg_trgm extension
CREATE INDEX idx_schemas_namespace_gin ON schemas USING GIN (namespace gin_trgm_ops);
CREATE INDEX idx_schemas_metadata_tags ON schemas USING GIN ((metadata->'tags'));

-- Performance indexes per PRD
CREATE INDEX idx_schemas_type_status ON schemas(schema_type, status);
CREATE INDEX idx_schemas_created_at_brin ON schemas USING BRIN (created_at);
CREATE INDEX idx_schemas_tenant_status ON schemas(tenant_id, status);

-- Contracts indexes per PRD
CREATE INDEX idx_contracts_schema_id ON contracts(schema_id);
CREATE INDEX idx_contracts_tenant_id ON contracts(tenant_id);
CREATE INDEX idx_contracts_type ON contracts(type);
CREATE INDEX idx_contracts_created_at ON contracts(created_at);

-- Schema dependencies indexes per PRD
CREATE INDEX idx_schema_deps_parent ON schema_dependencies(parent_schema_id);
CREATE INDEX idx_schema_deps_child ON schema_dependencies(child_schema_id);

-- Analytics indexes per PRD
CREATE INDEX idx_schema_analytics_schema_tenant ON schema_analytics(schema_id, tenant_id);
CREATE INDEX idx_schema_analytics_period ON schema_analytics(period, period_start);
CREATE INDEX idx_schema_analytics_tenant_period ON schema_analytics(tenant_id, period, period_start);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_schemas_updated_at BEFORE UPDATE ON schemas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contracts_updated_at BEFORE UPDATE ON contracts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
