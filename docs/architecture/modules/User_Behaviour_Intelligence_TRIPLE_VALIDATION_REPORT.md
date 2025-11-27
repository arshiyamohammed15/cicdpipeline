# User Behaviour Intelligence (UBI) Module - Triple Validation Report

**Module:** EPC-9 – User Behaviour Intelligence (UBI)  
**Document Version:** 1.0  
**Validation Date:** 2025-01-XX  
**Validation Type:** Technical & Functional Specification Review, Test Case Validation, Integration Alignment, Consistency Check

---

## Executive Summary

This report provides a comprehensive, systematic analysis of the UBI Module specification (EPC-9) against:
1. Technical and functional requirements completeness
2. Integration contract alignment with dependent modules
3. Test case coverage and validity
4. Consistency with platform architecture patterns
5. Industry best practices for behavioral analytics

**Overall Assessment:** The UBI specification is well-structured and comprehensive, but requires clarifications and enhancements in several critical areas to ensure production readiness.

---

## 1. Technical Specification Analysis

### 1.1 Data Model Validation

#### ✅ Strengths
- **Actor-centric design**: Correctly treats human and AI actors uniformly (FR-9, Section 6)
- **Privacy-first approach**: Data minimisation and purpose limitation principles are well-defined (FR-8)
- **Multi-level aggregation**: Actor, team, and tenant scopes are properly scoped (Section 10.2-10.4)

#### ⚠️ Issues Identified

**ISSUE-1.1.1: BehaviouralEvent Schema Alignment with PM-3**
- **Location**: Section 10.1 (Data Model)
- **Problem**: UBI defines `BehaviouralEvent` with fields `tenant_id`, `actor_id`, `actor_type`, `source_system`, `event_type`, `ts`, `properties`, `privacy_tags`. However, PM-3 (Signal Ingestion & Normalization) produces `SignalEnvelope` with different field names:
  - PM-3 uses: `signal_id`, `tenant_id`, `actor_id`, `signal_kind`, `signal_type`, `occurred_at`, `ingested_at`, `resource`, `payload`, `schema_version`
  - UBI expects: `event_id`, `ts`, `properties`, `privacy_tags`, `source_system`
- **Impact**: **CRITICAL** - Direct mapping mismatch will cause ingestion failures
- **Recommendation**: 
  - UBI MUST consume `SignalEnvelope` from PM-3, not define its own `BehaviouralEvent` schema
  - UBI should map PM-3 fields: `occurred_at` → `ts`, `payload` → `properties`, `signal_type` → `event_type`
  - UBI MUST extract `privacy_tags` from PM-3's `resource` or `payload` metadata (PM-3 may not have explicit `privacy_tags` field)
  - Add explicit mapping specification in FR-1

**ISSUE-1.1.2: Actor Type Enum Consistency**
- **Location**: Section 10.1, Line 201
- **Problem**: UBI defines `actor_type` as `(human / ai_agent / hybrid)`, but:
  - ERIS PRD (Section 8.1) uses: `human`, `ai_agent`, `service`
  - Detection Engine PRD (Section 3.2) references: `human`, `ai_agent`, `service`
  - Trust as Capability uses: `human`, `ai_agent`, `service`
- **Impact**: **HIGH** - Inconsistent actor type values will break downstream integrations
- **Recommendation**: 
  - Standardize on: `human`, `ai_agent`, `service` (add `service` to UBI enum)
  - Remove `hybrid` or define it as a distinct type if needed
  - Update Section 10.1 and all references

**ISSUE-1.1.3: Missing Schema Version in BehaviouralEvent**
- **Location**: Section 10.1
- **Problem**: `BehaviouralEvent` does not include `schema_version` field, but PM-3's `SignalEnvelope` includes it (required for forward/backward compatibility)
- **Impact**: **MEDIUM** - Schema evolution handling will be difficult
- **Recommendation**: Add `schema_version` field to BehaviouralEvent model (or inherit from SignalEnvelope)

### 1.2 API Contract Validation

#### ✅ Strengths
- RESTful API design with clear resource paths
- Query parameters are well-defined
- Event streaming interface is specified

#### ⚠️ Issues Identified

**ISSUE-1.2.1: API Path Inconsistency**
- **Location**: Section 11.1, Line 243
- **Problem**: UBI uses `/v1/ubi/actors/{actor_id}/profile`, but platform pattern from other modules suggests:
  - IAM uses: `/v1/iam/...`
  - ERIS uses: `/v1/evidence/...`
  - Detection Engine uses: `/v1/detection/...`
- **Impact**: **LOW** - Consistency issue, not functional
- **Recommendation**: Verify against platform API naming conventions document (if exists) or align with observed patterns

**ISSUE-1.2.2: Missing IAM Integration in API Contracts**
- **Location**: Section 11.1-11.4
- **Problem**: API endpoints do not specify:
  - Authentication requirements (JWT token format)
  - Authorization checks (IAM role requirements)
  - Tenant isolation enforcement mechanism
- **Impact**: **CRITICAL** - Security and multi-tenancy gaps
- **Recommendation**: 
  - Add authentication/authorization requirements to each API endpoint
  - Specify IAM role requirements (e.g., `ubi:read:actor`, `ubi:read:team`, `ubi:read:tenant`)
  - Reference IAM integration pattern from ERIS PRD (Section 10.3, FR-6)

**ISSUE-1.2.3: Event Stream Specification Missing**
- **Location**: Section 11.3, Line 262
- **Problem**: Event stream `ubi.behavioural_signals` is mentioned but:
  - No message format/schema specified
  - No delivery guarantees (at-least-once, exactly-once)
  - No error handling (DLQ, retries)
  - No consumer acknowledgment pattern
- **Impact**: **HIGH** - Downstream consumers (MMM, Detection) cannot reliably integrate
- **Recommendation**: 
  - Define message schema (serialized BehaviouralSignal format)
  - Specify delivery semantics (at-least-once recommended for auditability)
  - Define error handling and DLQ strategy
  - Reference platform event bus patterns (if documented)

