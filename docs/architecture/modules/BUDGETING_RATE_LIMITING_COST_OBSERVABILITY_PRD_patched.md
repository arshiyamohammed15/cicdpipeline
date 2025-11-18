ZEROUI PRODUCT REQUIREMENTS DOCUMENT
MODULE: BUDGETING, RATE-LIMITING & COST OBSERVABILITY
MODULE ID: M35
VERSION: 3.0.0
STATUS: ✅ READY FOR IMPLEMENTATION
VALIDATION: All 35 issues resolved (12 CRITICAL, 8 HIGH, 15 MEDIUM) - Gold Standard Quality
VALIDATION_DATE: 2025-01-27

Module Identity
json
{
  "module_id": "M35",
  "name": "Budgeting, Rate-Limiting & Cost Observability",
  "version": "1.0.0",
  "description": "Real-time resource budgeting, rate-limiting enforcement, and cost transparency for ZeroUI ecosystem",
  "supported_events": [
    "budget_threshold_exceeded",
    "rate_limit_violated",
    "cost_anomaly_detected",
    "quota_allocated",
    "quota_exhausted",
    "resource_usage_optimized"
  ],
  "policy_categories": ["financial_governance", "resource_management", "cost_optimization"],
  "api_endpoints": {
    "health": "/budget/v1/health",
    "metrics": "/budget/v1/metrics",
    "budgets": "/budget/v1/budgets",
    "budgets_check": "/budget/v1/budgets/check",
    "rate_limits": "/budget/v1/rate-limits",
    "rate_limits_check": "/budget/v1/rate-limits/check",
    "cost_tracking": "/budget/v1/cost-tracking",
    "cost_tracking_record": "/budget/v1/cost-tracking/record",
    "cost_tracking_reports": "/budget/v1/cost-tracking/reports",
    "quotas": "/budget/v1/quotas",
    "quotas_allocate": "/budget/v1/quotas/allocate",
    "alerts": "/budget/v1/alerts",
    "event_subscriptions": "/budget/v1/event-subscriptions"
  },
  "performance_requirements": {
    "budget_check_ms_max": 10,
    "rate_limit_check_ms_max": 5,
    "cost_calculation_ms_max": 50,
    "max_memory_mb": 2048
  }
}

Core Function
Enterprise-grade resource budgeting, rate-limiting enforcement, and cost observability system that provides real-time financial governance, resource allocation control, and cost transparency across all ZeroUI modules and tenant deployments.

Architecture Principles
1. Real-Time Enforcement
text
Resource Usage → Budget Check → Rate Limit Check → Cost Calculation → Enforcement
Proactive Budget Controls: Pre-execution budget validation for all resource-intensive operations
Dynamic Rate Limiting: Context-aware throttling based on usage patterns and priorities
Immediate Cost Attribution: Real-time cost assignment to tenants, users, and features
2. Multi-Dimensional Cost Tracking
text
Infrastructure Costs → Service Usage → Feature Utilization → Tenant Allocation
Granular Cost Breakdown: Per-tenant, per-user, per-feature cost attribution
Cross-Cloud Cost Aggregation: Unified cost tracking across client cloud and product cloud
Predictive Cost Forecasting: ML-based cost prediction and anomaly detection
3. Policy-Driven Governance
text
Policy Definition → Automated Enforcement → Exception Handling → Optimization
Flexible Budget Policies: Time-bound, rolling, and project-specific budgets
Automated Remediation: Pre-defined actions for budget violations
Optimization Recommendations: AI-driven cost optimization suggestions

Functional Components
1. Budget Management Engine
yaml
budget_management:
  budget_types:
    - "Tenant-level monthly budgets"
    - "Project-level sprint budgets"
    - "User-level resource quotas"
    - "Feature-level cost caps"
  budget_periods:
    - "Monthly rolling"
    - "Quarterly fixed"
    - "Project duration"
    - "Custom time windows"
  period_calculation:
    monthly_rolling:
      description: "Rolling 30-day window from first usage or budget start"
      calculation: "period_start = first_usage_date OR budget.start_date, period_end = period_start + 30 days"
      reset: "Automatic rollover every 30 days"
    quarterly_fixed:
      description: "Fixed calendar quarters (Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec)"
      calculation: "period_start = quarter start date, period_end = quarter end date"
      reset: "Reset at quarter boundary"
    project_duration:
      description: "Budget spans entire project lifecycle"
      calculation: "period_start = project.start_date, period_end = project.end_date"
      reset: "No automatic reset, manual closure required"
    custom_time_windows:
      description: "User-defined start and end dates"
      calculation: "period_start = user_defined_start, period_end = user_defined_end"
      reset: "Manual reset or renewal based on auto_renew flag"
  overlapping_periods:
    resolution: "Most restrictive budget applies (lowest budget_amount)"
    priority: "Feature > User > Project > Tenant (most specific to least specific)"
  enforcement_actions:
    hard_stop:
      description: "Immediately block all operations when budget exhausted"
      behavior: "Return BUDGET_EXCEEDED error, no operations allowed"
    soft_limit:
      description: "Allow operations but send notifications"
      behavior: "Continue operations, emit alerts at thresholds"
    throttle:
      description: "Gradually reduce operation rate as budget approaches limit"
      behavior: "Apply rate limiting multiplier based on utilization ratio"
    escalate:
      description: "Require approval workflow for operations exceeding budget"
      behavior: "Route to approval queue, await authorization before proceeding"
  approval_workflow:
    states: ["pending", "approved", "rejected", "expired"]
    roles: ["financial_controller", "tenant_admin"]
    timeout: "24 hours default, configurable per budget"
    notifications: "Email and IDE notifications on state changes"
2. Rate-Limiting Framework
yaml
rate_limiting:
  limit_dimensions:
    - "API calls per second"
    - "Compute minutes per hour"
    - "Storage operations per day"
    - "AI inference requests per minute"
  algorithms:
    token_bucket:
      description: "Token bucket algorithm with configurable refill rate"
      parameters:
        capacity: "Maximum tokens (limit_value)"
        refill_rate: "Tokens per time_window_seconds"
        burst_capacity: "Additional tokens for burst handling"
      selection_criteria: "Use for smooth rate limiting with burst tolerance"
      implementation: "Atomic increment with Redis, refill based on elapsed time"
    leaky_bucket:
      description: "Leaky bucket algorithm with fixed output rate"
      parameters:
        capacity: "Bucket size (limit_value)"
        leak_rate: "Requests per time_window_seconds"
      selection_criteria: "Use for strict rate limiting without bursts"
      implementation: "Queue-based with fixed processing rate"
    fixed_window:
      description: "Fixed time window counter"
      parameters:
        limit: "limit_value per time_window_seconds"
        window_start: "Aligned to time_window_seconds boundaries"
      selection_criteria: "Use for simple per-period limits"
      implementation: "Counter per window, reset at window boundary"
    sliding_window_log:
      description: "Sliding window with request timestamps"
      parameters:
        limit: "limit_value per time_window_seconds"
        precision: "1 second granularity"
      selection_criteria: "Use for precise rate limiting"
      implementation: "Redis sorted set with timestamp scores, cleanup old entries"
  algorithm_selection:
    default: "token_bucket"
    criteria:
      - "If burst_capacity specified: token_bucket"
      - "If strict no-burst required: leaky_bucket"
      - "If simple period-based: fixed_window"
      - "If precise timing needed: sliding_window_log"
  dynamic_adjustment:
    usage_pattern_analysis:
      description: "Analyze historical usage to adjust limits"
      method: "ML-based pattern detection, adjust limits during off-peak hours"
    priority_based_scaling:
      description: "Scale limits based on request priority"
      multipliers:
        critical: 2.0
        high: 1.5
        normal: 1.0
        low: 0.5
    time_of_day_adjustments:
      description: "Adjust limits based on time of day"
      configuration: "Defined in overrides.time_of_day_adjustments"
      off_peak_multiplier: "Applied during off-peak hours"
      peak_multiplier: "Applied during peak hours"
    emergency_capacity_allocation:
      description: "Temporary limit increase for emergencies"
      authorization: "system_architect role required"
      duration_limit: "Maximum 24 hours, requires approval after 4 hours"
      audit_requirement: "All emergency allocations logged to M27"
3. Cost Calculation Engine
yaml
cost_calculation:
  cost_sources:
    - "Cloud provider billing APIs"
    - "Infrastructure monitoring metrics"
    - "Service usage telemetry"
    - "Third-party service costs"
  calculation_methods:
    real_time_resource_metering:
      description: "Calculate costs based on actual resource usage"
      formula: "cost = usage_quantity * unit_price"
      unit_prices: "Stored per resource_type, updated from cloud provider APIs"
      example: "1000 API calls * $0.0001 per call = $0.10"
    amortized_cost_allocation:
      description: "Distribute fixed costs over usage period"
      formula: "allocated_cost = (fixed_cost / total_usage) * tenant_usage"
      use_cases: "Shared infrastructure, reserved capacity"
      example: "$1000 reserved instance / 10000 hours = $0.10 per hour"
    showback_chargeback_models:
      description: "Cost allocation for internal billing"
      showback: "Report costs without actual billing"
      chargeback: "Actual billing to cost centers"
      allocation_rules:
        - "Equal distribution: cost / number_of_tenants"
        - "Usage-based: cost * (tenant_usage / total_usage)"
        - "Weighted: cost * (tenant_weight / sum_of_weights)"
    predictive_cost_forecasting:
      description: "ML-based cost prediction"
      method: "Time-series analysis of historical costs"
      features: "Usage patterns, seasonal trends, growth rates"
      accuracy_target: "> 90% for 30-day forecasts"
  cost_breakdown:
    per_tenant_allocation:
      formula: "tenant_cost = SUM(cost_records WHERE tenant_id = X)"
      aggregation: "Group by tenant_id, sum cost_amount"
    per_feature_attribution:
      formula: "feature_cost = SUM(cost_records WHERE attributed_to_type='feature' AND attributed_to_id = Y)"
      aggregation: "Group by attributed_to_id where attributed_to_type='feature'"
    per_user_resource_costing:
      formula: "user_cost = SUM(cost_records WHERE attributed_to_type='user' AND attributed_to_id = Z)"
      aggregation: "Group by attributed_to_id where attributed_to_type='user'"
    cross_module_cost_distribution:
      formula: "module_cost = SUM(cost_records WHERE tags.module = 'M##')"
      aggregation: "Group by tags.module, sum cost_amount"
  cost_attribution_rules:
    priority: "feature > user > project > tenant (most specific wins)"
    multiple_dimensions: "Cost attributed to most specific dimension, with percentage allocation to parent dimensions"
    unattributed_costs: "Allocated to tenant level with 'unattributed' tag"
  anomaly_detection:
    method: "Statistical analysis with ML enhancement"
    baseline_calculation: "Moving average of last 30 days, adjusted for day-of-week and seasonal patterns"
    sensitivity_thresholds:
      info: "Deviation > 10% from baseline"
      warning: "Deviation > 25% from baseline"
      critical: "Deviation > 50% from baseline"
    false_positive_handling: "Require 3 consecutive anomalies before alerting"
