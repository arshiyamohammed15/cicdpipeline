-- Health & Reliability Monitoring initial schema migration
CREATE TABLE IF NOT EXISTS health_reliability_monitoring_components (
    component_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    component_type TEXT NOT NULL,
    plane TEXT NOT NULL,
    environment TEXT NOT NULL,
    tenant_scope TEXT NOT NULL,
    metrics_profile JSON NOT NULL DEFAULT ('[]'),
    health_policies JSON NOT NULL DEFAULT ('[]'),
    slo_target REAL,
    error_budget_minutes INTEGER,
    owner_team TEXT,
    documentation_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS health_reliability_monitoring_component_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id TEXT NOT NULL,
    dependency_id TEXT NOT NULL,
    critical BOOLEAN DEFAULT 1,
    FOREIGN KEY (component_id) REFERENCES health_reliability_monitoring_components(component_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS health_reliability_monitoring_health_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    component_id TEXT NOT NULL,
    tenant_id TEXT,
    plane TEXT NOT NULL,
    environment TEXT NOT NULL,
    state TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    metrics_summary JSON NOT NULL DEFAULT ('{}'),
    slo_state TEXT,
    policy_version TEXT,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (component_id) REFERENCES health_reliability_monitoring_components(component_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_health_reliability_monitoring_snapshots_component ON health_reliability_monitoring_health_snapshots(component_id);
CREATE INDEX IF NOT EXISTS idx_health_reliability_monitoring_snapshots_evaluated_at ON health_reliability_monitoring_health_snapshots(evaluated_at);

CREATE TABLE IF NOT EXISTS health_reliability_monitoring_slo_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id TEXT NOT NULL,
    slo_id TEXT NOT NULL,
    window TEXT NOT NULL,
    sli_values JSON NOT NULL DEFAULT ('{}'),
    error_budget_total_minutes INTEGER,
    error_budget_consumed_minutes INTEGER,
    burn_rate REAL,
    state TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_health_reliability_monitoring_slo_component ON health_reliability_monitoring_slo_status(component_id);

