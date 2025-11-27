-- MMM Engine Database Schema (PM-1)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS mmm_playbooks (
    playbook_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    description TEXT,
    triggers JSONB NOT NULL DEFAULT '[]'::jsonb,
    conditions JSONB NOT NULL DEFAULT '[]'::jsonb,
    actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    limits JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_playbooks_tenant ON mmm_playbooks (tenant_id);
CREATE INDEX IF NOT EXISTS idx_playbooks_status ON mmm_playbooks (tenant_id, status);

CREATE TABLE IF NOT EXISTS mmm_decisions (
    decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    actor_id VARCHAR(255),
    actor_type VARCHAR(50) NOT NULL DEFAULT 'human',
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    signal_reference JSONB,
    policy_snapshot_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_decisions_tenant ON mmm_decisions (tenant_id, created_at);

CREATE TABLE IF NOT EXISTS mmm_actions (
    action_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_id UUID NOT NULL REFERENCES mmm_decisions(decision_id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    surfaces JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    requires_consent BOOLEAN NOT NULL DEFAULT FALSE,
    requires_dual_channel BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mmm_outcomes (
    outcome_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_id UUID NOT NULL REFERENCES mmm_decisions(decision_id) ON DELETE CASCADE,
    action_id UUID NOT NULL,
    actor_id VARCHAR(255),
    result VARCHAR(50) NOT NULL,
    reason TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mmm_experiments (
    experiment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_experiments_tenant ON mmm_experiments (tenant_id, status);


