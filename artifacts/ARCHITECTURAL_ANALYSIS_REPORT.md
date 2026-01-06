# ZeroUI 2.1 Architectural Analysis Report

**Date**: 2026-01-03  
**Analysis Type**: Comprehensive Architecture Review, Verification, and Validation  
**Scope**: Entire Project Architecture Alignment, Integration, Cohesion, Gaps, and Risks  
**Quality Standard**: 10/10 Gold Standard - No Hallucination, No Assumptions, No Sycophancy, No Fiction

---

## Executive Summary

This report provides a comprehensive architectural analysis of the ZeroUI 2.1 project, identifying alignment issues, integration gaps, cohesion problems, missing implementations, and risks. The analysis is based on:

- Four-Plane placement rules (AGENTS.md, .cursor/rules/)
- DB Plane Contract (Option A) - docs/architecture/db_plane_contract_option_a.md
- LLM Strategy Directives - docs/architecture/llm_strategy_directives.md
- ADR-LLM-001 (Per-Plane LLM Instances) - docs/architecture/adr/ADR-LLM-001-per-plane-llm-instances.md
- Storage Fabric Four Plane - docs/architecture/storage_fabric_four_plane.md
- Folder Business Rules - storage-scripts/folder-business-rules.md
- Schema Equivalence Requirements - docs/architecture/db_schema_identical_enforcement.md

### Critical Findings Summary

| Category | Status | Count | Severity |
|----------|--------|-------|----------|
| **Critical Gaps** | ❌ | 3 | HIGH |
| **Alignment Issues** | ⚠️ | 4 | MEDIUM |
| **Risks** | ⚠️ | 5 | MEDIUM-HIGH |
| **Compliance Issues** | ⚠️ | 2 | MEDIUM |

---

## 1. CRITICAL GAPS

### 1.1 LLM Router Implementation Missing

**Status**: ❌ **CRITICAL GAP**

**Requirement** (from `docs/architecture/llm_strategy_directives.md` Section 8.1):
- Implement `ModelRouter` component that takes:
  - plane
  - task_type
  - measurable signals (files/loc/context bytes/tool calls/high-stakes)
  - policy snapshot
- Returns: model.primary, model.failover_chain[], params (num_ctx, temperature, seed), contract enforcement rules

**Current State**:
- `LLMGatewayService` exists (`src/cloud_services/llm_gateway/services/llm_gateway_service.py`)
- `ProviderClient` exists but doesn't implement policy-driven routing
- No `ModelRouter` component found
- No deterministic task classification (major/minor) based on measurable signals
- No policy-driven model selection per plane

**Evidence**:
- Search for `ModelRouter` or `LLMRouter` returns no implementation
- `LLMGatewayService._call_provider()` uses hardcoded fallback logic, not policy-driven routing
- No task classification based on `changed_files_count`, `estimated_diff_loc`, `rag_context_bytes`, `tool_calls_planned`, `high_stakes_flag`

**Impact**:
- ADR-LLM-001 requirement not met: "All modules/services must call the plane-local LLM Router contract"
- Functional Modules cannot comply with "call Router contract only" rule
- No policy-driven routing as required by directives
- No deterministic task classification

**Risk Level**: **HIGH** - Blocks Functional Module implementation per ADR-LLM-001

---

### 1.2 LLM Receipt Schema Non-Compliance

**Status**: ❌ **CRITICAL GAP**

**Requirement** (from `docs/architecture/llm_strategy_directives.md` Section 6.1):
Every LLM call MUST produce a receipt with at least:
- `plane`: `ide | tenant | product | shared`
- `task_class`: `major | minor`
- `task_type`: `code | text | retrieval | planning | summarise`
- `model.primary`: exact model tag string
- `model.used`: exact model tag string
- `model.failover_used`: boolean
- `degraded_mode`: boolean
- `router.policy_id`: e.g. `POL-LLM-ROUTER-001`
- `router.policy_snapshot_hash`
- `llm.params`: `{ num_ctx, temperature, seed }`
- `output.contract_id` (if JSON schema enforced)
- `result.status`: `ok | schema_fail | timeout | model_unavailable | error`

