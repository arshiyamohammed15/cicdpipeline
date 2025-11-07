ZEROUI UNIFIED MASTER FRAMEWORK

1. Framework Definition & Principles

Core Identity:
Enterprise-grade, closed-loop, self-learning, autonomous behavioral nervous system for software engineering that operates unobtrusively within existing toolchains (VS Code → GitHub PR checks → CI/CD).

Guiding Principles:

Policy-driven behavioral intervention system

Supportive guidance rather than surveillance

Privacy-first, metadata-only data handling

Consistent UX execution across all modules

Measurable outcomes at individual, team, product, and organizational levels

2. Core Components

Evidence Peek Broker: The IDE Extension never reads evidence files directly.

All Evidence Peek requests are delegated to the local Edge Agent, which mediates access to the Evidence & Audit Ledger with policy/RBAC checks and returns metadata-only, time-scoped handles (no raw logs, no code, no tokens).

Module-Registry = The phone book of all available helpers

Knows about all 15+ different helpers (modules) in the system

Tells the Event-Router which helpers are available for different situations

Event-Router = The traffic director

Watches for important moments (like saving a file or creating a PR)

Decides which helpers should be notified about what's happening

Makes sure your computer doesn't slow down

Signal-Pipeline = The information processor

Takes raw events and turns them into clear signals

Filters out noise and focuses on what matters

Prepares information for the rule checker

Policy-Engine = The rule checker

Checks if what you're doing follows the team's rules

Uses simple YAML files that define good coding practices

Never sends your code anywhere - everything stays on your computer

Decision-Service = The advice generator

Decides what kind of help you need

Chooses between three types of help: Mirror, Mentor, or Multiplier

Figures out how urgent the situation is

Action-Dispatcher = The help deliverer

Shows helpful messages in your status bar

Adds quick-fix suggestions to your problems list

Opens Decision Card with explanations and solutions

Sends notifications only when really necessary

Receipt-Store = The memory keeper

Remembers what help was offered and what you did

Stores only basic facts (metadata), never your actual code

Keeps everything private on your computer unless you choose to share

Learning-Loop = The smart learner

Looks at what help actually worked

Improves the suggestions over time

Helps the system get smarter about how to help you

3. The Three Help Types (MMM)

Mirror = Friendly reflection

Shows you what just happened in a simple way

Always private - only you can see it

Example: "You just made a change that might cause issues later"

Mentor = Helpful coach

Gives you specific advice based on your role

Offers quick fixes and better ways to do things

Example: "Here's a faster way to fix that security issue"

Multiplier = Team booster

Shares good habits across your whole team

Reinforces patterns that work well

Example: "Your team's code quality improved 25% this month"

4. The Three Time Points (T0/T1/T2)

T0 = The "Notice" moment

When the system first notices something might need attention

Records what was noticed and what help was offered

Happens automatically in the background

T1 = The "Action" moment

When you respond to the help offered

Records what you did and how long it took

Example: clicking a quick-fix button

T2 = The "Result" moment

When we see if the help actually worked

Looks at whether things got better later

Example: checking if a deployment was successful

5. Integrated End-to-End Flow

Module-Registry → Event-Router → Signal-Pipeline → Policy-Engine 

→ Decision-Service → Action-Dispatcher → Receipt-Store → Learning-Loop

Step-by-Step Flow:

Module-Registry tells Event-Router what helpers are available

Event-Router watches for important coding moments

Signal-Pipeline processes these moments into clear signals

Policy-Engine checks signals against team rules

Decision-Service chooses the right type of help (MMM)

Action-Dispatcher shows the help in your editor

Receipt-Store remembers what happened (T0/T1/T2)

Learning-Loop uses these memories to improve future help

6. MMM Behavioral Activation Rules

Mirror: All policy violations (private feedback)

Mentor: Medium+ severity or repeat violations (role-aware guidance)

Multiplier: Upon successful violation resolution (organizational reinforcement)

7. Unified Receipt Schema (v2.0)

Receipt chain integrity fields:

  "sequence_no": "int>=1"

  "prev_receipt_hash": "sha256:<hex>"

  "receipt_hash": "sha256:<hex>"