4. Quota Management System
yaml
quota_management:
  quota_types:
    - "Compute resources (CPU/GPU hours)"
    - "Storage capacity (GB-months)"
    - "Network egress (GB)"
    - "AI model inferences"
    - "API request counts"
  allocation_strategies:
    fair_share_allocation:
      description: "Equal distribution among eligible entities"
      formula: "quota_per_entity = total_quota / number_of_entities"
      use_case: "Default allocation for new tenants"
    priority_based_distribution:
      description: "Allocate based on priority tiers"
      tiers:
        tier1: "50% of total quota"
        tier2: "30% of total quota"
        tier3: "20% of total quota"
      use_case: "Enterprise vs standard vs basic tiers"
    dynamic_scaling_based_on_usage:
      description: "Adjust quotas based on historical usage patterns"
      method: "Analyze usage over last 30 days, allocate 120% of average usage"
      use_case: "Auto-scaling quotas for growing tenants"
    reserved_capacity_pools:
      description: "Dedicated quota pools for specific tenants/projects"
      allocation: "Fixed quota reserved, not shared"
      use_case: "SLA-guaranteed capacity"
  quota_enforcement:
    pre_execution_validation:
      workflow:
        1: "Check quota availability before operation"
        2: "Calculate required quota amount"
        3: "Validate: used_amount + required <= allocated_amount + max_burst_amount"
        4: "If valid: proceed, increment used_amount"
        5: "If invalid: return QUOTA_EXHAUSTED error"
      transaction_isolation: "SERIALIZABLE for atomic quota checks"
    soft_quota_warnings:
      thresholds:
        warning_80: "Emit warning when 80% of quota used"
        critical_90: "Emit critical alert when 90% of quota used"
      behavior: "Continue operations, send notifications"
    hard_quota_enforcement:
      trigger: "used_amount >= allocated_amount (burst not available or exhausted)"
      behavior: "Block all operations, return QUOTA_EXHAUSTED error"
    burstable_quota_handling:
      calculation: "available = allocated_amount + max_burst_amount - used_amount"
      burst_usage: "Tracked separately, charged at premium rate if applicable"
      limits: "Burst cannot exceed max_burst_amount"
  quota_renewal_automation:
    timing: "Triggered 24 hours before period_end if auto_renew = true"
    amount_calculation: "Same as previous allocation, or based on usage pattern if configured"
    failure_handling: "Retry 3 times, notify tenant_admin on final failure"
    notifications: "Email and IDE notification on renewal success/failure"
5. Alerting & Notification System
yaml
alerting_system:
  alert_triggers:
    - "Budget threshold exceeded (80%, 90%, 100%)"
    - "Rate limit violations"
    - "Cost anomalies detected"
    - "Quota exhaustion imminent"
  notification_channels:
    - "IDE extension notifications"
    - "Email alerts"
    - "Slack/Teams webhooks"
    - "PagerDuty integration"
  escalation_policies:
    - "Multi-level escalation paths"
    - "Time-based escalation"
    - "Role-based notification routing"

Data Storage Architecture
Database Schema:
sql
-- Budget Definitions Table
CREATE TABLE budget_definitions (
    budget_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    budget_name VARCHAR(255) NOT NULL,
    budget_type VARCHAR(50) NOT NULL,
    budget_amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    period_type VARCHAR(20) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ,
    allocated_to_type VARCHAR(50) NOT NULL,
    allocated_to_id UUID NOT NULL,
    enforcement_action VARCHAR(50) NOT NULL,
    thresholds JSONB,
    notifications JSONB,
    created_at TIMESTAMPTZ NOT NULL,
    created_by UUID NOT NULL
);

-- Rate Limit Policies Table
CREATE TABLE rate_limit_policies (
    policy_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    scope_type VARCHAR(50) NOT NULL,
    scope_id UUID NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    limit_value INTEGER NOT NULL,
    time_window_seconds INTEGER NOT NULL,
    algorithm VARCHAR(50) NOT NULL,
    burst_capacity INTEGER,
    overrides JSONB,
    created_at TIMESTAMPTZ NOT NULL
);

-- Cost Records Table
CREATE TABLE cost_records (
    cost_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    resource_id UUID NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    cost_amount DECIMAL(15,6) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    usage_quantity DECIMAL(15,6),
    usage_unit VARCHAR(50),
    timestamp TIMESTAMPTZ NOT NULL,
    attributed_to_type VARCHAR(50) NOT NULL,
    attributed_to_id UUID NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    region VARCHAR(50),
    tags JSONB
);

-- Quota Allocations Table
CREATE TABLE quota_allocations (
    quota_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    allocated_amount DECIMAL(15,6) NOT NULL,
    used_amount DECIMAL(15,6) DEFAULT 0,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    allocation_type VARCHAR(50) NOT NULL,
    max_burst_amount DECIMAL(15,6),
    auto_renew BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL,
    CHECK (allocated_amount > 0),
    CHECK (used_amount >= 0),
    CHECK (used_amount <= allocated_amount + COALESCE(max_burst_amount, 0)),
    CHECK (period_end > period_start)
);