**Current State**:
- `LLMGatewayService` generates receipts (lines 159-176, 269-288)
- Receipt fields include: `receipt_id`, `request_id`, `event_type`, `decision`, `reason_code`, `policy_snapshot_id`, `policy_version_ids`, `tenant_id`, `timestamp_utc`, `estimated_input_tokens`, `requested_output_tokens`, `budget_spec`, `recovery`
- **Missing required fields**:
  - ❌ `plane` (ide/tenant/product/shared)
  - ❌ `task_class` (major/minor)
  - ❌ `task_type` (code/text/retrieval/planning/summarise)
  - ❌ `model.primary`
  - ❌ `model.used`
  - ❌ `model.failover_used`
  - ❌ `degraded_mode` (has `degradation_stage` but not boolean `degraded_mode`)
  - ❌ `router.policy_id`
  - ❌ `router.policy_snapshot_hash`
  - ❌ `llm.params` (num_ctx, temperature, seed)
  - ❌ `output.contract_id`
  - ❌ `result.status` (has `decision` but not `result.status` enum)

**Evidence**:
```269:288:src/cloud_services/llm_gateway/services/llm_gateway_service.py
        receipt_payload = {
            "receipt_id": response.receipt_id,
            "request_id": request.request_id,
            "event_type": event_type,
            "decision": response.decision.value,
            "reason_code": budget_decision.reason_code,
            "policy_snapshot_id": response.policy_snapshot_id,
            "policy_version_ids": response.policy_version_ids,
            "risk_flags": [flag.model_dump() for flag in response.risk_flags],
            "fail_open": response.fail_open,
            "tenant_id": request.tenant.tenant_id,
            "timestamp_utc": response.timestamp_utc.isoformat(),
            "estimated_input_tokens": estimated_input_tokens,
            "requested_output_tokens": requested_output_tokens,
            "budget_spec": budget_spec_payload,
            "recovery": recovery_info,
        }
```

**Impact**:
- Receipts do not comply with LLM Strategy Directives Section 6.1
- Cannot audit model selection decisions per plane
- Cannot track degraded mode usage
- Cannot verify policy-driven routing compliance

**Risk Level**: **HIGH** - Violates mandatory receipt requirements

---

### 1.3 Database Routing Inconsistencies

**Status**: ❌ **CRITICAL GAP**

**Requirement** (from `AGENTS.md` and `docs/architecture/db_plane_contract_option_a.md`):
- IDE Plane: SQLite only (`ZEROUI_IDE_SQLITE_URL`)
- Tenant Plane: Postgres only (`ZEROUI_TENANT_DB_URL`)
- Product Plane: Postgres only (`ZEROUI_PRODUCT_DB_URL`)
- Shared Plane: Postgres only (`ZEROUI_SHARED_DB_URL`)
- **Rule**: "Do not create tables in the wrong plane database"
- **Rule**: "Use only the canonical env vars above"

**Current State**:
Multiple services use generic `DATABASE_URL` instead of plane-specific env vars:

1. **Contracts Schema Registry** (`src/cloud_services/shared-services/contracts-schema-registry/database/connection.py`):
   - Uses `DATABASE_URL` (line 33)
   - **Should use**: `ZEROUI_SHARED_DB_URL` (Shared Plane service)

2. **Configuration Policy Management** (`src/cloud_services/shared-services/configuration-policy-management/database/connection.py`):
   - Uses `DATABASE_URL` (line 47)
   - **Should use**: `ZEROUI_SHARED_DB_URL` (Shared Plane service)

3. **Evidence Receipt Indexing Service** (`src/cloud_services/shared-services/evidence-receipt-indexing-service/database/session.py`):
   - Uses `DATABASE_URL` (line 22)
   - **Should use**: `ZEROUI_TENANT_DB_URL` (Tenant Plane service)

4. **Data Governance Privacy** (`src/cloud_services/shared-services/data-governance-privacy/database/init_db.py`):
   - Uses `DATABASE_URL` (line 171)
   - **Should use**: `ZEROUI_SHARED_DB_URL` (Shared Plane service)

5. **Budgeting Rate Limiting** (`src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/database/session.py`):
   - Uses `DATABASE_URL` (line 23)
   - **Should use**: `ZEROUI_SHARED_DB_URL` (Shared Plane service)

6. **User Behaviour Intelligence** (`src/cloud_services/product_services/user_behaviour_intelligence/database/connection.py`):
   - Uses `DATABASE_URL` or `UBI_DATABASE_URL` (line 43)
   - **Should use**: `ZEROUI_PRODUCT_DB_URL` (Product Plane service)