The receipt_hash is computed over the canonicalised JSON (RFC 8785) of the receipt minus the receipt_hash field itself; the chain is append-only.

json

{

  "timestamp": "2025-11-04T12:47:07.363Z",

  "module": "M03",

  "trigger": "ER-001",

  "policy_version": "sha256:<id>",

  

  "help_type": {

    "violation_id": "uuid",

    "seriousness": "critical|high|medium|low",

    "help_kind": "mirror|mentor|multiplier"

  },



  "t0_notice": {

    "alert_level": "off|warn|soft_block|hard_block",

    "help_shown": ["status_bar", "problems", "quick_fix", "decision_card", "notification"],

    "mirror_data": {

      "user_saw_message": true,

      "time_to_see_ms": 1500

    }

  },



  "t1_action": {

    "action_type": "quick_fix|card_button|notify_button|pill_click|feedback",

    "action_name": "open_rollback_runbook",

    "time_to_act_ms": 5000,

    "was_preferred_action": true,

    "worked_first_try": true,

    "action_path": "pill→quick_fix",

    "user_feedback": {

      "was_helpful": true,

      "reason": "helpful|confusing|noisy|null"

    },

    "mentor_data": {

      "advice_followed": true,

      "different_action_taken": "string",

      "coaching_completed": "yes|no|partial",

      "helpfulness_rating": 5

    }

  },



  "t2_result": {

    "deploy_result": "success|failed|rollback",

    "quality_checks": {

      "speed_ok": true,

      "errors_ok": true

    },

    "multiplier_data": {

      "good_pattern_name": "string",

      "team_adoption_rate": 0.85,

      "mistakes_reduced_rate": 0.4

    }

  }

}

8. Performance & Privacy

Speed Promises:

Basic checks: less than 1/3 of a second

Complex checks: less than 15 seconds

Heavy tests: less than 1 minute

Mirror help: appears instantly

Privacy Guarantees:

Everything stays on your computer unless you choose to share

Never stores your actual code

Only basic facts are remembered

You control what gets shared

9. Technical Architecture

Policy Engine & Definition Layer

Signed Snapshots: Policy snapshots are digitally signed and include a KID (key identifier).

The Edge Agent verifies signature and KID against the local trust store before use; unsigned or unknown-KID snapshots are rejected with safe fallback.

Policy Taxonomy: Security, Quality, Operational, Compliance

Policy Language: YAML-based declarative specification

Policy Hierarchy: Organizational > Team > Project inheritance

Version Control: Git-ops style with rollback capabilities

Event Processing & Trigger System

Violation Event Schema: Standardized JSON structure

Clickstream event_type (taxonomy extension): "system_trigger|ui_exposure|ui_click|ui_feedback" in addition to existing domain events.

UI events carry only enums/codes and handles; the Edge Agent may enrich with intent and policy_reason_ids.

Event Bus: Apache Kafka for distributed event handling

Severity Matrix: Critical/High/Medium/Low classification

Data Governance & Storage

Storage Location: Data & Memory Plane (M29)

Retention: 25-month rolling retention with archival

Access Control: RBAC-enforced by organizational role

Encryption: AES-256 at rest and in transit

10. Integration Specifications

System Integration Points

Evidence & Audit Ledger: All interventions logged to M27

Identity & Trust Plane: Integration with M32 for role-based access

Observability Plane: Metrics exported to M4 for system monitoring

API Gateway: All external APIs routed through PLATFORM CAPABILITY 6

Surface ID Standards

zeroUI.status.<module>

zeroUI.diagnostics.<module>

quickfix.zeroUI.<module>

zeroUI.decisionCard

zeroUI.container / zeroUI.view.main

11. Measurement Framework

Adaptability KPIs (T0→T1)

UI Thread Safety: Heavy work is never on the UI thread; Pill/Diagnostics/Decision Card updates must render within declared latency budgets.

Adoption Rate: % T0 where preferred Quick Fix used at T1

Median Time-to-Action: median t1.time_to_action_ms

Abandon Rate: % T0 with no T1 within N minutes

Re-Trigger After Fix: % T0 that re-fire within 24h after preferred T1

Usability KPIs

