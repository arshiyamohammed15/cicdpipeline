-- Budgeting & Rate Limiting (observed entities from code/tests)
-- PostgreSQL-compatible DDL; no speculative fields added.

CREATE TABLE budget_definition (
  budget_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  budget_name TEXT NOT NULL,
  budget_type TEXT NOT NULL,
  budget_amount NUMERIC(18,4) NOT NULL,
  currency TEXT NOT NULL DEFAULT 'USD',
  period_type TEXT NOT NULL,
  start_date TIMESTAMPTZ NOT NULL,
  end_date TIMESTAMPTZ,
  allocated_to_type TEXT NOT NULL,
  allocated_to_id UUID NOT NULL,
  enforcement_action TEXT NOT NULL,
  thresholds JSONB NOT NULL DEFAULT '{}',
  notifications JSONB NOT NULL DEFAULT '{}',
  created_by UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_budget_tenant_lookup
  ON budget_definition (tenant_id, allocated_to_type, allocated_to_id);

CREATE INDEX ix_budget_active
  ON budget_definition (tenant_id, start_date, end_date);


CREATE TABLE budget_utilization (
  utilization_id UUID PRIMARY KEY,
  budget_id UUID NOT NULL REFERENCES budget_definition(budget_id) ON DELETE CASCADE,
  tenant_id UUID NOT NULL,
  period_start TIMESTAMPTZ NOT NULL,
  period_end TIMESTAMPTZ NOT NULL,
  spent_amount NUMERIC(18,4) NOT NULL,
  last_updated TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (budget_id, period_start, period_end)
);

CREATE INDEX ix_budget_utilization_lookup
  ON budget_utilization (budget_id, period_start, period_end);


CREATE TABLE rate_limit_policy (
  policy_id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  scope_type TEXT NOT NULL,
  scope_id UUID NOT NULL,
  resource_type TEXT NOT NULL,
  limit_value BIGINT NOT NULL,
  time_window_seconds INT NOT NULL,
  algorithm TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_rl_policy_scope
  ON rate_limit_policy (tenant_id, scope_type, scope_id, resource_type);


-- Optional persistence for rate-limit counters (token bucket style)
CREATE TABLE rate_limit_usage (
  usage_id UUID PRIMARY KEY,
  policy_id UUID NOT NULL REFERENCES rate_limit_policy(policy_id) ON DELETE CASCADE,
  window_start TIMESTAMPTZ NOT NULL,
  count BIGINT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (policy_id, window_start)
);