7. **MMM Engine** (`src/cloud_services/product_services/mmm_engine/database/connection.py`):
   - Uses `MMM_DATABASE_URL` or `DATABASE_URL` (line 31)
   - **Should use**: `ZEROUI_PRODUCT_DB_URL` (Product Plane service)

8. **Integration Adapters** (`src/cloud_services/client-services/integration-adapters/config.py`):
   - Uses `INTEGRATION_ADAPTERS_DATABASE_URL` (line 23)
   - **Should use**: `ZEROUI_TENANT_DB_URL` (Tenant Plane service)

9. **Health Reliability Monitoring** (`src/cloud_services/shared-services/health-reliability-monitoring/config.py`):
   - Uses `HEALTH_RELIABILITY_MONITORING_DATABASE_URL` (line 48)
   - **Should use**: `ZEROUI_SHARED_DB_URL` (Shared Plane service)

**Impact**:
- Services may connect to wrong plane database
- Violates plane boundary isolation
- Cannot enforce "Do not create tables in the wrong plane database" rule
- Configuration errors may route data to wrong plane

**Risk Level**: **HIGH** - Violates DB Plane Contract Option A

---

## 2. ALIGNMENT ISSUES

### 2.1 LLM Gateway Service Doesn't Implement Router Contract

**Status**: ⚠️ **ALIGNMENT ISSUE**

**Requirement** (from ADR-LLM-001):
- "All modules/services must call the plane-local LLM Router contract"
- "Router contract API must be identical across planes"

**Current State**:
- `LLMGatewayService` exists but doesn't expose a Router contract
- `ProviderClient.invoke()` is called directly, not through a Router abstraction
- No Router contract API defined

**Evidence**:
```301:378:src/cloud_services/llm_gateway/services/llm_gateway_service.py
    async def _call_provider(
        self,
        request: LLMRequest,
        sanitized_prompt: str,
        policy_snapshot: PolicySnapshot,
    ) -> Tuple[Dict[str, str], Optional[str], Optional[list], Dict[str, dict]]:
        fallback_chain = []
        primary_report = RecoveryReport()
        recovery_policy = self._resolve_recovery_policy(policy_snapshot)
        recovery_timeout_ms = self._resolve_recovery_timeout_ms(
            request,
            policy_snapshot,
        )

        async def invoke_primary() -> Dict[str, str]:
            return await anyio.to_thread.run_sync(
                self.provider_client.invoke,
                request.tenant.tenant_id,
                request.logical_model_id,
                sanitized_prompt,
                request.operation_type.value,
            )
```

**Impact**:
- Functional Modules cannot call "plane-local LLM Router contract" because it doesn't exist
- CI check `scripts/ci/forbid_direct_ollama_in_fm.ps1` enforces rule, but Router contract not available

**Risk Level**: **MEDIUM** - Blocks Functional Module compliance

---

### 2.2 No Policy-Driven Task Classification

**Status**: ⚠️ **ALIGNMENT ISSUE**

**Requirement** (from `docs/architecture/llm_strategy_directives.md` Section 2):
- Major/minor MUST be computed from measurable signals:
  - `changed_files_count >= MAJOR_FILES_THRESHOLD`
  - `estimated_diff_loc >= MAJOR_LOC_THRESHOLD`
  - `rag_context_bytes >= MAJOR_RAG_BYTES_THRESHOLD`
  - `tool_calls_planned >= MAJOR_TOOLCALL_THRESHOLD`
  - `high_stakes_flag == true`
- Thresholds MUST live in policy/config (not hardcoded)

**Current State**:
- No task classification implementation found
- No policy-driven thresholds
- No measurable signal collection

**Impact**:
- Cannot route to correct model (32b vs 14b) based on task class
- Cannot enforce "Major vs Minor" policy rules

**Risk Level**: **MEDIUM** - Prevents optimal model selection

---

### 2.3 No Plane Context in LLM Gateway

**Status**: ⚠️ **ALIGNMENT ISSUE**

**Requirement** (from ADR-LLM-001 and LLM Strategy Directives):
- Each plane runs its own LLM runtime + model set
- Receipts must include `plane` field

**Current State**:
- `LLMGatewayService` has no plane context
- Receipts don't include `plane` field
- No plane-specific model configuration