i18n/a11y Baseline: English default; all surfaces keyboard-accessible with ARIA labels; contrast ≥ 4.5:1; no hardcoded UI strings—use a localisable string table.

Presentation-Only Extension: The IDE Extension renders UI and delegates all evaluation, decisions, evidence brokering, policy, and actions to the Edge Agent or backend.

Feedback Patterns: After each T1/T2, show FB-01-MIN (Was this helpful?); on abandonment escalate to FB-02-TIME; schedule FB-03-OUTCOME for post-resolution check-in. Negative/partial choices require a tag.

One-Click Success: % where first T1 resolves (no second T1)

Re-attempt Rate: % needing >1 actions before success

Short-Path Rate: % taking short path vs long path

Error-in-Flow Rate: extension errors per 100 T1

MMM Effectiveness KPIs

Mirror: User acknowledgment rate and time

Mentor: Nudge acceptance rate and effectiveness

Multiplier: Team adoption and violation reduction rates

12. Implementation Requirements

Mandatory Conformance

MUST implement canonical chain in specified order

MUST write unified receipts (append-only, metadata-only)

MUST meet latency budgets and performance requirements

MUST provide preferred Quick Fix per diagnostic

MUST implement MMM activation rules based on severity

Module Requirements

All 15+ product modules implement unified receipt schema

Policy evaluation includes MMM severity classification

Decision Card renders appropriate MMM components

All behavioral data routes through Data & Memory Plane (M29)

13. Validation & Testing

CI Assertions: Enforce canonical surface order (Trigger→Pill→Diagnostics→Quick Fix→Decision Card→Notification), receipt sequence_no monotonicity, receipt hash-chain continuity, and strict T0/T1/T2 schema conformance.

Acceptance Checklist

Event Router fires on expected events with proper debouncing

Status-Bar Pill updates consistently with MMM context

Diagnostics appear with preferred Quick Fix

Decision Card shows Mirror/Mentor/Multiplier appropriately

Notifications used only for Soft/Hard-block

Unified receipts written locally with all required fields

Performance within budgets with heavy work off UI thread

Test Assertions

Chain order → surfaces populated → MMM components rendered

Receipts: T0 on trigger, T1 on action, T2 on outcome

Performance: Verify latency budgets

MMM: Correct activation based on severity and resolution

14. Change Control

Field additions to receipts must remain metadata-only and backwards-compatible

Versioned schema changes (v2.0+)

Module deviations require documented rationale and impact analysis

All changes must maintain privacy-first stance and performance requirements

15. Framework Implementation Status

This framework provides complete high-level architecture and detailed operational specifications for all critical operational components. It is implementation-ready.

FRAMEWORK VALIDATION: COMPLETE TECHNICAL SPECIFICATION
This unified framework provides the complete conceptual foundation and operational blueprint.

ZEROUI UNIFIED MASTER FRAMEWORK - COMPLETE TECHNICAL SPECIFICATION

15. OPERATIONAL COMPONENT SPECIFICATIONS

15.1 Policy Schema Definition

yaml

# Policy Schema v1.0

policy:

  id: string<uuid>

  version: string<semver>

  name: string<max64>

  description: string<max256>

  category: enum<security|quality|operational|compliance>

  severity: enum<critical|high|medium|low>

  target_roles: array<enum<executive|lead|individual_contributor|ai_agent>>

  conditions:

    - type: enum<file_change|pr_creation|commit|deployment>

      pattern: string<regex>

      threshold: number

  actions:

    mirror: boolean

    mentor: boolean

    multiplier: boolean

  enforcement: enum<off|warn|soft_block|hard_block>

  created: timestamp

  modified: timestamp

15.2 Event Schema Specification

json

{

  "event_id": "uuid",

  "event_type": "file_change|pr_creation|commit|deployment|manual_trigger",

  "timestamp": "iso8601",

  "source": "vscode|github|ci_cd|api",

  "module": "M##",

  "workspace_id": "uuid",

  "repo_id": "uuid",

  "user_id": "uuid",

  "payload": {

    "file_path": "string",

    "branch": "string",

    "pr_id": "string",

    "commit_hash": "string",

    "deployment_id": "string"

  },

  "metadata": {

    "plugin_version": "string",

    "ide_version": "string",

    "os": "string"

  }

}