### 1.3 Functional Requirements Completeness

#### ✅ Strengths
- Comprehensive feature extraction requirements (FR-2)
- Baseline computation is well-specified (FR-3)
- Anomaly detection logic is clear (FR-4)
- Privacy controls are thorough (FR-8)

#### ⚠️ Issues Identified

**ISSUE-1.3.1: Missing Event Type Taxonomy**
- **Location**: FR-1, Section 86
- **Problem**: UBI references `event_type` (canonical taxonomy) but does not define:
  - List of supported event types
  - Mapping from PM-3 `signal_type` to UBI `event_type`
  - Event type classification rules
- **Impact**: **HIGH** - Implementation ambiguity
- **Recommendation**: 
  - Define canonical event type taxonomy (e.g., `file_edited`, `build_failed`, `pr_created`, `llm_request_submitted`)
  - Specify mapping rules from PM-3 `signal_type` to UBI `event_type`
  - Document event type classification in FR-1

**ISSUE-1.3.2: Baseline Computation Algorithm Unspecified**
- **Location**: FR-3, Section 99
- **Problem**: FR-3 states "rolling baselines" but does not specify:
  - Baseline calculation algorithm (exponential moving average, simple moving average, percentile-based)
  - Window size defaults
  - Outlier handling during baseline computation
  - Minimum data points required for baseline validity
- **Impact**: **MEDIUM** - Implementation variance risk
- **Recommendation**: 
  - Specify baseline algorithm (recommend: exponential moving average with configurable alpha)
  - Define minimum data points (e.g., 7 days of data)
  - Specify outlier handling (e.g., exclude outliers beyond 3 standard deviations)

**ISSUE-1.3.3: Anomaly Detection Thresholds Not Quantified**
- **Location**: FR-4, Section 105
- **Problem**: FR-4 mentions "configurable thresholds" but:
  - No default threshold values
  - No threshold tuning guidance
  - No false positive rate targets
- **Impact**: **MEDIUM** - Operational configuration uncertainty
- **Recommendation**: 
  - Define default z-score thresholds (e.g., |z-score| > 2.5 for WARN, > 3.5 for CRITICAL)
  - Specify false positive rate targets (e.g., < 5% false positive rate)
  - Document threshold tuning process

**ISSUE-1.3.4: Evidence Linking Mechanism Unclear**
- **Location**: FR-10, Section 149
- **Problem**: FR-10 requires "evidence references" but does not specify:
  - Evidence storage location (ERIS? UBI local store?)
  - Evidence handle format (ERIS evidence_handles format?)
  - Evidence retention policy
- **Impact**: **HIGH** - Integration with ERIS unclear
- **Recommendation**: 
  - Specify that evidence is stored in ERIS (PM-7) and referenced via `evidence_handles`
  - Use ERIS evidence handle format (per ERIS PRD Section 8.1)
  - Link to ERIS evidence retention policies

### 1.4 Receipt Integration (FR-13) Analysis

#### ✅ Strengths
- Receipt emission for configuration changes is specified
- Receipt emission for high-severity signals is required
- ERIS integration is explicitly required

#### ⚠️ Issues Identified

**ISSUE-1.4.1: Receipt Schema Not Specified**
- **Location**: FR-13, Section 172-176
- **Problem**: FR-13 requires receipts but does not specify:
  - Receipt schema format (canonical receipt schema from `docs/architecture/receipt-schema-cross-reference.md`?)
  - Required receipt fields for UBI receipts
  - Receipt `gate_id` value for UBI
- **Impact**: **CRITICAL** - Receipts cannot be emitted without schema
- **Recommendation**: 
  - Use canonical receipt schema from `docs/architecture/receipt-schema-cross-reference.md`
  - Define `gate_id = "ubi"` or `gate_id = "epc-9"`
  - Specify required fields: `tenant_id`, `actor_id` (or service identity), `policy_version_ids`, `decision.status`, `decision.rationale`, `timestamp_utc`, `signature`
  - Reference ERIS PRD Section 8.1 for receipt structure

**ISSUE-1.4.2: Receipt Emission Triggers Incomplete**
- **Location**: FR-13, Section 174-175
- **Problem**: FR-13 only specifies receipts for:
  - Configuration changes (line 174)
  - High-severity BehaviouralSignals (line 175)
- Missing receipts for:
  - Baseline recalculation (FR-3)
  - Anomaly detection (FR-4)
  - Signal generation (FR-5, FR-6, FR-7)
- **Impact**: **MEDIUM** - Audit trail gaps
- **Recommendation**: 
  - Clarify receipt emission policy: all state changes or only high-severity events?
  - If selective, define severity thresholds for receipt emission
  - Consider performance impact of receipt emission frequency

**ISSUE-1.4.3: Receipt Actor Identity Unclear**
- **Location**: FR-13, Section 174
- **Problem**: FR-13 states "triggering actor or service identity (as supplied by IAM)" but:
  - For configuration changes, who is the actor? (tenant admin? system service?)
  - For signal generation, is the actor the subject of the signal or the UBI service?
- **Impact**: **MEDIUM** - Receipt provenance unclear
- **Recommendation**: 
  - For configuration changes: use IAM identity of the requester (tenant admin)
  - For signal generation: use UBI service identity as `actor.type = "service"`, with signal subject in receipt `inputs` or `result` metadata

---

## 2. Integration Contract Analysis

### 2.1 PM-3 (Signal Ingestion & Normalization) Integration

#### ✅ Strengths
- UBI correctly identifies PM-3 as upstream dependency
- Privacy-filtered events requirement is specified

#### ⚠️ Issues Identified

**ISSUE-2.1.1: Event Consumption Mechanism Unspecified**
- **Location**: FR-1, Section 86-90
- **Problem**: FR-1 states "UBI MUST consume normalised behavioural events from PM-3" but does not specify:
  - Consumption method (HTTP API? Event stream? Direct database query?)
  - Event routing from PM-3 to UBI (how does PM-3 route events to UBI?)
  - Event ordering guarantees
  - Idempotency handling
