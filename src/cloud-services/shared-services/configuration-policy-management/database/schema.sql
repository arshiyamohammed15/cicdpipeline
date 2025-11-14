-- Configuration & Policy Management Module (M23) - Production Database Schema
-- Version: 1.1.0
-- Per PRD: Complete SQL schema matching specification exactly (lines 128-186)

-- Enable required extensions for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For GIN trigram indexes

-- Policies Table (PRD lines 218-233)
CREATE TABLE policies (
    policy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    policy_type VARCHAR(50) NOT NULL,
    policy_definition JSONB NOT NULL,
    version VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    scope JSONB NOT NULL,
    enforcement_level VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    tenant_id UUID NOT NULL,
    metadata JSONB
);

-- Configurations Table (PRD lines 236-247)
CREATE TABLE configurations (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    config_type VARCHAR(50) NOT NULL,
    config_definition JSONB NOT NULL,
    version VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    deployed_at TIMESTAMPTZ,
    deployed_by UUID,
    tenant_id UUID NOT NULL,
    environment VARCHAR(50) NOT NULL
);

-- Gold Standards Table (PRD lines 250-259)
CREATE TABLE gold_standards (
    standard_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    framework VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    control_definitions JSONB NOT NULL,
    compliance_rules JSONB NOT NULL,
    evidence_requirements JSONB NOT NULL,
    tenant_id UUID NOT NULL
);

-- Constraints per PRD
ALTER TABLE policies ADD CONSTRAINT policies_policy_type_check CHECK (policy_type IN ('security', 'compliance', 'operational', 'governance'));
ALTER TABLE policies ADD CONSTRAINT policies_status_check CHECK (status IN ('draft', 'review', 'approved', 'active', 'deprecated'));
ALTER TABLE policies ADD CONSTRAINT policies_enforcement_level_check CHECK (enforcement_level IN ('advisory', 'warning', 'enforcement'));

ALTER TABLE configurations ADD CONSTRAINT configurations_config_type_check CHECK (config_type IN ('security', 'performance', 'feature', 'compliance'));
ALTER TABLE configurations ADD CONSTRAINT configurations_status_check CHECK (status IN ('draft', 'staging', 'active', 'deprecated'));
ALTER TABLE configurations ADD CONSTRAINT configurations_environment_check CHECK (environment IN ('production', 'staging', 'development'));

ALTER TABLE gold_standards ADD CONSTRAINT gold_standards_framework_check CHECK (framework IN ('soc2', 'gdpr', 'hipaa', 'nist', 'custom'));

-- Primary indexes per PRD (lines 264-266)
CREATE INDEX idx_policies_policy_id_tenant_id ON policies(policy_id, tenant_id);
CREATE INDEX idx_configurations_config_id_env_tenant ON configurations(config_id, environment, tenant_id);
CREATE INDEX idx_gold_standards_standard_id_framework_tenant ON gold_standards(standard_id, framework, tenant_id);

-- Performance indexes per PRD (lines 268-270)
CREATE INDEX idx_policies_type_status_tenant ON policies(policy_type, status, tenant_id);
CREATE INDEX idx_configurations_type_status_env ON configurations(config_type, status, environment);
CREATE INDEX idx_gold_standards_framework_version_tenant ON gold_standards(framework, version, tenant_id);

-- Search indexes per PRD (lines 184-186) - GIN indexes for JSONB
CREATE INDEX idx_policies_definition_gin ON policies USING GIN (policy_definition);
CREATE INDEX idx_configurations_definition_gin ON configurations USING GIN (config_definition);
CREATE INDEX idx_gold_standards_control_definitions_gin ON gold_standards USING GIN (control_definitions);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