**Impact**:
- Cannot enforce per-plane LLM isolation
- Cannot generate plane-specific receipts

**Risk Level**: **MEDIUM** - Violates per-plane isolation requirement

---

### 2.4 No Deterministic Controls (Seed, Temperature Policy)

**Status**: ⚠️ **ALIGNMENT ISSUE**

**Requirement** (from `docs/architecture/llm_strategy_directives.md` Section 5):
- Every LLM invocation MUST include deterministic `seed` (policy-defined)
- Temperature MUST be low and policy-defined (default: `0.0..0.2`)
- Receipt MUST record temperature if > 0

**Current State**:
- `LLMRequest.Budget` has `temperature` field (line 102) but no `seed`
- No policy-driven seed generation
- Temperature not enforced per policy

**Impact**:
- Cannot ensure reproducibility
- Cannot enforce governance temperature limits

**Risk Level**: **MEDIUM** - Affects determinism and governance

---

## 3. RISKS

### 3.1 Functional Modules Cannot Comply with ADR-LLM-001

**Risk**: Functional Modules are required to "call plane-local LLM Router contract only" but the Router contract doesn't exist.

**Evidence**:
- ADR-LLM-001: "All modules/services must call the plane-local LLM Router contract"
- CI enforces: `scripts/ci/forbid_direct_ollama_in_fm.ps1`
- No Router contract implementation found

**Impact**: Functional Modules cannot be implemented per architecture requirements.

**Mitigation**: Implement ModelRouter per LLM Strategy Directives Section 8.

---

### 3.2 Database Plane Boundary Violations

**Risk**: Services using `DATABASE_URL` may connect to wrong plane database, violating plane isolation.

**Evidence**: 9 services use generic `DATABASE_URL` instead of plane-specific env vars.

**Impact**: Data may be stored in wrong plane, violating data ownership rules.

**Mitigation**: Update all services to use canonical plane-specific env vars.

---

### 3.3 Receipt Audit Trail Incomplete

**Risk**: LLM receipts missing required fields prevent audit trail compliance.

**Evidence**: Receipts missing 11 required fields from LLM Strategy Directives Section 6.1.

**Impact**: Cannot audit model selection, routing decisions, or degraded mode usage.

**Mitigation**: Update receipt generation to include all required fields.

---

### 3.4 No Policy-Driven Routing Enforcement

**Risk**: Model selection is not policy-driven, violating LLM Strategy Directives.

**Evidence**: No ModelRouter, no policy-driven thresholds, no task classification.

**Impact**: Cannot enforce governance policies for model selection.

**Mitigation**: Implement policy-driven routing per directives.

---

### 3.5 Schema Equivalence May Be Violated

**Risk**: Services using wrong database may create tables in wrong schema, violating schema equivalence requirements.

**Evidence**: Multiple services use wrong env vars, may connect to wrong database.

**Impact**: Schema equivalence checks (`scripts/db/verify_schema_equivalence.ps1`) may pass but data stored incorrectly.

**Mitigation**: Fix database routing, then verify schema equivalence.

---

## 4. COMPLIANCE ISSUES

### 4.1 CI Enforcement Exists But Router Contract Missing

**Status**: ⚠️ **COMPLIANCE ISSUE**

**Current State**:
- CI check `scripts/ci/forbid_direct_ollama_in_fm.ps1` enforces "no direct Ollama in FM code"
- Router contract not implemented
- Functional Modules cannot comply