- **Impact**: **CRITICAL** - Integration cannot be implemented
- **Recommendation**: 
  - Specify consumption via PM-3 routing (PM-3 PRD Section 4.6, F6 mentions routing classes)
  - UBI should subscribe to PM-3 routing class `realtime_detection` or `analytics_store`
  - Specify event ordering (at-least-once delivery, out-of-order handling)
  - Define idempotency key (`signal_id` from PM-3)

**ISSUE-2.1.2: Event Type Filtering Not Aligned with PM-3**
- **Location**: FR-1, Section 90
- **Problem**: UBI requires "configurable inclusion/exclusion of event types per tenant" but:
  - PM-3 does not have tenant-level event type filtering in its PRD
  - PM-3 has producer-level `allowed_signal_types` (PM-3 PRD Section 4.2, F2.1)
- **Impact**: **HIGH** - Filtering must be implemented in UBI, not PM-3
- **Recommendation**: 
  - Clarify that UBI implements tenant-level filtering after receiving events from PM-3
  - UBI should maintain tenant configuration for allowed event types
  - UBI should drop events that don't match tenant configuration (with audit log)

**ISSUE-2.1.3: Privacy Tags Mapping Unclear**
- **Location**: FR-1, Section 89
- **Problem**: UBI expects `privacy_tags` in events, but PM-3's `SignalEnvelope` does not have explicit `privacy_tags` field
- **Impact**: **HIGH** - Privacy filtering cannot be applied
- **Recommendation**: 
  - UBI should extract privacy classification from PM-3's `resource` metadata or `payload` attributes
  - Alternatively, PM-3 should add `privacy_tags` field to `SignalEnvelope` (requires PM-3 PRD update)
  - Document privacy tag extraction rules in FR-1

### 2.2 PM-7 (ERIS) Integration

#### ✅ Strengths
- ERIS integration is explicitly required (FR-13)
- Receipt emission is mandatory

#### ⚠️ Issues Identified

**ISSUE-2.2.1: Receipt Ingestion API Not Specified**
- **Location**: FR-13, Section 173-176
- **Problem**: FR-13 requires receipts to be "persisted via ERIS" but does not specify:
  - ERIS API endpoint to use (`POST /v1/evidence/receipts`?)
  - Receipt format validation requirements
  - Error handling (what if ERIS is unavailable?)
- **Impact**: **CRITICAL** - Receipts cannot be emitted
- **Recommendation**: 
  - Use ERIS ingestion API: `POST /v1/evidence/receipts` (per ERIS PRD Section 9.1)
  - Implement retry logic with exponential backoff
  - Handle ERIS unavailability: queue receipts locally or fail gracefully with audit log
  - Reference ERIS PRD Section 9.1 for API contract

**ISSUE-2.2.2: Receipt Schema Validation Missing**
- **Location**: FR-13, Section 176
- **Problem**: FR-13 states receipts "MUST conform to the receipt schema defined by ERIS" but:
  - UBI does not specify which receipt schema version to use
  - UBI does not validate receipt structure before emission
- **Impact**: **HIGH** - Receipt validation failures at ERIS
- **Recommendation**: 
  - Use canonical receipt schema from `docs/architecture/receipt-schema-cross-reference.md`
  - Validate receipts against schema before emission
  - Specify schema version in receipt `schema_version` field

**ISSUE-2.2.3: Evidence Handles Not Linked to ERIS**
- **Location**: FR-10, Section 149-153
- **Problem**: FR-10 requires "evidence_refs" in BehaviouralSignals, but:
  - Evidence storage location is not specified (ERIS? UBI local?)
  - Evidence handle format is not specified
- **Impact**: **MEDIUM** - Evidence linking unclear
- **Recommendation**: 
  - Store evidence in ERIS (if evidence is separate from receipts)
  - Use ERIS evidence handle format (per ERIS PRD Section 8.1: `evidence_handles` array)
  - Or: embed evidence summaries directly in BehaviouralSignal (if evidence is small)

### 2.3 PM-1 (MMM Engine) Integration

#### ✅ Strengths
- MMM consumption of BehaviouralSignals is specified
- Event stream interface is mentioned

#### ⚠️ Issues Identified

**ISSUE-2.3.1: MMM Signal Consumption Contract Unclear**
- **Location**: Section 12, Line 278-279
- **Problem**: UBI states "MMM subscribes to BehaviouralSignals" but:
  - MMM PRD does not exist in codebase (cannot verify contract)
  - Signal format for MMM is not specified
  - MMM filtering requirements (which signals does MMM need?) are not specified
- **Impact**: **HIGH** - MMM integration cannot be implemented
- **Recommendation**: 
  - Define BehaviouralSignal schema for MMM consumption
  - Specify which signal types MMM requires (risk signals? opportunity signals? both?)
  - Define signal priority/severity filtering for MMM
  - Coordinate with MMM PRD when available

**ISSUE-2.3.2: Event Stream Reliability Not Addressed**
- **Location**: Section 11.3, Line 262
- **Problem**: Event stream `ubi.behavioural_signals` is mentioned but:
  - No delivery guarantees specified
  - No consumer acknowledgment pattern
  - No backpressure handling
- **Impact**: **MEDIUM** - MMM may miss signals or be overwhelmed
- **Recommendation**: 
  - Specify at-least-once delivery semantics
  - Define consumer acknowledgment pattern (if using message queue)
  - Specify backpressure handling (signal buffering, rate limiting)

### 2.4 PM-4 (Detection Engine Core) Integration

#### ✅ Strengths
- Detection Engine consumption is specified
- High-severity signals are identified

#### ⚠️ Issues Identified