-- Budget Utilization Tracking Table
CREATE TABLE budget_utilization (
    utilization_id UUID PRIMARY KEY,
    budget_id UUID NOT NULL REFERENCES budget_definitions(budget_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    spent_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(budget_id, period_start, period_end),
    CHECK (spent_amount >= 0),
    CHECK (period_end > period_start)
);

-- Rate Limit Usage Counters Table
CREATE TABLE rate_limit_usage (
    usage_id UUID PRIMARY KEY,
    policy_id UUID NOT NULL REFERENCES rate_limit_policies(policy_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    resource_key VARCHAR(255) NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    current_count INTEGER NOT NULL DEFAULT 0,
    last_request_at TIMESTAMPTZ,
    UNIQUE(policy_id, resource_key, window_start),
    CHECK (current_count >= 0),
    CHECK (window_end > window_start)
);

-- Quota Usage History Table
CREATE TABLE quota_usage_history (
    usage_id UUID PRIMARY KEY,
    quota_id UUID NOT NULL REFERENCES quota_allocations(quota_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    usage_timestamp TIMESTAMPTZ NOT NULL,
    usage_amount DECIMAL(15,6) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    CHECK (usage_amount >= 0)
);

-- Database Constraints
ALTER TABLE budget_definitions ADD CONSTRAINT budget_amount_positive CHECK (budget_amount > 0);
ALTER TABLE budget_definitions ADD CONSTRAINT budget_dates_valid CHECK (end_date IS NULL OR end_date > start_date);
ALTER TABLE budget_definitions ADD CONSTRAINT budget_type_valid CHECK (budget_type IN ('tenant', 'project', 'user', 'feature'));
ALTER TABLE budget_definitions ADD CONSTRAINT enforcement_action_valid CHECK (enforcement_action IN ('hard_stop', 'soft_limit', 'throttle', 'escalate'));

ALTER TABLE rate_limit_policies ADD CONSTRAINT limit_value_positive CHECK (limit_value > 0);
ALTER TABLE rate_limit_policies ADD CONSTRAINT time_window_positive CHECK (time_window_seconds > 0);
ALTER TABLE rate_limit_policies ADD CONSTRAINT algorithm_valid CHECK (algorithm IN ('token_bucket', 'leaky_bucket', 'fixed_window', 'sliding_window_log'));

ALTER TABLE cost_records ADD CONSTRAINT cost_amount_positive CHECK (cost_amount >= 0);
ALTER TABLE cost_records ADD CONSTRAINT usage_quantity_positive CHECK (usage_quantity IS NULL OR usage_quantity >= 0);

-- Unique Constraints
CREATE UNIQUE INDEX idx_budget_active_per_allocated ON budget_definitions(tenant_id, allocated_to_type, allocated_to_id) 
    WHERE end_date IS NULL OR end_date > NOW();

-- Index Creation Statements
CREATE INDEX idx_budget_definitions_tenant_id ON budget_definitions(tenant_id);
CREATE INDEX idx_budget_definitions_allocated ON budget_definitions(tenant_id, allocated_to_type, allocated_to_id);
CREATE INDEX idx_budget_definitions_period ON budget_definitions(start_date, end_date) WHERE end_date IS NOT NULL;
CREATE INDEX idx_budget_definitions_name ON budget_definitions USING gin(to_tsvector('english', budget_name));

CREATE INDEX idx_rate_limit_policies_tenant_id ON rate_limit_policies(tenant_id);
CREATE INDEX idx_rate_limit_policies_scope ON rate_limit_policies(scope_type, scope_id);
CREATE INDEX idx_rate_limit_policies_resource ON rate_limit_policies(resource_type, tenant_id);

CREATE INDEX idx_cost_records_tenant_id ON cost_records(tenant_id);
CREATE INDEX idx_cost_records_timestamp ON cost_records(timestamp DESC, tenant_id);
CREATE INDEX idx_cost_records_attributed ON cost_records(attributed_to_type, attributed_to_id, tenant_id);
CREATE INDEX idx_cost_records_resource_type ON cost_records(resource_type, attributed_to_type);
CREATE INDEX idx_cost_records_tags ON cost_records USING gin(tags);
CREATE INDEX idx_cost_records_service_region ON cost_records(service_name, region);
CREATE INDEX idx_cost_records_time_range ON cost_records USING brin(timestamp) WITH (pages_per_range = 32);

CREATE INDEX idx_quota_allocations_tenant_id ON quota_allocations(tenant_id);
CREATE INDEX idx_quota_allocations_period ON quota_allocations(period_start, period_end, tenant_id);
CREATE INDEX idx_quota_allocations_resource ON quota_allocations(resource_type, tenant_id);

CREATE INDEX idx_budget_utilization_budget_id ON budget_utilization(budget_id);
CREATE INDEX idx_budget_utilization_period ON budget_utilization(budget_id, period_start, period_end);
CREATE INDEX idx_budget_utilization_tenant ON budget_utilization(tenant_id, period_start);

CREATE INDEX idx_rate_limit_usage_policy ON rate_limit_usage(policy_id, resource_key, window_start);
CREATE INDEX idx_rate_limit_usage_window ON rate_limit_usage(window_start, window_end) WHERE window_end > NOW();
CREATE INDEX idx_rate_limit_usage_tenant ON rate_limit_usage(tenant_id, window_start);

CREATE INDEX idx_quota_usage_history_quota_id ON quota_usage_history(quota_id, usage_timestamp DESC);
CREATE INDEX idx_quota_usage_history_tenant ON quota_usage_history(tenant_id, usage_timestamp DESC);
CREATE INDEX idx_quota_usage_history_timestamp ON quota_usage_history USING brin(usage_timestamp) WITH (pages_per_range = 32);

Indexing Strategy:
yaml
indexing:
  primary_indexes:
    - "budget_id, tenant_id (composite)"
    - "policy_id, tenant_id (composite)"
    - "cost_id, tenant_id (composite)"
    - "quota_id, tenant_id (composite)"
  
  performance_indexes:
    - "tenant_id, allocated_to_type, allocated_to_id (composite)"
    - "timestamp, tenant_id (composite) - BRIN for time-series"
    - "resource_type, attributed_to_type (composite)"
    - "period_start, period_end, tenant_id (composite)"
    - "budget_id, period_start, period_end (composite) - for utilization lookups"
    - "policy_id, resource_key, window_start (composite) - for rate limit usage"
  
  search_indexes:
    - "tags (GIN index)"
    - "service_name, region (composite)"
    - "budget_name (full-text search GIN)"
  
  time_series_indexes:
    - "cost_records.timestamp (BRIN)"
    - "quota_usage_history.usage_timestamp (BRIN)"

Transaction Isolation and Concurrency Control:
yaml
transaction_isolation:
  budget_check_operations:
    isolation_level: "SERIALIZABLE"
    requirement: "Atomic budget check and utilization update"
    implementation: "Database transaction with row-level locking on budget_utilization"
  rate_limit_increment:
    isolation_level: "SERIALIZABLE"
    requirement: "Atomic counter increment to prevent race conditions"
    implementation: "Redis atomic INCR with Lua script for distributed coordination"
  cost_recording:
    isolation_level: "READ COMMITTED"
    requirement: "Consistent cost record insertion"
    implementation: "Database transaction with foreign key constraints"
  quota_allocation:
    isolation_level: "SERIALIZABLE"
    requirement: "Atomic quota allocation and usage tracking"
    implementation: "Database transaction with row-level locking on quota_allocations"
concurrency_control:
  optimistic_locking: "Version fields on budget_definitions and quota_allocations for concurrent updates"
  pessimistic_locking: "Row-level locks for budget utilization and quota usage updates"
  distributed_coordination: "Redis-based distributed locks for rate limit operations across instances"

Caching Strategy:
yaml
caching:
  rate_limit_data:
    cache_type: "Redis cluster"
    ttl: "300 seconds (5 minutes)"
    key_pattern: "rate_limit:policy:{policy_id}:resource:{resource_key}"
    invalidation: "On policy update, TTL expiration, or manual invalidation"
    consistency: "Eventual consistency acceptable, cache-aside pattern"
  budget_definitions:
    cache_type: "In-memory cache with Redis backup"
    ttl: "600 seconds (10 minutes)"
    key_pattern: "budget:tenant:{tenant_id}:allocated:{type}:{id}"
    invalidation: "On budget create/update/delete, TTL expiration"
    warming: "Pre-load active budgets on service startup"
  quota_allocations:
    cache_type: "Redis cluster"
    ttl: "180 seconds (3 minutes)"
    key_pattern: "quota:tenant:{tenant_id}:resource:{resource_type}"
    invalidation: "On quota allocation/update, TTL expiration"
  cost_aggregations:
    cache_type: "Redis with periodic refresh"
    ttl: "3600 seconds (1 hour)"
    key_pattern: "cost:aggregate:tenant:{tenant_id}:period:{start}:{end}"
    invalidation: "On new cost records, TTL expiration, or manual refresh"
  cache_invalidation_strategies:
    write_through: "Update cache immediately on write operations"
    write_behind: "Update cache asynchronously for non-critical data"
    cache_eviction: "LRU eviction when cache reaches 80% capacity"

API Versioning Strategy:
yaml
api_versioning:
  current_version: "v1"
  version_format: "/budget/v{version}/"
  deprecation_policy:
    notice_period: "6 months before deprecation"
    migration_guide: "Provided 3 months before version removal"
    backward_compatibility: "Maintained for at least 12 months"
  version_support:
    active_versions: ["v1"]
    deprecated_versions: []
    sunset_versions: []
  migration_path:
    description: "Clear migration guide with code examples"
    breaking_changes: "Documented with alternatives"
    tooling: "Migration scripts and validation tools provided"

Multi-Currency Support:
yaml
multi_currency:
  currency_conversion:
    source: "Real-time exchange rates from financial APIs"
    update_frequency: "Daily at 00:00 UTC"
    fallback: "Last known rate if API unavailable"
  conversion_timing:
    budget_checks: "Convert to budget currency at check time"
    cost_recording: "Store in original currency, convert on aggregation"
    reporting: "Convert to requested currency at report generation time"
  currency_display:
    default: "USD"
    per_tenant_preference: "Stored in tenant configuration"
    report_formatting: "Currency code prefix (e.g., '$', '€', '£')"
  multi_currency_budget_aggregation:
    method: "Convert all costs to budget currency before aggregation"
    formula: "aggregated_cost = SUM(cost_amount * exchange_rate_to_budget_currency)"

Data Partitioning Strategy:
yaml
data_partitioning:
  partition_key_selection:
    cost_records: "tenant_id + timestamp (monthly partitions)"
    budget_utilization: "tenant_id + period_start (monthly partitions)"
    quota_usage_history: "tenant_id + usage_timestamp (monthly partitions)"
  partition_size_limits:
    max_rows_per_partition: "10000000"
    max_size_per_partition: "50GB"
    auto_partition_creation: "Monthly automatic partition creation"
  partition_retention:
    active_partitions: "Last 12 months"
    archived_partitions: "7 years for compliance"
    archival_process: "Move to cold storage after 12 months"
  partition_pruning:
    query_optimization: "Automatic partition elimination based on WHERE clauses"
    index_usage: "Partition-aware index scans"

API Contracts
yaml
openapi: 3.0.3
info:
  title: ZeroUI Budgeting, Rate-Limiting & Cost Observability
  version: 2.0.0
  description: Enterprise-grade resource budgeting, rate-limiting enforcement, and cost observability API

servers:
  - url: https://api.zeroui.com/budget/v1
    description: Production server
  - url: https://staging-api.zeroui.com/budget/v1
    description: Staging server

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT token obtained from M21 IAM Module
    apiKey:
      type: apiKey
      in: header
      name: X-API-Key
      description: API key for service-to-service authentication
  
  parameters:
    CorrelationId:
      name: X-Correlation-ID
      in: header
      required: false
      schema:
        type: string
        format: uuid
      description: Correlation ID for request tracing
    TenantId:
      name: tenant_id
      in: query
      required: true
      schema:
        type: string
        format: uuid
      description: Tenant identifier
    Page:
      name: page
      in: query
      required: false
      schema:
        type: integer
        minimum: 1
        default: 1
      description: Page number for pagination
    PageSize:
      name: page_size
      in: query
      required: false
      schema:
        type: integer
        minimum: 1
        maximum: 1000
        default: 100
      description: Number of items per page
    IdempotencyKey:
      name: X-Idempotency-Key
      in: header
      required: false
      schema:
        type: string
        format: uuid
      description: Idempotency key for safe retries
  
  schemas:
    ErrorResponse:
      type: object
      required: [error_code, message, correlation_id]
      properties:
        error_code:
          type: string
          enum: [BUDGET_EXCEEDED, RATE_LIMIT_VIOLATED, QUOTA_EXHAUSTED, COST_CALCULATION_ERROR, VALIDATION_ERROR, NOT_FOUND, UNAUTHORIZED, FORBIDDEN, INTERNAL_ERROR]
        message:
          type: string
        details:
          type: object
        correlation_id:
          type: string
          format: uuid
        retriable:
          type: boolean
        suggested_action:
          type: string
        tenant_id:
          type: string
          format: uuid
    
    PaginationMeta:
      type: object
      required: [page, page_size, total_count]
      properties:
        page:
          type: integer
        page_size:
          type: integer
        total_count:
          type: integer
        total_pages:
          type: integer
        next_page_token:
          type: string
          nullable: true
        prev_page_token:
          type: string
          nullable: true
    
    Alert:
      type: object
      required: [alert_id, alert_type, tenant_id, severity, status, created_at]
      properties:
        alert_id:
          type: string
          format: uuid
        alert_type:
          type: string
          enum: [budget_threshold_exceeded, rate_limit_violated, cost_anomaly_detected, quota_exhausted]
        tenant_id:
          type: string
          format: uuid
        severity:
          type: string
          enum: [info, warning, critical]
        status:
          type: string
          enum: [active, acknowledged, resolved]
        title:
          type: string
        message:
          type: string
        details:
          type: object
        resource_id:
          type: string
          format: uuid
        created_at:
          type: string
          format: date-time
        acknowledged_at:
          type: string
          format: date-time
          nullable: true
        resolved_at:
          type: string
          format: date-time
          nullable: true
    
    BudgetDefinition:
      type: object
      required: [budget_id, tenant_id, budget_name, budget_type, budget_amount, period_type, start_date, allocated_to_type, allocated_to_id, enforcement_action]
      properties:
        budget_id:
          type: string
          format: uuid
        tenant_id:
          type: string
          format: uuid
        budget_name:
          type: string
          maxLength: 255
        budget_type:
          type: string
          enum: [tenant, project, user, feature]
        budget_amount:
          type: number
          minimum: 0
        currency:
          type: string
          pattern: '^[A-Z]{3}$'
          default: USD
        period_type:
          type: string
          enum: [monthly, quarterly, yearly, custom]
        start_date:
          type: string
          format: date-time
        end_date:
          type: string
          format: date-time
          nullable: true
        allocated_to_type:
          type: string
          enum: [tenant, project, user, feature]
        allocated_to_id:
          type: string
          format: uuid
        enforcement_action:
          type: string
          enum: [hard_stop, soft_limit, throttle, escalate]
        thresholds:
          type: object
          properties:
            warning_80:
              type: boolean
            critical_90:
              type: boolean
            exhausted_100:
              type: boolean
        notifications:
          type: object
          properties:
            channels:
              type: array
              items:
                type: string
                enum: [ide, email, slack, teams, pagerduty]
            escalation_paths:
              type: array
              items:
                type: string
        created_at:
          type: string
          format: date-time
        created_by:
          type: string
          format: uuid
    
    RateLimitPolicy:
      type: object
      required: [policy_id, tenant_id, scope_type, scope_id, resource_type, limit_value, time_window_seconds, algorithm]
      properties:
        policy_id:
          type: string
          format: uuid
        tenant_id:
          type: string
          format: uuid
        scope_type:
          type: string
          enum: [tenant, user, project, feature]
        scope_id:
          type: string
          format: uuid
        resource_type:
          type: string
        limit_value:
          type: integer
          minimum: 1
        time_window_seconds:
          type: integer
          minimum: 1
        algorithm:
          type: string
          enum: [token_bucket, leaky_bucket, fixed_window, sliding_window_log]
        burst_capacity:
          type: integer
          minimum: 0
          nullable: true
        overrides:
          type: object
          nullable: true
        created_at:
          type: string
          format: date-time
    
    QuotaAllocation:
      type: object
      required: [quota_id, tenant_id, resource_type, allocated_amount, period_start, period_end, allocation_type]
      properties:
        quota_id:
          type: string
          format: uuid
        tenant_id:
          type: string
          format: uuid
        resource_type:
          type: string
        allocated_amount:
          type: number
          minimum: 0
        used_amount:
          type: number
          minimum: 0
          default: 0
        period_start:
          type: string
          format: date-time
        period_end:
          type: string
          format: date-time
        allocation_type:
          type: string
          enum: [tenant, project, user, feature]
        max_burst_amount:
          type: number
          minimum: 0
          nullable: true
        auto_renew:
          type: boolean
          default: true
        created_at:
          type: string
          format: date-time
    
    CostRecord:
      type: object
      required: [cost_id, tenant_id, resource_id, resource_type, cost_amount, timestamp, attributed_to_type, attributed_to_id, service_name]
      properties:
        cost_id:
          type: string
          format: uuid
        tenant_id:
          type: string
          format: uuid
        resource_id:
          type: string
          format: uuid
        resource_type:
          type: string
        cost_amount:
          type: number
          minimum: 0
        currency:
          type: string
          pattern: '^[A-Z]{3}$'
          default: USD
        usage_quantity:
          type: number
          nullable: true
        usage_unit:
          type: string
          nullable: true
        timestamp:
          type: string
          format: date-time
        attributed_to_type:
          type: string
          enum: [tenant, user, project, feature]
        attributed_to_id:
          type: string
          format: uuid
        service_name:
          type: string
        region:
          type: string
          nullable: true
        tags:
          type: object
          nullable: true
  
  responses:
    BadRequest:
      description: Bad request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    Forbidden:
      description: Forbidden
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    InternalError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'

security:
  - bearerAuth: []
  - apiKey: []

paths:
  /budget/v1/health:
    get:
      operationId: budgetHealthCheck
      summary: Health probe for Budgeting, Rate-Limiting & Cost Observability module
      tags: [System]
      security: []
      responses:
        '200':
          description: Service health status
          content:
            application/json:
              schema:
                type: object
                required: [status, version, timestamp, dependencies]
                properties:
                  status:
                    type: string
                    enum: [UP, DOWN, DEGRADED]
                  version:
                    type: string
                  timestamp:
                    type: string
                    format: date-time
                  dependencies:
                    type: object
                    properties:
                      database:
                        type: object
                        properties:
                          status: {type: string, enum: [UP, DOWN]}
                          latency_ms: {type: number}
                      cache:
                        type: object
                        properties:
                          status: {type: string, enum: [UP, DOWN]}
                          latency_ms: {type: number}
                      m27_audit_ledger:
                        type: object
                        properties:
                          status: {type: string, enum: [UP, DOWN]}
                          latency_ms: {type: number}
                      m31_notification_engine:
                        type: object
                        properties:
                          status: {type: string, enum: [UP, DOWN]}
                          latency_ms: {type: number}
                      m33_key_management:
                        type: object
                        properties:
                          status: {type: string, enum: [UP, DOWN]}
                          latency_ms: {type: number}
                  degraded_reasons:
                    type: array
                    items: {type: string}
        '503':
          description: Service unavailable
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /budget/v1/metrics:
    get:
      operationId: budgetMetrics
      summary: Metrics for Budgeting, Rate-Limiting & Cost Observability module
      responses:
        '200':
          description: Metrics in platform-standard exposition format
          content:
            text/plain:
              schema:
                type: string
                description: "Metrics in ZeroUI-standard / OpenTelemetry-compatible format"

  /budget/v1/alerts:
    get:
      operationId: listBudgetAlerts
      summary: List active budgeting and cost alerts for a tenant
      tags: [Alerts]
      parameters:
        - $ref: '#/components/parameters/TenantId'
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/PageSize'
        - $ref: '#/components/parameters/CorrelationId'
        - in: query
          name: alert_type
          schema:
            type: string
            enum: [budget_threshold_exceeded, rate_limit_violated, cost_anomaly_detected, quota_exhausted]
          description: Filter by alert type
        - in: query
          name: severity
          schema:
            type: string
            enum: [info, warning, critical]
          description: Filter by severity
        - in: query
          name: status
          schema:
            type: string
            enum: [active, acknowledged, resolved]
          description: Filter by status
        - in: query
          name: start_time
          schema:
            type: string
            format: date-time
          description: Filter alerts created after this time
        - in: query
          name: end_time
          schema:
            type: string
            format: date-time
          description: Filter alerts created before this time
      responses:
        '200':
          description: Active alerts for the tenant
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
              description: Correlation ID for this request
          content:
            application/json:
              schema:
                type: object
                required: [alerts, pagination]
                properties:
                  alerts:
                    type: array
                    items:
                      $ref: '#/components/schemas/Alert'
                  pagination:
                    $ref: '#/components/schemas/PaginationMeta'
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
  /budget/v1/budgets/check:
    post:
      operationId: checkBudget
      summary: Check budget availability for operation
      tags: [Budgets]
      parameters:
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [tenant_id, resource_type, estimated_cost]
              properties:
                tenant_id:
                  type: string
                  format: uuid
                resource_type:
                  type: string
                estimated_cost:
                  type: number
                  minimum: 0
                operation_context:
                  type: object
                allocated_to_type:
                  type: string
                  enum: [tenant, project, user, feature]
                allocated_to_id:
                  type: string
                  format: uuid
      responses:
        '200':
          description: Budget check result
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [allowed, remaining_budget, budget_id, correlation_id]
                properties:
                  allowed:
                    type: boolean
                  remaining_budget:
                    type: number
                  budget_id:
                    type: string
                    format: uuid
                  enforcement_action:
                    type: string
                    enum: [hard_stop, soft_limit, throttle, escalate]
                  message:
                    type: string
                  utilization_ratio:
                    type: number
                    minimum: 0
                    maximum: 1
                  correlation_id:
                    type: string
                    format: uuid
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '403':
          description: Forbidden
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '429':
          description: Rate limit exceeded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /budget/v1/budgets:
    post:
      operationId: createBudget
      summary: Create a new budget definition
      tags: [Budgets]
      parameters:
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BudgetDefinition'
      responses:
        '201':
          description: Budget created successfully
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BudgetDefinition'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '409':
          description: Budget already exists
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          $ref: '#/components/responses/InternalError'
    get:
      operationId: listBudgets
      summary: List budgets for a tenant
      tags: [Budgets]
      parameters:
        - $ref: '#/components/parameters/TenantId'
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/PageSize'
        - $ref: '#/components/parameters/CorrelationId'
        - in: query
          name: budget_type
          schema:
            type: string
            enum: [tenant, project, user, feature]
        - in: query
          name: allocated_to_type
          schema:
            type: string
            enum: [tenant, project, user, feature]
        - in: query
          name: allocated_to_id
          schema:
            type: string
            format: uuid
        - in: query
          name: active_only
          schema:
            type: boolean
            default: false
      responses:
        '200':
          description: List of budgets
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [budgets, pagination]
                properties:
                  budgets:
                    type: array
                    items:
                      $ref: '#/components/schemas/BudgetDefinition'
                  pagination:
                    $ref: '#/components/schemas/PaginationMeta'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/budgets/{budget_id}:
    get:
      operationId: getBudget
      summary: Get budget by ID
      tags: [Budgets]
      parameters:
        - in: path
          name: budget_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
      responses:
        '200':
          description: Budget details
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BudgetDefinition'
        '404':
          description: Budget not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'
    put:
      operationId: updateBudget
      summary: Update budget definition
      tags: [Budgets]
      parameters:
        - in: path
          name: budget_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BudgetDefinition'
      responses:
        '200':
          description: Budget updated successfully
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BudgetDefinition'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          description: Budget not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          $ref: '#/components/responses/InternalError'
    delete:
      operationId: deleteBudget
      summary: Delete budget definition
      tags: [Budgets]
      parameters:
        - in: path
          name: budget_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
      responses:
        '204':
          description: Budget deleted successfully
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          description: Budget not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '409':
          description: Budget cannot be deleted (active utilization exists)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/rate-limits/check:
    post:
      operationId: checkRateLimit
      summary: Check rate limit for resource
      tags: [Rate Limits]
      parameters:
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [tenant_id, resource_type, request_count]
              properties:
                tenant_id: {type: string, format: uuid}
                resource_type: {type: string}
                request_count: {type: integer, default: 1, minimum: 1}
                priority: {type: string, enum: [low, normal, high, critical]}
                resource_key: {type: string}
      responses:
        '200':
          description: Rate limit check result
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [allowed, remaining_requests, reset_time, correlation_id]
                properties:
                  allowed: {type: boolean}
                  remaining_requests: {type: integer}
                  reset_time: {type: string, format: date-time}
                  limit_value: {type: integer}
                  retry_after: {type: integer}
                  policy_id: {type: string, format: uuid}
                  correlation_id: {type: string, format: uuid}
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '429':
          description: Rate limit exceeded
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/rate-limits:
    post:
      operationId: createRateLimitPolicy
      summary: Create a new rate limit policy
      tags: [Rate Limits]
      parameters:
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RateLimitPolicy'
      responses:
        '201':
          description: Rate limit policy created successfully
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RateLimitPolicy'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '409':
          description: Rate limit policy already exists
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          $ref: '#/components/responses/InternalError'
    get:
      operationId: listRateLimitPolicies
      summary: List rate limit policies for a tenant
      tags: [Rate Limits]
      parameters:
        - $ref: '#/components/parameters/TenantId'
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/PageSize'
        - $ref: '#/components/parameters/CorrelationId'
        - in: query
          name: scope_type
          schema:
            type: string
            enum: [tenant, user, project, feature]
        - in: query
          name: scope_id
          schema:
            type: string
            format: uuid
        - in: query
          name: resource_type
          schema:
            type: string
      responses:
        '200':
          description: List of rate limit policies
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [policies, pagination]
                properties:
                  policies:
                    type: array
                    items:
                      $ref: '#/components/schemas/RateLimitPolicy'
                  pagination:
                    $ref: '#/components/schemas/PaginationMeta'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/rate-limits/{policy_id}:
    get:
      operationId: getRateLimitPolicy
      summary: Get rate limit policy by ID
      tags: [Rate Limits]
      parameters:
        - in: path
          name: policy_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
      responses:
        '200':
          description: Rate limit policy details
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RateLimitPolicy'
        '404':
          $ref: '#/components/responses/NotFound'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'
    put:
      operationId: updateRateLimitPolicy
      summary: Update rate limit policy
      tags: [Rate Limits]
      parameters:
        - in: path
          name: policy_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RateLimitPolicy'
      responses:
        '200':
          description: Rate limit policy updated successfully
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RateLimitPolicy'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'
    delete:
      operationId: deleteRateLimitPolicy
      summary: Delete rate limit policy
      tags: [Rate Limits]
      parameters:
        - in: path
          name: policy_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
      responses:
        '204':
          description: Rate limit policy deleted successfully
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '409':
          description: Rate limit policy cannot be deleted (active usage exists)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/cost-tracking/record:
    post:
      operationId: recordCost
      summary: Record resource usage cost
      tags: [Cost Tracking]
      parameters:
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [tenant_id, resource_type, cost_amount, usage_quantity]
              properties:
                tenant_id: {type: string, format: uuid}
                resource_type: {type: string}
                cost_amount: {type: number, minimum: 0}
                usage_quantity: {type: number}
                usage_unit: {type: string}
                resource_id: {type: string, format: uuid}
                service_name: {type: string}
                attributed_to_type: {type: string, enum: [tenant, user, project, feature]}
                attributed_to_id: {type: string, format: uuid}
                region: {type: string}
                tags: {type: object}
      responses:
        '202':
          description: Cost recording accepted
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [record_id, recorded_at, correlation_id]
                properties:
                  record_id: {type: string, format: uuid}
                  recorded_at: {type: string, format: date-time}
                  correlation_id: {type: string, format: uuid}
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/cost-tracking:
    get:
      operationId: queryCostRecords
      summary: Query cost records with filtering and aggregation
      tags: [Cost Tracking]
      parameters:
        - $ref: '#/components/parameters/TenantId'
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/PageSize'
        - $ref: '#/components/parameters/CorrelationId'
        - in: query
          name: start_time
          schema:
            type: string
            format: date-time
          description: Filter records from this time
        - in: query
          name: end_time
          schema:
            type: string
            format: date-time
          description: Filter records until this time
        - in: query
          name: resource_type
          schema:
            type: string
        - in: query
          name: attributed_to_type
          schema:
            type: string
            enum: [tenant, user, project, feature]
        - in: query
          name: attributed_to_id
          schema:
            type: string
            format: uuid
        - in: query
          name: service_name
          schema:
            type: string
        - in: query
          name: group_by
          schema:
            type: array
            items:
              type: string
              enum: [resource_type, service_name, region, attributed_to_type, day, week, month]
          description: Group results by these dimensions
      responses:
        '200':
          description: Cost records matching query
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [records, pagination]
                properties:
                  records:
                    type: array
                    items:
                      $ref: '#/components/schemas/CostRecord'
                  pagination:
                    $ref: '#/components/schemas/PaginationMeta'
                  aggregated:
                    type: object
                    properties:
                      total_cost: {type: number}
                      total_usage: {type: number}
                      currency: {type: string}
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/cost-tracking/{record_id}:
    get:
      operationId: getCostRecord
      summary: Get cost record by ID
      tags: [Cost Tracking]
      parameters:
        - in: path
          name: record_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
      responses:
        '200':
          description: Cost record details
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CostRecord'
        '404':
          $ref: '#/components/responses/NotFound'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/cost-tracking/reports:
    get:
      operationId: generateCostReport
      summary: Generate aggregated cost reports
      tags: [Cost Tracking]
      parameters:
        - $ref: '#/components/parameters/TenantId'
        - $ref: '#/components/parameters/CorrelationId'
        - in: query
          name: report_type
          required: true
          schema:
            type: string
            enum: [summary, detailed, by_resource, by_service, by_user, by_feature, by_time_period]
        - in: query
          name: start_time
          required: true
          schema:
            type: string
            format: date-time
        - in: query
          name: end_time
          required: true
          schema:
            type: string
            format: date-time
        - in: query
          name: group_by
          schema:
            type: array
            items:
              type: string
              enum: [resource_type, service_name, region, attributed_to_type, day, week, month]
        - in: query
          name: format
          schema:
            type: string
            enum: [json, csv]
            default: json
      responses:
        '200':
          description: Cost report generated
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [report_id, report_type, period, total_cost, currency, correlation_id]
                properties:
                  report_id: {type: string, format: uuid}
                  report_type: {type: string}
                  period: {type: object}
                  total_cost: {type: number}
                  currency: {type: string}
                  breakdown: {type: array}
                  correlation_id: {type: string, format: uuid}
            text/csv:
              schema:
                type: string
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/quotas/allocate:
    post:
      operationId: allocateQuota
      summary: Allocate resource quota
      tags: [Quotas]
      parameters:
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [tenant_id, resource_type, allocated_amount, period_start, period_end, allocation_type]
              properties:
                tenant_id: {type: string, format: uuid}
                resource_type: {type: string}
                allocated_amount: {type: number, minimum: 0}
                period_start: {type: string, format: date-time}
                period_end: {type: string, format: date-time}
                allocation_type: {type: string, enum: [tenant, project, user, feature]}
                max_burst_amount: {type: number, minimum: 0}
                auto_renew: {type: boolean, default: true}
      responses:
        '201':
          description: Quota allocated successfully
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [quota_id, allocated_at, correlation_id]
                properties:
                  quota_id: {type: string, format: uuid}
                  allocated_at: {type: string, format: date-time}
                  correlation_id: {type: string, format: uuid}
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '409':
          description: Quota already exists for this period
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/quotas:
    get:
      operationId: listQuotas
      summary: List quotas for a tenant
      tags: [Quotas]
      parameters:
        - $ref: '#/components/parameters/TenantId'
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/PageSize'
        - $ref: '#/components/parameters/CorrelationId'
        - in: query
          name: resource_type
          schema:
            type: string
        - in: query
          name: allocation_type
          schema:
            type: string
            enum: [tenant, project, user, feature]
        - in: query
          name: active_only
          schema:
            type: boolean
            default: false
      responses:
        '200':
          description: List of quotas
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [quotas, pagination]
                properties:
                  quotas:
                    type: array
                    items:
                      $ref: '#/components/schemas/QuotaAllocation'
                  pagination:
                    $ref: '#/components/schemas/PaginationMeta'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/quotas/{quota_id}:
    get:
      operationId: getQuota
      summary: Get quota by ID
      tags: [Quotas]
      parameters:
        - in: path
          name: quota_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
      responses:
        '200':
          description: Quota details
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QuotaAllocation'
        '404':
          $ref: '#/components/responses/NotFound'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'
    put:
      operationId: updateQuota
      summary: Update quota allocation
      tags: [Quotas]
      parameters:
        - in: path
          name: quota_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                allocated_amount: {type: number, minimum: 0}
                max_burst_amount: {type: number, minimum: 0}
                auto_renew: {type: boolean}
                period_end: {type: string, format: date-time}
      responses:
        '200':
          description: Quota updated successfully
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QuotaAllocation'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'
    delete:
      operationId: deleteQuota
      summary: Delete quota allocation
      tags: [Quotas]
      parameters:
        - in: path
          name: quota_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
      responses:
        '204':
          description: Quota deleted successfully
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '409':
          description: Quota cannot be deleted (active usage exists)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/event-subscriptions:
    post:
      operationId: createEventSubscription
      summary: Subscribe to budget and cost events
      tags: [Event Subscriptions]
      parameters:
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [tenant_id, event_types, webhook_url]
              properties:
                tenant_id: {type: string, format: uuid}
                event_types: {type: array, items: {type: string, enum: [budget_threshold_exceeded, rate_limit_violated, cost_anomaly_detected, quota_exhausted]}}
                webhook_url: {type: string, format: uri}
                filters: {type: object}
                enabled: {type: boolean, default: true}
      responses:
        '201':
          description: Event subscription created
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [subscription_id, created_at, correlation_id]
                properties:
                  subscription_id: {type: string, format: uuid}
                  created_at: {type: string, format: date-time}
                  correlation_id: {type: string, format: uuid}
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'
    get:
      operationId: listEventSubscriptions
      summary: List event subscriptions for a tenant
      tags: [Event Subscriptions]
      parameters:
        - $ref: '#/components/parameters/TenantId'
        - $ref: '#/components/parameters/Page'
        - $ref: '#/components/parameters/PageSize'
        - $ref: '#/components/parameters/CorrelationId'
      responses:
        '200':
          description: List of event subscriptions
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [subscriptions, pagination]
                properties:
                  subscriptions:
                    type: array
                    items:
                      type: object
                      required: [subscription_id, tenant_id, event_types, webhook_url, enabled]
                      properties:
                        subscription_id: {type: string, format: uuid}
                        tenant_id: {type: string, format: uuid}
                        event_types: {type: array}
                        webhook_url: {type: string}
                        enabled: {type: boolean}
                        created_at: {type: string, format: date-time}
                  pagination:
                    $ref: '#/components/schemas/PaginationMeta'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/event-subscriptions/{subscription_id}:
    get:
      operationId: getEventSubscription
      summary: Get event subscription by ID
      tags: [Event Subscriptions]
      parameters:
        - in: path
          name: subscription_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
      responses:
        '200':
          description: Event subscription details
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [subscription_id, tenant_id, event_types, webhook_url, enabled]
                properties:
                  subscription_id: {type: string, format: uuid}
                  tenant_id: {type: string, format: uuid}
                  event_types: {type: array}
                  webhook_url: {type: string}
                  filters: {type: object}
                  enabled: {type: boolean}
                  created_at: {type: string, format: date-time}
        '404':
          $ref: '#/components/responses/NotFound'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'
    put:
      operationId: updateEventSubscription
      summary: Update event subscription
      tags: [Event Subscriptions]
      parameters:
        - in: path
          name: subscription_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                event_types: {type: array}
                webhook_url: {type: string, format: uri}
                filters: {type: object}
                enabled: {type: boolean}
      responses:
        '200':
          description: Event subscription updated
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [subscription_id, tenant_id, event_types, webhook_url, enabled]
                properties:
                  subscription_id: {type: string, format: uuid}
                  tenant_id: {type: string, format: uuid}
                  event_types: {type: array}
                  webhook_url: {type: string}
                  filters: {type: object}
                  enabled: {type: boolean}
                  updated_at: {type: string, format: date-time}
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'
    delete:
      operationId: deleteEventSubscription
      summary: Delete event subscription
      tags: [Event Subscriptions]
      parameters:
        - in: path
          name: subscription_id
          required: true
          schema:
            type: string
            format: uuid
        - $ref: '#/components/parameters/CorrelationId'
      responses:
        '204':
          description: Event subscription deleted
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/cost-tracking/record/batch:
    post:
      operationId: recordCostBatch
      summary: Record multiple cost records in a single request
      tags: [Cost Tracking]
      parameters:
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [records]
              properties:
                records:
                  type: array
                  minItems: 1
                  maxItems: 1000
                  items:
                    type: object
                    required: [tenant_id, resource_type, cost_amount, usage_quantity, idempotency_key]
                    properties:
                      tenant_id: {type: string, format: uuid}
                      resource_type: {type: string}
                      cost_amount: {type: number, minimum: 0}
                      usage_quantity: {type: number}
                      usage_unit: {type: string}
                      resource_id: {type: string, format: uuid}
                      service_name: {type: string}
                      attributed_to_type: {type: string, enum: [tenant, user, project, feature]}
                      attributed_to_id: {type: string, format: uuid}
                      region: {type: string}
                      tags: {type: object}
                      idempotency_key: {type: string, format: uuid}
      responses:
        '202':
          description: Batch cost recording accepted
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [batch_id, processed_count, failed_count, correlation_id]
                properties:
                  batch_id: {type: string, format: uuid}
                  processed_count: {type: integer}
                  failed_count: {type: integer}
                  failures: {type: array, items: {type: object}}
                  correlation_id: {type: string, format: uuid}
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '413':
          description: Payload too large
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/budgets/check/batch:
    post:
      operationId: checkBudgetBatch
      summary: Check budgets for multiple operations
      tags: [Budgets]
      parameters:
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [checks]
              properties:
                checks:
                  type: array
                  minItems: 1
                  maxItems: 500
                  items:
                    type: object
                    required: [tenant_id, resource_type, estimated_cost]
                    properties:
                      tenant_id: {type: string, format: uuid}
                      resource_type: {type: string}
                      estimated_cost: {type: number, minimum: 0}
                      operation_context: {type: object}
                      allocated_to_type: {type: string, enum: [tenant, project, user, feature]}
                      allocated_to_id: {type: string, format: uuid}
      responses:
        '200':
          description: Batch budget check results
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [results, correlation_id]
                properties:
                  results:
                    type: array
                    items:
                      type: object
                      required: [allowed, remaining_budget, budget_id]
                      properties:
                        allowed: {type: boolean}
                        remaining_budget: {type: number}
                        budget_id: {type: string, format: uuid}
                        enforcement_action: {type: string}
                        utilization_ratio: {type: number}
                  correlation_id: {type: string, format: uuid}
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'

  /budget/v1/quotas/allocate/batch:
    post:
      operationId: allocateQuotaBatch
      summary: Allocate multiple quotas in a single request
      tags: [Quotas]
      parameters:
        - $ref: '#/components/parameters/CorrelationId'
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [allocations]
              properties:
                allocations:
                  type: array
                  minItems: 1
                  maxItems: 100
                  items:
                    type: object
                    required: [tenant_id, resource_type, allocated_amount, period_start, period_end, allocation_type, idempotency_key]
                    properties:
                      tenant_id: {type: string, format: uuid}
                      resource_type: {type: string}
                      allocated_amount: {type: number, minimum: 0}
                      period_start: {type: string, format: date-time}
                      period_end: {type: string, format: date-time}
                      allocation_type: {type: string, enum: [tenant, project, user, feature]}
                      max_burst_amount: {type: number, minimum: 0}
                      auto_renew: {type: boolean}
                      idempotency_key: {type: string, format: uuid}
      responses:
        '201':
          description: Batch quota allocation results
          headers:
            X-Correlation-ID:
              schema:
                type: string
                format: uuid
          content:
            application/json:
              schema:
                type: object
                required: [batch_id, successful_count, failed_count, correlation_id]
                properties:
                  batch_id: {type: string, format: uuid}
                  successful_count: {type: integer}
                  failed_count: {type: integer}
                  quotas: {type: array, items: {type: object}}
                  failures: {type: array, items: {type: object}}
                  correlation_id: {type: string, format: uuid}
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalError'

Data Schemas
Budget Definition Schema:
json
{
  "budget_id": "uuid",
  "tenant_id": "uuid",
  "budget_name": "string",
  "budget_type": "tenant|project|user|feature",
  "budget_amount": 10000.00,
  "currency": "USD",
  "period_type": "monthly|quarterly|yearly|custom",
  "start_date": "iso8601",
  "end_date": "iso8601",
  "allocated_to_type": "tenant|project|user|feature",
  "allocated_to_id": "uuid",
  "enforcement_action": "hard_stop|soft_limit|throttle|escalate",
  "thresholds": {
    "warning_80": true,
    "critical_90": true,
    "exhausted_100": true
  },
  "notifications": {
    "channels": ["ide", "email", "slack"],
    "escalation_paths": ["user", "manager", "admin"]
  },
  "created_at": "iso8601",
  "created_by": "uuid"
}
Rate Limit Policy Schema:
json
{
  "policy_id": "uuid",
  "tenant_id": "uuid",
  "scope_type": "tenant|user|project|feature",
  "scope_id": "uuid",
  "resource_type": "api_requests|compute_minutes|storage_operations",
  "limit_value": 1000,
  "time_window_seconds": 3600,
  "algorithm": "token_bucket|leaky_bucket|fixed_window",
  "burst_capacity": 100,
  "overrides": {
    "emergency_capacity": 200,
    "time_of_day_adjustments": {
      "off_peak_multiplier": 2.0,
      "peak_multiplier": 0.5
    }
  },
  "created_at": "iso8601"
}
Cost Record Schema:
json
{
  "cost_id": "uuid",
  "tenant_id": "uuid",
  "resource_id": "uuid",
  "resource_type": "api_call|compute_instance|storage_volume",
  "cost_amount": 0.125,
  "currency": "USD",
  "usage_quantity": 125000,
  "usage_unit": "api_calls|cpu_minutes|gb_storage",
  "timestamp": "iso8601",
  "attributed_to_type": "tenant|user|project|feature",
  "attributed_to_id": "uuid",
  "service_name": "api_gateway|compute_engine|cloud_storage",
  "region": "us-west1",
  "tags": {
    "module": "M22",
    "feature": "data_classification",
    "environment": "production"
  }
}

Quota Allocation Schema:
json
{
  "quota_id": "uuid",
  "tenant_id": "uuid",
  "resource_type": "string",
  "allocated_amount": 1000.0,
  "used_amount": 0.0,
  "period_start": "iso8601",
  "period_end": "iso8601",
  "allocation_type": "tenant|project|user|feature",
  "max_burst_amount": 100.0,
  "auto_renew": true,
  "created_at": "iso8601"
}

Event Contracts:
All events use a common envelope pattern with event-specific payloads. Events are emitted to M31 Notification Engine for delivery.

Common Event Envelope:
json
{
  "event_id": "uuid",
  "event_type": "budget_threshold_exceeded|rate_limit_violated|cost_anomaly_detected|quota_allocated|quota_exhausted|resource_usage_optimized",
  "ts": "iso8601",
  "tenant_id": "uuid",
  "environment": "dev|staging|prod",
  "plane": "tenant|product|shared",
  "source_module": "M35",
  "payload": {}
}

Event Payloads:
yaml
events:
  budget_threshold_exceeded:
    description: "Emitted when a budget crosses a configured threshold (warning, critical, exhausted)."
    payload_schema:
      type: object
      required: [budget_id, threshold, utilization_ratio, correlation_id]
      properties:
        budget_id: {type: string, format: uuid}
        threshold: {type: string, enum: ["warning_80", "critical_90", "exhausted_100"]}
        utilization_ratio: {type: number, minimum: 0, maximum: 1}
        correlation_id: {type: string, format: uuid}
        spent_amount: {type: number}
        remaining_budget: {type: number}
        enforcement_action: {type: string, enum: ["hard_stop", "soft_limit", "throttle", "escalate"]}
  rate_limit_violated:
    description: "Emitted when a rate limit is exceeded for a resource or principal."
    payload_schema:
      type: object
      required: [policy_id, resource_key, current_rate, limit, correlation_id]
      properties:
        policy_id: {type: string, format: uuid}
        resource_key: {type: string}
        current_rate: {type: number}
        limit: {type: number}
        correlation_id: {type: string, format: uuid}
        reset_time: {type: string, format: date-time}
        retry_after: {type: integer}
  cost_anomaly_detected:
    description: "Emitted when cost patterns deviate from historical baselines."
    payload_schema:
      type: object
      required: [anomaly_id, dimension, expected_cost, observed_cost, severity, correlation_id]
      properties:
        anomaly_id: {type: string, format: uuid}
        dimension: {type: string, enum: ["tenant", "project", "feature", "region"]}
        expected_cost: {type: number}
        observed_cost: {type: number}
        severity: {type: string, enum: ["info", "warning", "critical"]}
        correlation_id: {type: string, format: uuid}
        deviation_percentage: {type: number}
        time_period: {type: string}
  quota_allocated:
    description: "Emitted when a new quota is allocated to a tenant, project, user, or feature."
    payload_schema:
      type: object
      required: [quota_id, resource_type, allocated_amount, allocation_type, correlation_id]
      properties:
        quota_id: {type: string, format: uuid}
        resource_type: {type: string}
        allocated_amount: {type: number}
        allocation_type: {type: string, enum: ["tenant", "project", "user", "feature"]}
        correlation_id: {type: string, format: uuid}
        period_start: {type: string, format: date-time}
        period_end: {type: string, format: date-time}
        max_burst_amount: {type: number}
  quota_exhausted:
    description: "Emitted when an allocated quota is fully consumed."
    payload_schema:
      type: object
      required: [quota_id, resource_type, used_amount, correlation_id]
      properties:
        quota_id: {type: string, format: uuid}
        resource_type: {type: string}
        used_amount: {type: number}
        correlation_id: {type: string, format: uuid}
        allocated_amount: {type: number}
        remaining_amount: {type: number}
        period_end: {type: string, format: date-time}
  resource_usage_optimized:
    description: "Emitted when the module recommends or applies a cost optimization action."
    payload_schema:
      type: object
      required: [optimization_id, action_type, estimated_savings, correlation_id]
      properties:
        optimization_id: {type: string, format: uuid}
        action_type: {type: string}
        estimated_savings: {type: number}
        correlation_id: {type: string, format: uuid}
        resource_type: {type: string}
        optimization_details: {type: object}
Performance Specifications
Throughput Requirements:
yaml
throughput:
  budget_checks: 20000 operations/second
  rate_limit_checks: 50000 operations/second
  cost_recording: 10000 operations/second
  quota_allocations: 1000 operations/second
Scalability Limits:
yaml
scalability:
  maximum_budget_definitions: 100000
  maximum_rate_limit_policies: 50000
  maximum_cost_records_per_day: 100000000
  maximum_tenants: 1000
  maximum_concurrent_checks: 50000
Latency Budgets:
yaml
latency:
  budget_check:
    p95: < 10ms
    p99: < 25ms
  rate_limit_check:
    p95: < 5ms
    p99: < 15ms
  cost_recording:
    p95: < 50ms
    p99: < 100ms
  quota_allocation:
    p95: < 100ms
    p99: < 250ms

Security Implementation
Access Control Matrix:
yaml
access_control:
  budget_management:
    view: ["tenant_admin", "financial_controller", "auditor"]
    modify: ["tenant_admin", "financial_controller"]
    approve: ["financial_controller"]
  rate_limit_management:
    view: ["tenant_admin", "system_architect"]
    modify: ["tenant_admin", "system_architect"]
    override: ["system_architect"]
  cost_reporting:
    view: ["tenant_user", "tenant_admin", "financial_controller"]
    export: ["tenant_admin", "financial_controller"]
  quota_management:
    view: ["tenant_user", "tenant_admin"]
    request: ["tenant_user"]
    approve: ["tenant_admin"]
Data Protection:
yaml
data_protection:
  encryption:
    at_rest: "AES-256-GCM"
    in_transit: "TLS 1.3"
    key_management: "M33 Key Management Module"
  data_retention:
    cost_records: "7 years for compliance"
    budget_definitions: "5 years"
    rate_limit_policies: "3 years"
  access_logging:
    comprehensive_audit_trails: true
    immutable_logs: true
    real_time_cost_alerts: true

Testing Requirements
Acceptance Criteria:
yaml
acceptance_criteria:
  - "Budget checks complete within 10ms p95 latency"
  - "Rate limit checks complete within 5ms p95 latency"
  - "Cost recording maintains 99.9% accuracy"
  - "Quota enforcement prevents resource exhaustion"
  - "Multi-tenant isolation prevents cross-tenant cost leakage"
  - "Alerting system triggers within 30 seconds of threshold breach"
Performance Test Cases:
Test Case 1: High-Volume Budget Checking
yaml
test_case: TC-PERF-BUDGET-001
description: "Sustain 20,000 budget checks per second"
environment: "Production-equivalent load testing"
test_steps:
  - "Generate 20,000 RPS load with realistic budget scenarios"
  - "Monitor system resources and latency metrics"
  - "Run for 60 minutes to assess stability"
  - "Verify budget enforcement accuracy"
success_criteria:
  - "p95 latency < 10ms maintained"
  - "Zero failed budget checks"
  - "CPU utilization < 70%"
  - "Memory utilization < 65%"
  - "100% budget enforcement accuracy"
Test Case 2: Rate Limit Enforcement Under Load
yaml
test_case: TC-PERF-RATELIMIT-001
description: "Validate rate limiting at 50,000 requests per second"
environment: "Staging with production data"
test_steps:
  - "Configure rate limits for various resource types"
  - "Generate load exceeding rate limits"
  - "Verify proper throttling and error responses"
  - "Test burst capacity handling"
success_criteria:
  - "Rate limits enforced with 100% accuracy"
  - "p95 latency < 5ms under load"
  - "Burst capacity properly handled"
  - "Appropriate HTTP 429 responses for exceeded limits"
Functional Test Cases:
Test Case 1: End-to-End Budget Enforcement
yaml
test_case: TC-FUNC-BUDGET-001
description: "Complete budget enforcement workflow"
preconditions:
  - "Budget service running"
  - "Test tenant with budget defined"
  - "Cost tracking enabled"
test_steps:
  - "Set budget threshold at $100"
  - "Simulate resource usage costing $90"
  - "Verify warning notifications triggered"
  - "Simulate additional usage exceeding $100"
  - "Verify enforcement action executed"
expected_results:
  - "Warning notification at 90% threshold"
  - "Enforcement action at 100% threshold"
  - "Accurate cost tracking throughout"
  - "Audit trail maintained"
Test Case 2: Rate Limit Policy Application
yaml
test_case: TC-FUNC-RATELIMIT-001
description: "Rate limit policy creation and enforcement"
preconditions:
  - "Rate limit service running"
  - "Test tenant configured"
  - "Policy management API available"
test_steps:
  - "Create rate limit policy: 1000 requests/hour"
  - "Make 900 requests within hour"
  - "Verify requests allowed"
  - "Make 200 additional requests"
  - "Verify requests throttled after 1000"
expected_results:
  - "First 1000 requests allowed"
  - "Requests beyond limit properly throttled"
  - "Accurate remaining count returned"
  - "Reset time properly calculated"
Test Case 3: Cost Attribution Accuracy
yaml
test_case: TC-FUNC-COST-001
description: "Validate cost attribution across dimensions"
preconditions:
  - "Cost tracking service running"
  - "Test data for multiple tenants"
  - "Attribution rules configured"
test_steps:
  - "Generate cost events for multiple tenants"
  - "Record costs with different attribution dimensions"
  - "Query cost reports by tenant, user, feature"
  - "Verify attribution accuracy"
expected_results:
  - "Costs accurately attributed to correct tenants"
  - "User-level costing matches expected values"
  - "Feature-level breakdowns accurate"
  - "Cross-tenant isolation maintained"
Integration Test Cases:
Test Case 1: IAM Integration for Budget Management
yaml
test_case: TC-INT-IAM-001
description: "Budget policies integrated with access control"
preconditions:
  - "IAM service running"
  - "Budget service running"
  - "Test users with different roles"
test_steps:
  - "Attempt budget modification with insufficient permissions"
  - "Verify access denied"
  - "Authenticate with financial_controller role"
  - "Verify budget modification allowed"
  - "Check audit trail for authorization events"
expected_results:
  - "Role-based access control properly enforced"
  - "Budget modifications require appropriate permissions"
  - "Audit trail captures authorization decisions"
Test Case 2: Cross-Module Cost Integration
yaml
test_case: TC-INT-COST-001
description: "Cost tracking integrated across ZeroUI modules"
preconditions:
  - "All relevant modules running"
  - "Cost tracking enabled globally"
  - "Test data flows established"
test_steps:
  - "Execute operations across multiple modules"
  - "Verify cost recording for each module operation"
  - "Check cost aggregation at tenant level"
  - "Validate cross-module cost reporting"
expected_results:
  - "Costs recorded for all module operations"
  - "Accurate aggregation at tenant level"
  - "Cross-module cost reports generated"
  - "Performance within latency budgets"
Security Test Cases:
Test Case 1: Tenant Cost Isolation
yaml
test_case: TC-SEC-TENANT-001
description: "Verify tenant isolation in cost data"
preconditions:
  - "Multiple tenants configured"
  - "Tenant-specific cost data exists"
  - "Cross-tenant access attempts possible"
test_steps:
  - "Authenticate as Tenant A"
  - "Attempt to access Tenant B cost data"
  - "Attempt to modify Tenant B budget policies"
  - "Attempt to view Tenant B rate limits"
expected_results:
  - "All cross-tenant access attempts denied"
  - "Appropriate authorization errors returned"
  - "No cost data leakage between tenants"
  - "Audit trail records isolation violations"

Deployment Specifications
Containerization:
yaml
containerization:
  runtime: "docker_20.10"
  orchestration: "kubernetes_1.25"
  resource_limits:
    cpu: "4.0"
    memory: "8Gi"
    storage: "50Gi"
  scaling:
    min_replicas: 2
    max_replicas: 20
  metrics:
    - "cpu_utilization_70%"
    - "memory_utilization_65%"
    - "budget_check_queue_1000"
    - "rate_limit_cache_hit_95%"
High Availability:
yaml
high_availability:
  database:
    - "Multi-AZ PostgreSQL cluster"
    - "Synchronous replication"
    - "Automatic failover"
    - "RTO: < 5 minutes, RPO: < 1 minute"
  service:
    - "Multi-region deployment"
    - "Global load balancing"
    - "Health-based traffic routing"
    - "RTO: < 2 minutes, RPO: 0 (stateless design)"
  cache:
    - "Redis cluster for rate limiting"
    - "Cross-region replication"
    - "Automatic failover"
    - "RTO: < 1 minute, RPO: < 5 minutes (acceptable data loss window)"

Disaster Recovery Procedures:
yaml
disaster_recovery:
  rto_rpo_targets:
    rto: "< 15 minutes for full service restoration"
    rpo: "< 5 minutes for data loss tolerance"
  backup_procedures:
    database_backups:
      frequency: "Continuous WAL archiving + daily full backups"
      retention: "30 days daily, 12 months monthly"
      storage: "Encrypted S3-compatible storage"
    cache_backups:
      frequency: "Daily snapshots"
      retention: "7 days"
      storage: "Redis persistence to disk"
  recovery_procedures:
    database_recovery:
      steps:
        1: "Identify last known good backup"
        2: "Restore from backup to standby instance"
        3: "Replay WAL logs to point-in-time"
        4: "Validate data integrity"
        5: "Switch traffic to recovered instance"
      estimated_time: "10-15 minutes"
    service_recovery:
      steps:
        1: "Deploy service to standby region"
        2: "Update DNS/load balancer configuration"
        3: "Verify health checks"
        4: "Gradually route traffic"
      estimated_time: "2-5 minutes"
  data_replication_lag_tolerance:
    acceptable_lag: "< 1 second for synchronous replication"
    fallback_mode: "Asynchronous replication if lag exceeds 5 seconds"
    monitoring: "Real-time replication lag monitoring with alerts"

M35 API Rate Limiting:
yaml
m35_api_rate_limiting:
  default_limits:
    per_tenant: "1000 requests per minute"
    per_user: "100 requests per minute"
    per_api_key: "5000 requests per minute"
  endpoint_specific_limits:
    budget_checks: "20000 requests per minute per tenant"
    rate_limit_checks: "50000 requests per minute per tenant"
    cost_recording: "10000 requests per minute per tenant"
    cost_reports: "100 requests per minute per tenant"
  enforcement:
    method: "Token bucket algorithm"
    response: "HTTP 429 with Retry-After header"
    headers:
      X-RateLimit-Limit: "Maximum requests allowed"
      X-RateLimit-Remaining: "Remaining requests in window"
      X-RateLimit-Reset: "Unix timestamp when limit resets"

Batch Operations:
yaml
batch_operations:
  bulk_cost_recording:
    endpoint: "POST /budget/v1/cost-tracking/record/batch"
    max_batch_size: "1000 records per request"
    timeout: "30 seconds"
    error_handling: "Partial success with error details per record"
    idempotency: "Per-record idempotency keys supported"
  bulk_budget_checks:
    endpoint: "POST /budget/v1/budgets/check/batch"
    max_batch_size: "500 checks per request"
    timeout: "10 seconds"
    error_handling: "All-or-nothing, transaction rollback on any failure"
  bulk_quota_allocations:
    endpoint: "POST /budget/v1/quotas/allocate/batch"
    max_batch_size: "100 allocations per request"
    timeout: "15 seconds"
    error_handling: "Partial success with error details per allocation"

Idempotency Requirements:
yaml
idempotency:
  cost_recording:
    required: true
    key_header: "X-Idempotency-Key"
    key_format: "UUID"
    deduplication_window: "24 hours"
    behavior: "Return same response for duplicate idempotency key within window"
  budget_checks:
    required: false
    recommended: true
    key_header: "X-Idempotency-Key"
    behavior: "Cache check result for 5 minutes if idempotency key provided"
  quota_allocations:
    required: true
    key_header: "X-Idempotency-Key"
    deduplication_window: "7 days"
    behavior: "Return existing quota allocation if idempotency key matches"

Deployment Rollback Procedures:
yaml
deployment_rollback:
  database_migrations:
    rollback_strategy: "Versioned migrations with up/down scripts"
    rollback_window: "24 hours after deployment"
    procedure:
      1: "Identify migration version to rollback to"
      2: "Execute down migration scripts in reverse order"
      3: "Validate data integrity"
      4: "Verify application compatibility"
    risk_assessment: "Data loss possible if rollback removes columns with data"
  service_deployments:
    rollback_strategy: "Blue-green deployment with instant rollback capability"
    rollback_trigger: "Health check failures, error rate spikes, or manual trigger"
    procedure:
      1: "Switch load balancer to previous version"
      2: "Monitor health metrics for 5 minutes"
      3: "Scale down new version if rollback successful"
    rollback_time: "< 2 minutes"
  configuration_changes:
    rollback_strategy: "Versioned configuration with rollback API"
    procedure:
      1: "Revert to previous configuration version"
      2: "Reload configuration without service restart"
      3: "Validate configuration applied correctly"
    rollback_time: "< 30 seconds"

Operational Procedures
Budget Operations Runbook:
yaml
budget_operations:
  1. "Budget policy definition and validation"
  2. "Threshold configuration and notification setup"
  3. "Enforcement action configuration"
  4. "Regular budget review and adjustment"
  5. "Exception handling and escalation"
Incident Response:
yaml
incident_response:
  budget_violation:
    - "Immediate notification to stakeholders"
    - "Temporary quota increase if justified"
    - "Root cause analysis"
    - "Policy adjustment if needed"
  rate_limit_circuit_breaker:
    - "Automatic failover to secondary region"
    - "Emergency capacity allocation"
    - "Performance degradation mitigation"
    - "Post-incident review"

Monitoring & Alerting
Key Metrics:
yaml
metrics:
  business:
    budget_utilization_rate:
      type: "gauge"
      unit: "percentage"
      threshold: "< 95%"
      labels: ["tenant_id", "budget_id", "budget_type"]
    cost_savings_from_optimizations:
      type: "counter"
      unit: "currency"
      threshold: "> 15% of baseline"
      labels: ["tenant_id", "optimization_type"]
    rate_limit_violation_rate:
      type: "rate"
      unit: "violations per second"
      threshold: "< 1% of total requests"
      labels: ["tenant_id", "policy_id", "resource_type"]
    quota_allocation_efficiency:
      type: "gauge"
      unit: "percentage"
      threshold: "> 90%"
      labels: ["tenant_id", "resource_type"]
  technical:
    budget_check_latency:
      type: "histogram"
      unit: "milliseconds"
      threshold: "p95 < 10ms, p99 < 25ms"
      labels: ["tenant_id", "operation_type"]
      buckets: [1, 5, 10, 25, 50, 100, 250, 500]
    rate_limit_check_performance:
      type: "histogram"
      unit: "milliseconds"
      threshold: "p95 < 5ms, p99 < 15ms"
      labels: ["tenant_id", "policy_id", "algorithm"]
      buckets: [1, 2, 5, 10, 15, 25, 50]
    cost_calculation_accuracy:
      type: "gauge"
      unit: "percentage"
      threshold: "> 99.9%"
      labels: ["tenant_id", "calculation_method"]
    cache_hit_rates:
      type: "gauge"
      unit: "percentage"
      threshold: "> 95%"
      labels: ["cache_type", "tenant_id"]
    database_connection_pool_utilization:
      type: "gauge"
      unit: "percentage"
      threshold: "< 80%"
      labels: ["pool_name"]
    redis_operation_latency:
      type: "histogram"
      unit: "milliseconds"
      threshold: "p95 < 2ms"
      labels: ["operation_type", "redis_cluster"]

Alert Thresholds and Rules:
yaml
alerts:
  critical:
    budget_exceeded_hard_stop:
      condition: "budget_utilization_rate >= 100 AND enforcement_action = 'hard_stop'"
      severity: "critical"
      notification: "Immediate email + PagerDuty"
      escalation: "Financial controller + Tenant admin within 5 minutes"
    rate_limit_service_unavailable:
      condition: "service_health_status = 'DOWN' OR error_rate > 10%"
      severity: "critical"
      notification: "Immediate PagerDuty + Slack"
      escalation: "On-call engineer + System architect"
    cost_calculation_discrepancy:
      condition: "ABS(calculated_cost - expected_cost) / expected_cost > 0.05"
      severity: "critical"
      notification: "Email + IDE notification"
      escalation: "Financial controller within 15 minutes"
    quota_exhaustion_multiple_tenants:
      condition: "COUNT(tenants WITH quota_utilization >= 100) >= 5"
      severity: "critical"
      notification: "Email + Slack"
      escalation: "System architect + Tenant admins"
  warning:
    budget_utilization_high:
      condition: "budget_utilization_rate > 90"
      severity: "warning"
      notification: "Email + IDE notification"
      deduplication: "One alert per budget per 24 hours"
    rate_limit_violation_rate_high:
      condition: "rate_limit_violation_rate > 0.05"
      severity: "warning"
      notification: "Email"
      deduplication: "One alert per policy per hour"
    cost_recording_latency_high:
      condition: "cost_recording_latency_p95 > 100ms"
      severity: "warning"
      notification: "Email"
      deduplication: "One alert per 6 hours"
    cache_hit_rate_low:
      condition: "cache_hit_rate < 90%"
      severity: "warning"
      notification: "Email"
      deduplication: "One alert per 12 hours"
  alert_deduplication:
    method: "Group alerts by tenant_id + alert_type"
    window: "Configurable per alert type (default: 1 hour)"
    escalation: "Escalate if alert persists beyond deduplication window"

Dependency Specifications
Module Dependencies:
yaml
dependencies:
  required:
    - "M21: IAM Module (access control)"
    - "M33: Key Management (encryption)"
    - "M27: Audit Ledger (compliance evidence)"
    - "M29: Data & Memory Plane (data storage)"
  integration:
    - "M22: Data Governance (privacy cost tracking)"
    - "M31: Notification Engine (alert delivery)"
    - "M34: Schema Registry (data validation)"
Infrastructure Dependencies:
yaml
infrastructure:
  database:
    - "PostgreSQL 14+ with JSONB and partitioning"
    - "Connection pooling with failover"
    - "Read replicas for reporting"
  caching:
    - "Redis 6+ cluster with persistence"
    - "SSL/TLS encryption"
    - "Cross-region replication for rate limits"

Audit Integration (M27):
yaml
audit_integration:
  decision_receipts:
    description: "Every budget, rate limit, cost, and quota decision emits a structured receipt via M27 using the canonical M27 receipt schema."
    sink: "M27 Audit Ledger (module M27)"
    receipt_schema:
      description: "M35 MUST use the canonical M27 receipt schema format. All receipts include the following required fields:"
      required_fields:
        - "receipt_id (UUID)"
        - "gate_id (string, e.g., 'budget-management', 'rate-limit-check', 'cost-tracking', 'quota-management')"
        - "policy_version_ids (array of strings)"
        - "snapshot_hash (string, pattern: '^sha256:[0-9a-f]{64}$')"
        - "timestamp_utc (ISO8601)"
        - "timestamp_monotonic_ms (number)"
        - "inputs (object)"
        - "decision.status (enum: 'pass'|'warn'|'soft_block'|'hard_block')"
        - "decision.rationale (string)"
        - "decision.badges (array of strings)"
        - "result (object)"
        - "actor.repo_id (string)"
        - "actor.user_id (UUID, optional)"
        - "actor.machine_fingerprint (string, optional)"
        - "degraded (boolean)"
        - "signature (string, Ed25519 via M33)"
      optional_fields:
        - "evidence_handles (array)"
  pii_handling:
    description: "No raw PII, secrets, or source code are written into receipts; only opaque identifiers and aggregates are used."
  schema_reference:
    description: "M35 reuses the canonical receipt schema defined in the M27 Audit Ledger PRD and MUST NOT invent a new one. Receipt schemas are defined below for each operation type."

Receipt Schemas:
All budget, rate limit, cost, and quota operations generate receipts that flow from Tier 3 → Tier 2 → Tier 1 for UI rendering. Receipts follow ZeroUI canonical receipt schema standards with module-specific payloads.

Budget Check Receipt Schema:
json
{
  "receipt_id": "uuid",
  "gate_id": "budget-check",
  "policy_version_ids": ["uuid"],
  "snapshot_hash": "sha256:hex",
  "timestamp_utc": "iso8601",
  "timestamp_monotonic_ms": "number",
  "inputs": {
    "tenant_id": "uuid",
    "resource_type": "string",
    "estimated_cost": "number",
    "allocated_to_type": "tenant|project|user|feature",
    "allocated_to_id": "uuid",
    "operation_context": "object"
  },
  "decision": {
    "status": "pass|warn|soft_block|hard_block",
    "rationale": "string",
    "badges": ["string"]
  },
  "result": {
    "allowed": "boolean",
    "remaining_budget": "number",
    "budget_id": "uuid",
    "enforcement_action": "hard_stop|soft_limit|throttle|escalate",
    "utilization_ratio": "number"
  },
  "evidence_handles": [
    {
      "url": "string",
      "type": "budget_utilization|cost_record|audit_trail",
      "description": "string",
      "expires_at": "iso8601"
    }
  ],
  "actor": {
    "repo_id": "string",
    "user_id": "uuid",
    "machine_fingerprint": "string"
  },
  "degraded": "boolean",
  "signature": "string"
}

Rate Limit Check Receipt Schema:
json
{
  "receipt_id": "uuid",
  "gate_id": "rate-limit-check",
  "policy_version_ids": ["uuid"],
  "snapshot_hash": "sha256:hex",
  "timestamp_utc": "iso8601",
  "timestamp_monotonic_ms": "number",
  "inputs": {
    "tenant_id": "uuid",
    "resource_type": "string",
    "request_count": "integer",
    "priority": "low|normal|high|critical",
    "resource_key": "string"
  },
  "decision": {
    "status": "pass|warn|soft_block|hard_block",
    "rationale": "string",
    "badges": ["string"]
  },
  "result": {
    "allowed": "boolean",
    "remaining_requests": "integer",
    "reset_time": "iso8601",
    "limit_value": "integer",
    "policy_id": "uuid"
  },
  "evidence_handles": [
    {
      "url": "string",
      "type": "rate_limit_usage|policy_definition|audit_trail",
      "description": "string",
      "expires_at": "iso8601"
    }
  ],
  "actor": {
    "repo_id": "string",
    "user_id": "uuid",
    "machine_fingerprint": "string"
  },
  "degraded": "boolean",
  "signature": "string"
}

Cost Recording Receipt Schema:
json
{
  "receipt_id": "uuid",
  "gate_id": "cost-tracking",
  "policy_version_ids": ["uuid"],
  "snapshot_hash": "sha256:hex",
  "timestamp_utc": "iso8601",
  "timestamp_monotonic_ms": "number",
  "inputs": {
    "tenant_id": "uuid",
    "resource_type": "string",
    "cost_amount": "number",
    "usage_quantity": "number",
    "usage_unit": "string",
    "resource_id": "uuid",
    "service_name": "string",
    "tags": "object"
  },
  "decision": {
    "status": "pass|warn|soft_block|hard_block",
    "rationale": "string",
    "badges": ["string"]
  },
  "result": {
    "record_id": "uuid",
    "recorded_at": "iso8601",
    "attributed_to_type": "tenant|user|project|feature",
    "attributed_to_id": "uuid"
  },
  "evidence_handles": [
    {
      "url": "string",
      "type": "cost_record|usage_metric|audit_trail",
      "description": "string",
      "expires_at": "iso8601"
    }
  ],
  "actor": {
    "repo_id": "string",
    "user_id": "uuid",
    "machine_fingerprint": "string"
  },
  "degraded": "boolean",
  "signature": "string"
}

Quota Allocation Receipt Schema:
json
{
  "receipt_id": "uuid",
  "gate_id": "quota-management",
  "policy_version_ids": ["uuid"],
  "snapshot_hash": "sha256:hex",
  "timestamp_utc": "iso8601",
  "timestamp_monotonic_ms": "number",
  "inputs": {
    "tenant_id": "uuid",
    "resource_type": "string",
    "allocated_amount": "number",
    "period_start": "iso8601",
    "period_end": "iso8601",
    "allocation_type": "tenant|project|user|feature",
    "max_burst_amount": "number",
    "auto_renew": "boolean"
  },
  "decision": {
    "status": "pass|warn|soft_block|hard_block",
    "rationale": "string",
    "badges": ["string"]
  },
  "result": {
    "quota_id": "uuid",
    "allocated_at": "iso8601",
    "used_amount": "number",
    "remaining_amount": "number"
  },
  "evidence_handles": [
    {
      "url": "string",
      "type": "quota_allocation|usage_history|audit_trail",
      "description": "string",
      "expires_at": "iso8601"
    }
  ],
  "actor": {
    "repo_id": "string",
    "user_id": "uuid",
    "machine_fingerprint": "string"
  },
  "degraded": "boolean",
  "signature": "string"
}

Notification Engine Integration (M31):
yaml
notification_integration:
  engine: "M31 Notification Engine"
  integration_pattern: "M35 does not send email/SMS/Chat directly; it emits logical alert events for M31 to deliver."
  alert_events:
    - "budget_threshold_exceeded"
    - "rate_limit_violated"
    - "cost_anomaly_detected"
    - "quota_exhausted"
  payload_reference:
    description: "M31 consumes the event payloads defined in the Event Contracts section; no notification-specific fields are added in M35."

Error Handling & Resilience
Error Response Schema:
json
{
  "error_code": "BUDGET_EXCEEDED|RATE_LIMIT_VIOLATED|QUOTA_EXHAUSTED|COST_CALCULATION_ERROR",
  "message": "string",
  "details": "object",
  "correlation_id": "uuid",
  "retriable": "boolean",
  "suggested_action": "string",
  "tenant_id": "uuid"
}
Circuit Breaker Patterns:
yaml
resilience:
  budget_service:
    failure_threshold: "40% over 30 seconds"
    timeout: "15ms"
    fallback: "last_known_budget_status"
  rate_limit_service:
    failure_threshold: "30% over 60 seconds"
    timeout: "10ms"
    fallback: "emergency_allow_all"

Data Retention and Compliance
Retention Periods:
yaml
retention_periods:
  budget_definitions: "5 years"
  rate_limit_policies: "3 years"
  cost_records: "7 years (regulatory requirement)"
  quota_allocations: "3 years after expiration"
  audit_trails: "7 years (regulatory requirement)"
Compliance Evidence:
yaml
compliance_evidence:
  financial_controls:
    - "Budget approval workflows"
    - "Cost attribution audit trails"
    - "Rate limit policy documentation"
    - "Quota allocation records"
  regulatory:
    - "SOX Section 404 controls"
    - "GDPR Article 30 processing records"
    - "CCPA opt-out cost tracking"

ZeroUI Plane Placement, Receipts, and PII Handling
text
- Execution planes:
  - "M35 runs primarily in the Tenant Cloud and Product Cloud planes."
  - "Persistent storage for budgets, rate limits, costs, and quotas uses the Tenant Cloud Data & Memory Plane (M29)."
  - "Shared Services Plane provides observability, key management (M33), and the audit ledger (M27)."
- Receipts and evidence:
  - "Every enforcement decision (budget check, rate limit decision, cost recording, quota allocation) emits a structured receipt via M27 using the canonical M27 receipt schema."
  - "Receipts MUST include: receipt_id, gate_id, policy_version_ids, snapshot_hash, timestamp_utc, timestamp_monotonic_ms, inputs, decision.status, decision.rationale, decision.badges, result, actor.repo_id, actor.user_id (optional), actor.machine_fingerprint (optional), degraded, signature."
  - "Receipts use gate_id values: 'budget-check', 'rate-limit-check', 'cost-tracking', 'quota-management'."
  - "Receipts are append-only and are never modified in-place; corrections are written as new receipts."
  - "All receipts are signed with Ed25519 via M33 Key Management Module."
- PII constraints:
  - "No raw PII, secrets, or source code are stored in M35 tables, cost records, receipts, or events."
  - "Only opaque identifiers (tenant_id, user_id, project_id, feature_id) and aggregated numeric metrics are emitted."
  - "Any joins to PII-resident stores occur in the correct plane per ZeroUI global data governance rules; M35 does not introduce new PII stores."