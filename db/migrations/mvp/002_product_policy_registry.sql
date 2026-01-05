-- Product Plane: Policy bundle registry
-- Stores policy snapshot metadata with hash references for verification

CREATE TABLE IF NOT EXISTS app.policy_bundles (
    bundle_id TEXT PRIMARY KEY,
    snapshot_hash TEXT NOT NULL UNIQUE,  -- SHA-256 hash of policy snapshot
    tenant_id TEXT,
    version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_policy_bundles_tenant ON app.policy_bundles(tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_policy_bundles_hash ON app.policy_bundles(snapshot_hash);

COMMENT ON TABLE app.policy_bundles IS 'Policy bundle registry with snapshot hash references. Policy snapshots stored in ZU_ROOT/product/{region}/policy/registry/';