**ISSUE-2.4.1: Detection Engine Signal Format Unclear**
- **Location**: Section 12, Line 276-277
- **Problem**: UBI states Detection Engine "consumes high-severity BehaviouralSignals as features in risk detection" but:
  - Detection Engine PRD (Section 3.1) states it "operates on normalized signals emitted by SIN", not UBI signals
  - UBI signal format for Detection Engine is not specified
  - How UBI signals are converted to Detection Engine features is unclear
- **Impact**: **HIGH** - Integration contract mismatch
- **Recommendation**: 
  - Clarify integration: Does Detection Engine consume UBI signals directly, or does UBI emit signals that are ingested via PM-3?
  - If direct: Define BehaviouralSignal → Detection Engine feature mapping
  - If via PM-3: UBI should emit signals to PM-3, which routes to Detection Engine
  - Coordinate with Detection Engine PRD Section 3.1

**ISSUE-2.4.2: Signal Severity Threshold Not Defined**
- **Location**: Section 12, Line 277
- **Problem**: "High-severity BehaviouralSignals" is mentioned but:
  - Severity threshold is not defined (what is "high"?)
  - Severity enum values are not specified
- **Impact**: **MEDIUM** - Implementation ambiguity
- **Recommendation**: 
  - Define severity enum: `INFO`, `WARN`, `CRITICAL` (or similar)
  - Specify "high-severity" threshold (e.g., `severity >= WARN`)
  - Make threshold configurable per tenant

### 2.5 EPC-2 (Data Governance & Privacy) Integration

#### ✅ Strengths
- Data Governance integration is specified (FR-8, Section 281)
- Retention and residency requirements are mentioned

#### ⚠️ Issues Identified

**ISSUE-2.5.1: Data Governance API Contract Missing**
- **Location**: FR-8, Section 139-144
- **Problem**: FR-8 states "UBI MUST honour per-tenant data residency and retention specified by Data Governance" but:
  - Data Governance API endpoints are not specified
  - Retention policy lookup mechanism is not defined
  - Data deletion trigger mechanism is not specified
- **Impact**: **HIGH** - Retention policies cannot be enforced
- **Recommendation**: 
  - Use Data Governance API: `GET /privacy/v1/retention/policies?tenant_id={tenant_id}` (per Data Governance PRD)
  - Implement periodic retention policy evaluation (daily batch job)
  - Implement data deletion callback from Data Governance (event-driven or polling)
  - Reference Data Governance PRD for API contracts

**ISSUE-2.5.2: Privacy Classification Integration Unclear**
- **Location**: FR-8, Section 140-141
- **Problem**: FR-8 mentions "data minimisation" but:
  - How UBI determines what data is "minimal" is not specified
  - Data Governance classification service integration is not specified
- **Impact**: **MEDIUM** - Privacy enforcement unclear
- **Recommendation**: 
  - Integrate with Data Governance classification service: `POST /privacy/v1/classification` (if available)
  - Or: Use privacy tags from PM-3 events to determine data minimisation
  - Document data minimisation rules per event type

### 2.6 EPC-1 (IAM) Integration

#### ⚠️ Issues Identified

**ISSUE-2.6.1: IAM Integration Not Specified**
- **Location**: Throughout document
- **Problem**: UBI APIs require authentication/authorization but:
  - IAM integration is not mentioned in the PRD
  - IAM role requirements are not specified
  - Token validation mechanism is not defined
- **Impact**: **CRITICAL** - Security and access control gaps
- **Recommendation**: 
  - Integrate with IAM (EPC-1) for token verification: `POST /iam/v1/verify` (per IAM module pattern)
  - Define IAM roles: `ubi:read:actor`, `ubi:read:team`, `ubi:read:tenant`, `ubi:write:config`
  - Enforce tenant isolation: queries must be scoped to caller's `tenant_id` from IAM token
  - Reference ERIS PRD Section 10.3 (FR-6) for IAM integration pattern

**ISSUE-2.6.2: Actor Identity Resolution Unclear**
- **Location**: FR-1, Section 89
- **Problem**: UBI expects `actor_id` in events, but:
  - How UBI resolves `actor_id` to IAM identity is not specified
  - Actor identity validation is not mentioned
- **Impact**: **MEDIUM** - Identity trust issues
- **Recommendation**: 
  - Validate `actor_id` against IAM (if `actor_id` is IAM user ID)
  - Or: Trust `actor_id` from PM-3 (if PM-3 validates identity)
  - Document actor identity trust model

### 2.7 EPC-10 (Gold Standards) Integration

#### ✅ Strengths
- Gold Standards integration is mentioned (Section 12, Line 282-283)

#### ⚠️ Issues Identified

**ISSUE-2.7.1: Gold Standards Policy Format Unclear**
- **Location**: Section 12, Line 282-283
- **Problem**: UBI states "Gold Standards provides reference policies that convert BehaviouralSignals into gating or recommendations" but:
  - Policy format is not specified
  - Policy evaluation mechanism is not defined
  - How UBI consumes Gold Standards policies is unclear
- **Impact**: **MEDIUM** - Policy enforcement unclear
- **Recommendation**: 
  - Clarify: Does UBI evaluate Gold Standards policies, or does UBI emit signals that Gold Standards consumes?
  - If UBI evaluates: Specify policy format (GSMD snapshots? Policy-as-code?)
  - If Gold Standards consumes: Define signal format for Gold Standards

---

## 3. Test Case Validation

### 3.1 Unit Tests (Section 13.1)

#### ✅ Strengths
- Test cases cover core functionality (feature calculation, baselines, anomalies)
- Privacy and actor parity tests are included

#### ⚠️ Issues Identified

**ISSUE-3.1.1: Test Data Generation Not Specified**
- **Location**: UT-UBI-01, Section 289
- **Problem**: Test cases mention "synthetic BehaviouralEvents" but:
  - Test data generation methodology is not specified
  - Test data volume is not specified
  - Test data realism (does it match production patterns?) is unclear