15.3 Module Registration Protocol

json

{

  "module_id": "M##",

  "name": "string",

  "version": "semver",

  "description": "string",

  "supported_events": ["file_change", "pr_creation", "commit", "deployment"],

  "policy_categories": ["security", "quality", "operational", "compliance"],

  "api_endpoints": {

    "health": "/health",

    "metrics": "/metrics",

    "config": "/config"

  },

  "performance_requirements": {

    "max_latency_ms": 300,

    "max_memory_mb": 512

  },

  "registered": "iso8601",

  "last_updated": "iso8601"

}

15.4 Signal Processing Specification

Input Validation: JSON schema validation for all incoming events

Normalization Rules:

Timestamp conversion to ISO8601

Path standardization (Unix/Windows)

Branch name normalization

Filtering Criteria:

Duplicate event detection (5-second window)

Noise reduction (configurable thresholds)

Relevance scoring (ML-based)

Performance Requirements:

Processing latency: < 50ms per event

Throughput: 1000 events/second

Memory: < 256MB heap

15.5 Decision Service Logic

yaml

decision_engine:

  algorithm: "rule_engine_v1"

  rule_evaluation:

    order: "sequential"

    timeout: "100ms"

  confidence_scoring:

    required_confidence: 0.8

    factors: ["policy_match", "historical_accuracy", "context_relevance"]

  fallback_strategy: "escalate_to_human_review"

  justification_requirements:

    required: true

    format: "structured"

    fields: ["policy_id", "triggering_conditions", "confidence_score"]

15.6 Learning Loop Implementation

yaml

learning_pipeline:

  data_sources: ["receipt_store", "t2_outcomes", "user_feedback"]

  training_schedule: "daily"

  model_types:

    - "policy_effectiveness"

    - "nudge_success_prediction"

    - "behavioral_drift_detection"

  feedback_incorporation:

    window: "30d"

    weight: "recency_based"

  model_validation:

    accuracy_threshold: 0.85

    drift_detection_sensitivity: 0.95

  update_protocol:

    strategy: "canary_deployment"

    rollback: "automatic_on_failure"

15.7 Error Handling Specifications

yaml

error_handling:

Degraded Mode Allow-List: When policy is stale/invalid, allow only safe non-privileged actions [status_bar_update, open_decision_card, open_docs_link]; deny all privileged actions.

  component_failures:

    event_router: "queue_events_retry_later"

    policy_engine: "fallback_to_cached_policies"

    decision_service: "default_to_mirror_only"

    receipt_store: "local_cache_sync_later"

  retry_policies:

    max_attempts: 3

    backoff: "exponential"

    max_delay: "30s"

  fallback_strategies:

    performance_degradation: "reduce_functionality"

    data_loss: "prioritize_recent_data"

    network_outage: "local_mode_operation"

15.8 Security Implementation Details

Authorised Actions: Any one-click action that changes state outside the IDE (e.g., create PR, trigger pipeline, open ticket) MUST pass RBAC authorisation in the Edge Agent and emit a signed T1 receipt with decision rationale, approver/channel, scope, and expiry (dual-channel when required).

yaml

security:

  authentication:

    method: "jwt_bearer_tokens"

    token_expiry: "1h"

    refresh_interval: "55m"

  authorization:

    rbac_roles:

      - "admin"

      - "developer"

      - "viewer"

      - "ci_bot"

    permissions:

      admin: ["read", "write", "configure", "delete"]

      developer: ["read", "write", "execute"]

      viewer: ["read"]

      ci_bot: ["execute"]

  data_protection:

    encryption:

      at_rest: "AES-256"

      in_transit: "TLS_1.3"

    key_rotation: "90d"

15.9 Data Retention Enforcement

Local Receipts (JSONL): rotate daily or at 100 MB; path = receipts/dt=YYYY-MM-DD/receipts-<hhmmss>.jsonl; gzip after 7 days; purge after 30 days (configurable).

Maintain per-file watermark using sequence_no to ensure continuity checks.

yaml