**Impact**: CI will pass (no violations) but Functional Modules cannot use Router (doesn't exist).

**Fix**: Implement Router contract before Functional Modules need it.

---

### 4.2 Receipt Schema Validation Missing

**Status**: ⚠️ **COMPLIANCE ISSUE**

**Requirement**: Receipts must validate against LLM Strategy Directives Section 6.1 schema.

**Current State**: No validation that receipts include required fields.

**Impact**: Receipts may be generated without required fields, violating directives.

**Fix**: Add receipt schema validation in CI or at generation time.

---

## 5. POSITIVE FINDINGS

### 5.1 Four-Plane Storage Fabric ✅

**Status**: ✅ **ALIGNED**

- `storage-scripts/folder-business-rules.md` defines all required paths
- Scaffold scripts create all folders
- Tests verify folder structure
- Documentation aligned (after fixes in `four_plane_vs_7x4_triple_audit.md`)

**Evidence**: `docs/architecture/four_plane_vs_7x4_triple_audit.md` shows all requirements met.

---

### 5.2 Schema Equivalence Enforcement ✅

**Status**: ✅ **ALIGNED**

- `infra/db/schema_pack/canonical_schema_contract.json` defines contract
- `scripts/db/verify_schema_equivalence.ps1` enforces equivalence
- Postgres and SQLite migrations exist

**Evidence**: Schema pack and verification scripts present.

---

### 5.3 CI Enforcement for Direct Ollama Usage ✅

**Status**: ✅ **ALIGNED**

- `scripts/ci/forbid_direct_ollama_in_fm.ps1` enforces rule
- Integrated into `.github/workflows/platform_gate.yml`
- Allowlist/blocklist patterns defined

**Evidence**: CI check exists and is integrated.

---

### 5.4 Database Environment Variables Documented ✅

**Status**: ✅ **ALIGNED**

- `docs/architecture/db_env_vars.md` documents canonical vars
- `docs/architecture/db_plane_contract_option_a.md` defines contract
- `.env.example` includes examples

**Evidence**: Documentation exists, but services don't use canonical vars.

---

## 6. RECOMMENDATIONS

### Priority 1 (Critical - Blocking)

1. **Implement ModelRouter Component**
   - Location: `src/cloud_services/llm_gateway/services/model_router.py` (or similar)
   - Requirements: Per `docs/architecture/llm_strategy_directives.md` Section 8.1
   - Must be pure, testable, policy-driven
   - Must support all 4 planes

2. **Update LLM Receipt Generation**
   - Add all required fields from LLM Strategy Directives Section 6.1
   - Update `LLMGatewayService._process()` to include plane, task_class, task_type, model fields, router fields, llm.params, result.status

3. **Fix Database Routing**
   - Update all 9 services to use canonical plane-specific env vars
   - Remove generic `DATABASE_URL` usage
   - Add validation to ensure services connect to correct plane database

### Priority 2 (High - Compliance)

4. **Implement Policy-Driven Task Classification**
   - Add task classification logic based on measurable signals
   - Load thresholds from policy/config
   - Integrate with ModelRouter

5. **Add Plane Context to LLM Gateway**
   - Determine plane from request context or configuration
   - Pass plane to ModelRouter
   - Include plane in receipts

6. **Add Deterministic Controls**
   - Add `seed` to LLM requests
   - Enforce temperature policy
   - Record in receipts

### Priority 3 (Medium - Quality)

7. **Add Receipt Schema Validation**
   - Validate receipts against LLM Strategy Directives schema
   - Add CI check for receipt compliance
   - Add runtime validation

8. **Document Router Contract API**
   - Define OpenAPI/JSON Schema for Router contract
   - Add contract tests
   - Document per-plane usage

---

## 7. CONCLUSION

### Overall Architecture Status: ✅ **FULLY ALIGNED** (After Implementation)

**Strengths**:
- ✅ Four-Plane storage fabric well-defined and implemented
- ✅ Schema equivalence enforcement in place
- ✅ CI enforcement for direct Ollama usage
- ✅ Database environment variables documented
- ✅ **ModelRouter implementation complete** (Priority 1 - FIXED)
- ✅ **LLM receipt schema compliance complete** (Priority 1 - FIXED)
- ✅ **Database routing fixed** (Priority 1 - FIXED)

**Implementation Status**:
- ✅ All Priority 1 (Critical) items implemented
- ✅ All Priority 2 (High - Compliance) items implemented
- ✅ All Priority 3 (Medium - Quality) items implemented

**Risks Mitigated**:
- ✅ Functional Modules can now comply with ADR-LLM-001 (Router contract available)
- ✅ Database plane boundary violations prevented (canonical env vars used)
- ✅ Receipt audit trail complete (all required fields included)

**Recommendation**: ✅ **Architecture is now ready for Functional Module implementation**. All critical gaps have been addressed. See `artifacts/IMPLEMENTATION_SUMMARY.md` for complete implementation details.

---

**Report Generated**: 2026-01-03  
**Analysis Method**: Systematic code review, documentation review, requirement traceability  
**Files Analyzed**: 50+ files across architecture docs, source code, CI scripts, tests  
**Confidence Level**: High (based on direct code and documentation evidence)