- **Impact**: **LOW** - Test implementation ambiguity
- **Recommendation**: 
  - Specify test data generation: use faker libraries or predefined test fixtures
  - Define test data volume (e.g., 1000 events for feature calculation tests)
  - Ensure test data matches production event patterns

**ISSUE-3.1.2: Baseline Computation Test Incomplete**
- **Location**: UT-UBI-02, Section 292-294
- **Problem**: Test asserts "BehaviouralBaseline fields match expected statistics" but:
  - Expected statistics calculation is not specified
  - Test data time series characteristics are not defined
- **Impact**: **MEDIUM** - Test validity unclear
- **Recommendation**: 
  - Specify test data: 30 days of data with known mean=50, std_dev=10
  - Assert: `baseline.mean ≈ 50`, `baseline.std_dev ≈ 10` (within tolerance)
  - Test edge cases: insufficient data (< 7 days), all zeros, outliers

**ISSUE-3.1.3: Anomaly Threshold Test Missing Edge Cases**
- **Location**: UT-UBI-03, Section 295-297
- **Problem**: Test only covers "large deviation" case, missing:
  - Boundary cases (z-score exactly at threshold)
  - Multiple anomalies in sequence
  - Anomaly resolution (when does anomaly status change to "resolved"?)
- **Impact**: **MEDIUM** - Test coverage gaps
- **Recommendation**: 
  - Add test: z-score exactly at threshold (should trigger anomaly)
  - Add test: multiple anomalies in sequence (should not duplicate)
  - Add test: anomaly resolution (when feature returns to baseline)

### 3.2 Integration Tests (Section 13.2)

#### ✅ Strengths
- End-to-end flow tests are specified
- Tenant isolation test is included

#### ⚠️ Issues Identified

**ISSUE-3.2.1: PM-3 Integration Test Setup Unclear**
- **Location**: IT-UBI-01, Section 305-307
- **Problem**: Test states "inject BehaviouralEvents via PM-3" but:
  - How to inject events (PM-3 API? Mock PM-3?) is not specified
  - Event injection timing (synchronous? asynchronous?) is unclear
- **Impact**: **MEDIUM** - Test implementation ambiguity
- **Recommendation**: 
  - Specify: Use PM-3 ingestion API `POST /v1/signals/ingest` with test events
  - Or: Mock PM-3 event stream for integration tests
  - Define event injection timing: wait for PM-3 processing, then query UBI

**ISSUE-3.2.2: MMM Subscription Test Missing**
- **Location**: IT-UBI-02, Section 308-310
- **Problem**: Test mentions "MMM consumes" but:
  - MMM PRD does not exist (cannot verify MMM consumption contract)
  - Test assertion "MMM receives correctly formatted signal" cannot be validated without MMM schema
- **Impact**: **HIGH** - Test cannot be implemented
- **Recommendation**: 
  - Defer MMM integration test until MMM PRD is available
  - Or: Mock MMM consumer and verify signal format matches UBI specification
  - Define BehaviouralSignal schema for MMM consumption

**ISSUE-3.2.3: Config Change Test Missing ERIS Verification**
- **Location**: IT-UBI-04, Section 314-316
- **Problem**: Test asserts "logs config version in ERIS" but:
  - ERIS receipt verification is not specified
  - Receipt content validation is not included
- **Impact**: **MEDIUM** - Test completeness gap
- **Recommendation**: 
  - Add assertion: Query ERIS for receipt with `gate_id = "ubi"` and `resource_type = "config"`
  - Validate receipt fields: `tenant_id`, `policy_version_ids`, `decision.status`, `timestamp_utc`
  - Verify receipt signature (if applicable)

### 3.3 Performance Tests (Section 13.3)

#### ✅ Strengths
- High volume event processing test is specified
- Baseline recompute load test is included

#### ⚠️ Issues Identified

**ISSUE-3.3.1: Performance SLOs Not Defined**
- **Location**: PT-UBI-01, Section 318-320
- **Problem**: Test asserts "keeps up with SLO" but:
  - SLO targets are not specified in NFR section
  - Backlog limits are not quantified
- **Impact**: **MEDIUM** - Test pass/fail criteria unclear
- **Recommendation**: 
  - Define SLO: Process 1000 events/second with p95 latency < 5 seconds
  - Define backlog limit: < 1000 events in queue
  - Add to NFR-2 (Latency) section

**ISSUE-3.3.2: Baseline Recompute SLO Missing**
- **Location**: PT-UBI-02, Section 321-323
- **Problem**: Test asserts "completes within SLO" but:
  - SLO target is not specified
  - Test data scale (how many actors/teams?) is not defined
- **Impact**: **MEDIUM** - Test criteria unclear
- **Recommendation**: 
  - Define SLO: Recompute baselines for 1000 actors within 1 hour
  - Specify test data: 1000 actors, 100 teams, 90 days of history
  - Add to NFR-3 (Scalability) section

### 3.4 Privacy & Compliance Tests (Section 13.4)

#### ✅ Strengths
- Data minimisation test is specified
- Aggregation threshold test is included
- Retention & deletion test is present

#### ⚠️ Issues Identified

**ISSUE-3.4.1: Data Minimisation Test Criteria Unclear**
- **Location**: PR-UBI-01, Section 325-326
- **Problem**: Test asserts "only configured event fields are stored" but:
  - Which fields are "configured" is not specified
  - How to verify field exclusion is not defined
- **Impact**: **MEDIUM** - Test implementation ambiguity
- **Recommendation**: 
  - Specify: Configure tenant to allow only `event_type`, `ts`, `actor_id`
  - Inject event with additional fields: `properties.secret_key`, `properties.pii_email`
  - Assert: Stored event does not contain `properties.secret_key` or `properties.pii_email`

**ISSUE-3.4.2: Retention & Deletion Test Missing Data Governance Integration**
- **Location**: PR-UBI-03, Section 329-330
- **Problem**: Test mentions "Data Governance triggers deletion" but:
  - Data Governance deletion trigger mechanism is not specified
  - How to verify deletion completeness is unclear