data_retention:

  receipts:

    active: "25months"

    archived: "60months"

    purge_schedule: "monthly"

  events:

    raw_events: "30d"

    processed_events: "90d"

  models:

    training_data: "12months"

    model_versions: "indefinite"

  enforcement:

    automated_purging: "enabled"

    compliance_reporting: "enabled"

    exception_handling: "manual_review"

15.10 Cross-Component Communication Protocols

IPC Session: The Agent mints an ephemeral session token (file mode 0600; TTL ≤ 60s) bound to workspace_id + process_id.

Every Extension→Agent request includes Session-Token; replay protection uses client nonce + timestamp with a 60s window.

Client Limits (Extension→Agent): rate 5 rps; burst 10; queue 100; on overflow drop_oldest and emit a local warning.

yaml

communication:

  event_bus:

    protocol: "kafka_2.13"

    topics:

      - "zeroUI.events.raw"

      - "zeroUI.events.processed"

      - "zeroUI.decisions"

      - "zeroUI.receipts"

  api_specifications:

    protocol: "REST_HTTPS"

    versioning: "url_path_v1"

    authentication: "bearer_token"

  message_formmas:

    event: "json_schema_v1"

    decision: "json_schema_v1"

    receipt: "json_schema_v2"

  synchronization:

    distributed_lock: "redis"

    consensus: "raft"

    conflict_resolution: "last_write_wins"

15.11 Performance Monitoring

yaml

monitoring:

  metrics:

    latency:

      event_processing: "p95<100ms"

      policy_evaluation: "p95<300ms"

      decision_generation: "p95<50ms"

    throughput:

      events_per_second: "min_1000"

      decisions_per_second: "min_500"

    resources:

      cpu_utilization: "max_80%"

      memory_utilization: "max_75%"

  alerting:

    thresholds:

      latency_breach: "5min_consecutive"

      error_rate: ">1%_per_5min"

      resource_saturation: ">90%_5min"

  capacity_planning:

    scaling:

      horizontal: "kubernetes_hpa"

      vertical: "manual_review"

    forecasting:

      model: "arima_seasonal"

      horizon: "30d"

15.12 Deployment Specifications

yaml

deployment:

  containerization:

    runtime: "docker_20.10"

    orchestration: "kubernetes_1.25"

    resource_limits:

      cpu: "2.0"

      memory: "4Gi"

      storage: "10Gi"

  scaling:

    min_replicas: 3

    max_replicas: 50

    metrics:

      - "cpu_utilization_80%"

      - "memory_utilization_75%"

      - "event_queue_length_1000"

  health_checks:

    liveness:

      path: "/health/live"

      interval: "30s"

      timeout: "10s"

    readiness:

      path: "/health/ready"

      interval: "10s"

      timeout: "5s"

15.13 Backup and Recovery

yaml

backup_recovery:

  backup:

    strategy: "incremental_daily_full_weekly"

    retention: "12_weeks"

    storage: "encrypted_object_storage"

    encryption: "AES-256"

  recovery:

    rto: "4h"

    rpo: "15m"

    procedures:

      - "database_restore"

      - "configuration_restore"

      - "secret_rotation"

    testing:

      schedule: "quarterly"

      validation: "automated_checks"

15.14 Compliance Evidence

yaml

compliance:

  audit_trail:

    retention: "7years"

    immutability: "enabled"

    integrity: "cryptographic_hashing"

  reporting:

    schedules:

      daily: "operational_metrics"

      monthly: "compliance_summary"

      quarterly: "regulatory_submission"

    formats:

      - "json"

      - "pdf"

      - "csv"

  regulatory_mappings:

    soc2:

      controls: ["CC6.1", "CC7.1"]

    gdpr:

      articles: ["25", "30", "32"]

    hipaa:

      rules: ["security_rule", "privacy_rule"]

FRAMEWORK VALIDATION: COMPLETE TECHNICAL SPECIFICATION
All operational components now have detailed implementation specifications. The framework provides complete coverage from high-level architecture to low-level implementation details.



15.15 Enum Registry & Governance

- All identifiers used in receipts, events, policies, and surfaces (e.g., module IDs, event_type, action_type, reasons) MUST originate from a central Enum Registry.

- Additions/changes follow §14 Change Control; clients must not emit free text.

- The Registry is versioned and distributed with policy snapshots.