- **Impact**: **MEDIUM** - Test implementation unclear
- **Recommendation**: 
  - Specify: Use Data Governance API to trigger deletion: `POST /privacy/v1/retention/delete?tenant_id={tenant_id}&time_range={range}`
  - Verify: Query UBI for deleted time range → returns empty result
  - Verify: Query ERIS for deleted receipts → returns empty result (if receipts reference deleted data)

### 3.5 Observability Tests (Section 13.5)

#### ✅ Strengths
- Telemetry emission test is specified

#### ⚠️ Issues Identified

**ISSUE-3.5.1: Observability Metrics Schema Not Specified**
- **Location**: OB-UBI-01, Section 332-333
- **Problem**: Test asserts metrics like `ubi_events_processed_total` but:
  - Complete metrics schema is not specified
  - Metric labels/dimensions are not defined
  - Metric aggregation rules are unclear
- **Impact**: **MEDIUM** - Observability implementation unclear
- **Recommendation**: 
  - Define metrics schema:
    - `ubi_events_processed_total{tenant_id, event_type, status}` (counter)
    - `ubi_signals_generated_total{tenant_id, dimension, signal_type}` (counter)
    - `ubi_anomalies_total{tenant_id, dimension, severity}` (counter)
    - `ubi_feature_computation_duration_seconds{tenant_id, feature_name}` (histogram)
  - Add to NFR-5 (Observability) section

### 3.6 Security & Authorization Tests (Section 13.6)

#### ✅ Strengths
- Actor-level access control test is specified
- Aggregated vs actor-level access test is included

#### ⚠️ Issues Identified

**ISSUE-3.6.1: IAM Integration Test Setup Missing**
- **Location**: ST-UBI-01, Section 336-340
- **Problem**: Test mentions "token bound to the correct tenant but without the IAM scopes" but:
  - IAM token generation for tests is not specified
  - IAM scope names are not defined
- **Impact**: **MEDIUM** - Test implementation unclear
- **Recommendation**: 
  - Specify: Use IAM test token generation API or mock IAM
  - Define IAM scopes: `ubi:read:actor`, `ubi:read:team`, `ubi:read:tenant`
  - Test with token missing `ubi:read:actor` scope → expect 403 Forbidden

**ISSUE-3.6.2: Cross-Tenant Access Test Missing**
- **Location**: ST-UBI-02, Section 341-343
- **Problem**: Test only covers aggregated vs actor-level access, missing:
  - Cross-tenant access attempt (tenant A token querying tenant B data)
  - Privileged role access (product_ops role accessing all tenants)
- **Impact**: **MEDIUM** - Security test coverage gap
- **Recommendation**: 
  - Add test: Tenant A token querying tenant B actor profile → expect 403 Forbidden
  - Add test: Product ops role querying all tenants → expect 200 with all tenant data
  - Verify IAM enforces tenant isolation

### 3.7 Fairness & Misuse-Prevention Tests (Section 13.7)

#### ✅ Strengths
- Disabled signal classes test is specified
- Prohibited feature use test is included

#### ⚠️ Issues Identified

**ISSUE-3.7.1: Policy Configuration Test Data Missing**
- **Location**: FM-UBI-01, Section 346-348
- **Problem**: Test mentions "configure a tenant so that certain signal classes are disabled" but:
  - Policy configuration format is not specified
  - How to configure policy is unclear
- **Impact**: **MEDIUM** - Test setup unclear
- **Recommendation**: 
  - Specify: Use UBI config API `PUT /v1/ubi/config/{tenant_id}` with `enabled_signal_types = ["risk", "opportunity"]` (excluding "informational")
  - Verify: Query signals → only risk and opportunity signals returned
  - Verify: Stream subscription → only enabled signal types emitted

### 3.8 Resilience & Fault-Tolerance Tests (Section 13.8)

#### ✅ Strengths
- PM-3 outage test is specified
- ERIS dependency test is included

#### ⚠️ Issues Identified

**ISSUE-3.8.1: Degradation Behavior Not Specified**
- **Location**: RF-UBI-01, Section 354-356
- **Problem**: Test asserts "UBI continues to serve existing profiles" but:
  - Degradation behavior is not specified (what is "stale" threshold?)
  - How UBI marks data as "stale" is unclear
- **Impact**: **MEDIUM** - Degradation behavior unclear
- **Recommendation**: 
  - Specify: Data older than 1 hour is marked as "stale" (configurable)
  - Add `stale: true` flag to API responses when data is stale
  - Document degradation behavior in NFR-6 (Reliability)

**ISSUE-3.8.2: ERIS Failure Handling Test Incomplete**
- **Location**: RF-UBI-02, Section 357-359
- **Problem**: Test mentions "fails receipt writes in a controlled way" but:
  - Receipt queueing mechanism is not specified
  - Receipt retry strategy is not defined
  - Receipt loss prevention is unclear
- **Impact**: **MEDIUM** - Receipt reliability unclear
- **Recommendation**: 
  - Specify: Queue receipts in local persistent store (e.g., SQLite, file-based queue)
  - Implement retry with exponential backoff (max 24 hours)
  - If retry fails: Move to DLQ for manual intervention
  - Document in FR-13 or NFR-6

---

## 4. Consistency & Alignment Analysis

### 4.1 Module ID and Naming Consistency

#### ✅ Strengths
- Module ID `EPC-9` is consistent with architecture patterns
- Module name "User Behaviour Intelligence" is clear

#### ⚠️ Issues Identified

**ISSUE-4.1.1: Module ID Mapping Missing**
- **Location**: Throughout document
- **Problem**: UBI uses `EPC-9` but architecture documents show M-number mappings (e.g., EPC-1 → M21)
- **Impact**: **LOW** - Codebase mapping unclear
- **Recommendation**: 
  - Define M-number mapping for EPC-9 (e.g., EPC-9 → M35)
  - Update `docs/architecture/MODULE_ID_MAPPING.md` (if exists) or create mapping
  - Reference in UBI PRD

### 4.2 Data Model Consistency

#### ⚠️ Issues Identified

**ISSUE-4.2.1: Timestamp Field Naming Inconsistency**
- **Location**: Section 10.1, Line 204
- **Problem**: UBI uses `ts` for timestamp, but:
  - PM-3 uses `occurred_at` and `ingested_at`
  - ERIS uses `timestamp_utc` and `timestamp_monotonic_ms`
  - Detection Engine uses `timestamp_utc`
- **Impact**: **MEDIUM** - Field mapping complexity
- **Recommendation**: 
  - Align with platform standard: Use `timestamp_utc` (ISO 8601) and `timestamp_monotonic_ms` (if monotonic timestamp needed)
  - Map PM-3 `occurred_at` → UBI `timestamp_utc`
  - Update Section 10.1

**ISSUE-4.2.2: Tenant ID Field Consistency**
- **Location**: Throughout data models
- **Problem**: UBI uses `tenant_id` consistently, which aligns with platform patterns ✅
- **Impact**: None (consistent)
- **Recommendation**: None needed

### 4.3 API Pattern Consistency

#### ⚠️ Issues Identified

**ISSUE-4.3.1: API Versioning Pattern**
- **Location**: Section 11, all API endpoints
- **Problem**: UBI uses `/v1/ubi/...` but:
  - Some modules use `/v1/{module_name}/...` (e.g., `/v1/evidence/...`)
  - Versioning strategy is not specified
- **Impact**: **LOW** - Consistency issue
- **Recommendation**: 
  - Align with platform API versioning pattern (if documented)
  - Or: Document UBI API versioning strategy (semantic versioning in path?)

### 4.4 Receipt Schema Consistency

#### ⚠️ Issues Identified

**ISSUE-4.4.1: Receipt Gate ID Not Standardized**
- **Location**: FR-13 (implicit)
- **Problem**: UBI receipt `gate_id` value is not specified
- **Impact**: **MEDIUM** - Receipt identification unclear
- **Recommendation**: 
  - Define `gate_id = "ubi"` or `gate_id = "epc-9"`
  - Align with other modules (Detection Engine uses `gate_id = "detection-engine-core"`)

---

## 5. Industry Best Practices Analysis

### 5.1 Behavioral Analytics Best Practices

#### ✅ Strengths
- SPACE framework alignment (Section 3.1, Line 35)
- DORA metrics support (Section 3.1, Line 34)
- UEBA-style anomaly detection (Section 4.1, Line 51)

#### ⚠️ Issues Identified

**ISSUE-5.1.1: Baseline Warm-up Period Not Specified**
- **Location**: Section 14, Risk Mitigation, Line 367
- **Problem**: Risk mitigation mentions "warm-up period" but:
  - Warm-up duration is not specified
  - Warm-up behavior (what happens during warm-up?) is unclear
- **Impact**: **MEDIUM** - Operational uncertainty
- **Recommendation**: 
  - Define warm-up period: 7 days minimum data collection before baseline computation
  - During warm-up: Mark baselines as "low confidence", do not emit anomalies
  - Document in FR-3 (Baseline Computation)

**ISSUE-5.1.2: False Positive Rate Targets Missing**
- **Location**: FR-4 (Anomaly Detection)
- **Problem**: Anomaly detection does not specify false positive rate targets
- **Impact**: **MEDIUM** - Operational quality unclear
- **Recommendation**: 
  - Define false positive rate target: < 5% (industry standard for UEBA)
  - Implement feedback loop to tune thresholds based on false positive rate
  - Document in FR-4

**ISSUE-5.1.3: Privacy-Preserving Analytics Techniques Not Specified**
- **Location**: FR-8 (Privacy)
- **Problem**: UBI mentions "privacy-preserving" but:
  - Differential privacy techniques are not mentioned
  - k-anonymity requirements are not specified
  - Aggregation thresholds are mentioned but not quantified
- **Impact**: **MEDIUM** - Privacy implementation unclear
- **Recommendation**: 
  - Specify aggregation threshold: Minimum 5 actors per team metric (k-anonymity)
  - Consider differential privacy for sensitive metrics (if needed)
  - Document in FR-8

### 5.2 Scalability Best Practices

#### ✅ Strengths
- Horizontal scalability is mentioned (NFR-3, Line 184)
- Time-series storage is specified (Section 15, Line 372)

#### ⚠️ Issues Identified

**ISSUE-5.2.1: Data Partitioning Strategy Not Specified**
- **Location**: NFR-3, Section 179
- **Problem**: Scalability mentions "time-series/columnar storage" but:
  - Partitioning key is not specified (tenant_id? timestamp? both?)
  - Partition size limits are not defined
- **Impact**: **MEDIUM** - Scalability implementation unclear
- **Recommendation**: 
  - Specify partitioning: By `tenant_id` and `dt` (date) for efficient queries
  - Define partition size limit: Max 10GB per partition
  - Document in Implementation Notes (Section 15)

**ISSUE-5.2.2: Feature Store Integration Not Mentioned**
- **Location**: Section 15, Line 371
- **Problem**: Implementation Notes mention "feature store" but:
  - Feature store technology is not specified
  - Feature store integration pattern is unclear
- **Impact**: **LOW** - Implementation guidance unclear
- **Recommendation**: 
  - Clarify: UBI may use platform feature store (if exists) or implement local feature storage
  - Document feature store requirements (if any)

---

## 6. Critical Gaps Summary

### 🔴 CRITICAL (Must Fix Before Implementation)

1. **ISSUE-1.1.1**: BehaviouralEvent schema misalignment with PM-3 SignalEnvelope
2. **ISSUE-1.2.2**: Missing IAM integration in API contracts
3. **ISSUE-1.4.1**: Receipt schema not specified
4. **ISSUE-2.1.1**: Event consumption mechanism unspecified
5. **ISSUE-2.2.1**: ERIS receipt ingestion API not specified
6. **ISSUE-2.6.1**: IAM integration not specified

### 🟡 HIGH (Should Fix Before Implementation)

7. **ISSUE-1.1.2**: Actor type enum inconsistency
8. **ISSUE-1.2.3**: Event stream specification missing
9. **ISSUE-1.3.1**: Missing event type taxonomy
10. **ISSUE-1.3.4**: Evidence linking mechanism unclear
11. **ISSUE-2.1.2**: Event type filtering not aligned with PM-3
12. **ISSUE-2.1.3**: Privacy tags mapping unclear
13. **ISSUE-2.3.1**: MMM signal consumption contract unclear
14. **ISSUE-2.4.1**: Detection Engine signal format unclear
15. **ISSUE-2.5.1**: Data Governance API contract missing

### 🟢 MEDIUM (Should Fix During Implementation)

16. **ISSUE-1.3.2**: Baseline computation algorithm unspecified
17. **ISSUE-1.3.3**: Anomaly detection thresholds not quantified
18. **ISSUE-2.4.2**: Signal severity threshold not defined
19. **ISSUE-3.3.1**: Performance SLOs not defined
20. **ISSUE-4.2.1**: Timestamp field naming inconsistency

---

## 7. Recommendations

### 7.1 Immediate Actions (Before Implementation)

1. **Resolve PM-3 Integration Contract**:
   - Update FR-1 to specify UBI consumes `SignalEnvelope` from PM-3
   - Define field mapping: `occurred_at` → `timestamp_utc`, `payload` → `properties`
   - Specify event consumption mechanism (HTTP API? Event stream?)

2. **Define Receipt Schema**:
   - Use canonical receipt schema from `docs/architecture/receipt-schema-cross-reference.md`
   - Define `gate_id = "ubi"` for UBI receipts
   - Specify required receipt fields in FR-13

3. **Add IAM Integration**:
   - Integrate with IAM (EPC-1) for token verification
   - Define IAM roles: `ubi:read:actor`, `ubi:read:team`, `ubi:read:tenant`, `ubi:write:config`
   - Enforce tenant isolation in all APIs

4. **Specify ERIS Integration**:
   - Use ERIS API: `POST /v1/evidence/receipts` for receipt emission
   - Implement retry logic with exponential backoff
   - Handle ERIS unavailability gracefully

5. **Standardize Actor Type Enum**:
   - Use: `human`, `ai_agent`, `service` (remove `hybrid` or define separately)
   - Update all references in UBI PRD

### 7.2 Implementation Phase Actions

6. **Define Event Type Taxonomy**:
   - Create canonical event type list (e.g., `file_edited`, `build_failed`, `pr_created`)
   - Specify mapping from PM-3 `signal_type` to UBI `event_type`

7. **Specify Baseline Algorithm**:
   - Use exponential moving average with configurable alpha (default: 0.1)
   - Define minimum data points: 7 days
   - Specify outlier handling: exclude outliers beyond 3 standard deviations

8. **Define Performance SLOs**:
   - Event processing: 1000 events/second, p95 latency < 5 seconds
   - Baseline recompute: 1000 actors within 1 hour
   - Add to NFR-2 and NFR-3

9. **Complete Test Specifications**:
   - Add test data generation methodology
   - Specify IAM token generation for security tests
   - Define ERIS receipt verification in integration tests

### 7.3 Documentation Enhancements

10. **Add Integration Diagrams**:
    - Create sequence diagrams for: PM-3 → UBI → MMM/Detection flows
    - Document receipt emission flow: UBI → ERIS

11. **Expand API Documentation**:
    - Add authentication/authorization requirements to each endpoint
    - Specify error response schemas
    - Document rate limiting (if applicable)

12. **Clarify Evidence Storage**:
    - Specify evidence storage location (ERIS or UBI local)
    - Define evidence handle format
    - Document evidence retention policy

---

## 8. Validation Checklist

### 8.1 Pre-Implementation Checklist

- [ ] PM-3 integration contract defined (event consumption, field mapping)
- [ ] Receipt schema specified (gate_id, required fields)
- [ ] IAM integration specified (token verification, roles, tenant isolation)
- [ ] ERIS integration specified (API endpoint, retry logic, error handling)
- [ ] Actor type enum standardized (`human`, `ai_agent`, `service`)
- [ ] Event type taxonomy defined
- [ ] API authentication/authorization requirements added

### 8.2 Implementation Checklist

- [ ] Baseline computation algorithm specified
- [ ] Anomaly detection thresholds quantified
- [ ] Performance SLOs defined
- [ ] Evidence storage location specified
- [ ] Data Governance API contracts defined
- [ ] Test data generation methodology specified

### 8.3 Post-Implementation Checklist

- [ ] Integration tests pass (PM-3, ERIS, IAM, MMM, Detection)
- [ ] Performance tests meet SLOs
- [ ] Security tests pass (IAM, tenant isolation)
- [ ] Privacy tests pass (data minimisation, aggregation thresholds)
- [ ] Observability metrics emitted correctly
- [ ] Receipts emitted to ERIS successfully

---

## 9. Conclusion

The UBI Module specification is **comprehensive and well-structured**, demonstrating strong alignment with privacy-first principles, behavioral analytics best practices (SPACE, DORA, UEBA), and platform architecture patterns.

However, **critical integration contracts must be resolved** before implementation can begin:
- PM-3 (Signal Ingestion) event consumption mechanism
- ERIS receipt emission API and schema
- IAM authentication/authorization integration
- Receipt schema definition

Additionally, several **high-priority clarifications** are needed:
- Event type taxonomy and mapping
- Evidence storage and linking
- MMM and Detection Engine signal consumption contracts
- Data Governance API integration

With these issues resolved, the UBI Module specification will be **production-ready** and aligned with ZeroUI platform standards.

---

**Report Status:** ✅ Complete  
**Next Steps:** Address CRITICAL and HIGH priority issues, then proceed with implementation planning.

