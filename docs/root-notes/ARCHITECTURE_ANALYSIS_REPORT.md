# ZeroUI 2.0 Architecture Analysis Report
**Date:** 2025-01-27  
**Scope:** Comprehensive analysis of CCCS module implementation, interoperability, integrity, cohesiveness, consistency, and architectural factors

---

## Executive Summary

This report provides a triple analysis of the ZeroUI 2.0 project, focusing on the Cross-Cutting Concern Services (CCCS) module implementation and its integration with the broader architecture. The analysis identifies critical inconsistencies, missing integration points, and architectural violations.

**Overall Assessment:** ⚠️ **CRITICAL ISSUES IDENTIFIED**

---

## 1. CRITICAL ARCHITECTURAL INCONSISTENCIES

### 1.1 Code State Mismatch (CRITICAL)

**Issue:** The attached user changes show significant modifications to `IdentityService`, `RateLimiterService`, and `PolicyRuntime` that implement offline-first operation with WAL queuing and caching. However, the actual codebase files do not reflect these changes.

**Evidence:**
- User's attached `identity/service.py` shows:
  - `__init__` accepts `wal: Optional[Any] = None`
  - `resolve_actor` accepts `use_cache: bool = True`
  - Implements `process_wal_entry` method
  - Implements `_queue_epc1_call` method
  - Has `_actor_cache` dictionary

- Actual `identity/service.py` shows:
  - No `wal` parameter in `__init__`
  - No `use_cache` parameter in `resolve_actor`
  - No `process_wal_entry` method
  - No `_queue_epc1_call` method
  - No `_actor_cache` dictionary

**Impact:** The implementation does not match the user's intended changes, violating PRD requirements for offline-first operation.

**Recommendation:** Verify that user's changes have been properly committed and merged.

---

### 1.2 Missing Integration Points

#### 1.2.1 Edge Agent → CCCS Integration (MISSING)

**Issue:** The Edge Agent (`src/edge-agent/EdgeAgent.ts`) does not import or use CCCS runtime.

**Evidence:**
- `EdgeAgent.ts` has no references to `CCCS`, `cccs`, or `shared_libs`
- Edge Agent implements its own receipt generation (`ReceiptGenerator`, `ReceiptStorageService`)
- Edge Agent implements its own policy storage (`PolicyStorageService`)
- No integration with CCCS runtime for identity, policy, or budget checks

**PRD Requirement:** "CCCS runs inside: Edge Agent (offline-first), Backend (Tenant + Product Cloud)"

**Impact:** Edge Agent is not using the unified CCCS SDK, violating architectural separation of concerns.

**Recommendation:** 
1. Create a Python bridge/FFI interface for Edge Agent to call CCCS runtime
2. Or refactor Edge Agent to use CCCS services via HTTP/gRPC
3. Remove duplicate receipt/policy logic from Edge Agent

---

#### 1.2.2 Cloud Services → CCCS Integration (MISSING)

**Issue:** Cloud Services modules do not import or use CCCS runtime.

**Evidence:**
- No references to `CCCS`, `cccs`, or `shared_libs` in `src/cloud-services/`
- Cloud Services would need to use CCCS for identity, policy, receipts, etc.

**PRD Requirement:** "CCCS runs inside: Backend (Tenant + Product Cloud)"

**Impact:** Cloud Services cannot leverage CCCS façade services, leading to potential duplication.

**Recommendation:**
1. Integrate CCCS runtime into Cloud Services FastAPI applications
2. Use CCCS for identity resolution, policy evaluation, receipt generation
3. Ensure Cloud Services use CCCS adapters (EPC-1, EPC-3, EPC-13, PM-7, EPC-11)

---

### 1.3 Policy Runtime Implementation Mismatch

**Issue:** User's attached changes show `PolicyRuntime` using offline HMAC-based signature validation, but actual codebase shows EPC-3 adapter-based evaluation.

**User's Changes:**
- `PolicyConfig` has `signing_secrets: Sequence[bytes]` instead of `epc3_base_url`
- `PolicyRuntime` validates signatures using HMAC instead of calling EPC-3
- Policy evaluation is entirely offline using cached snapshot

**Actual Codebase:**
- `PolicyConfig` has `epc3_base_url: str`
- `PolicyRuntime` calls `EPC3PolicyAdapter` for signature validation and evaluation
- Policy evaluation makes synchronous network calls to EPC-3

**PRD Requirement:** "Per PRD §9: No network policy evaluation; GSMD snapshots validated offline"

**Impact:** Current implementation violates PRD requirement for offline policy evaluation.

**Recommendation:** Verify that user's changes are properly applied to the codebase.

---

## 2. MODULE INTEROPERABILITY ISSUES

### 2.1 Type System Consistency

**Status:** ✅ **GOOD**

**Analysis:**
- `types.py` defines consistent data structures (`ActorBlock`, `PolicyDecision`, `BudgetDecision`, etc.)
- All services use these types consistently
- Type annotations are present throughout

**Minor Issues:**
- `ActorBlock` includes `salt_version` and `monotonic_counter` (per PRD §9), but these are not always populated in receipts
- Receipt generation in `runtime.py` only includes `actor_id`, `actor_type`, `session_id` - missing `provenance_signature`, `salt_version`, `monotonic_counter`

**Recommendation:** Update `runtime.py:execute_flow` to include all `ActorBlock` fields in receipt `actor` field.

---

### 2.2 Error Handling Consistency

**Status:** ✅ **GOOD**

**Analysis:**
- Consistent exception hierarchy (`CCCSError` base class)
- All services raise appropriate exceptions (`ActorUnavailableError`, `PolicyUnavailableError`, `BudgetExceededError`, etc.)
- Error taxonomy framework is implemented

**Issue:**
- `runtime.py:execute_flow` does not catch and normalize all exceptions through taxonomy
- Some exceptions may leak as raw adapter errors

**Recommendation:** Wrap all adapter exceptions in `execute_flow` with taxonomy normalization.

---

### 2.3 Configuration Consistency

**Status:** ⚠️ **ISSUES IDENTIFIED**

**Analysis:**
- `CCCSConfig` dataclass is well-structured
- All service configs are properly typed

**Issues:**
1. `PolicyConfig` in actual codebase uses `epc3_base_url`, but user's changes show `signing_secrets` - inconsistency
2. `ReceiptConfig` requires `epc11_base_url` and `epc11_key_id`, but user's changes show `epc11_signing_seed` - inconsistency
3. `IdentityConfig` and `RateLimiterConfig` do not have `fallback_enabled` flag in actual codebase, but user's changes show it

**Recommendation:** Align configuration with user's intended changes for offline-first operation.

---

## 3. ARCHITECTURAL INTEGRITY

### 3.1 PRD Compliance

#### 3.1.1 Zero Synchronous Network Calls (VIOLATION)

**PRD Requirement:** "Zero synchronous network calls on critical path (Edge + Backend)"

**Current Implementation:**
- `IdentityService.resolve_actor` makes synchronous `loop.run_until_complete` call to EPC-1
- `RateLimiterService.check_budget` makes synchronous `loop.run_until_complete` call to EPC-13
- `PolicyRuntime.evaluate` makes synchronous `loop.run_until_complete` call to EPC-3
- `ReceiptService.write_receipt` makes synchronous `loop.run_until_complete` call to EPC-11 and PM-7

**User's Intended Changes:**
- `IdentityService.resolve_actor` uses cache-first approach, queues to WAL when offline
- `RateLimiterService.check_budget` uses cache-first approach, queues to WAL when offline
- `PolicyRuntime.evaluate` performs offline evaluation using cached snapshot
- `ReceiptService.write_receipt` attempts PM-7 indexing but marks as `pending_sync` if fails

**Status:** ❌ **VIOLATION** (unless user's changes are applied)

---

#### 3.1.2 Offline-First Operation (VIOLATION)

**PRD Requirement:** "Edge Agent (offline-first): May enter degraded mode if upstream EPC services are unreachable"

**Current Implementation:**
- `runtime.py:execute_flow` does not check `_dependencies_ready` before calling services
- Services raise exceptions immediately if adapters unavailable
- No fallback to cached data or WAL queuing

**User's Intended Changes:**
- `runtime.py:execute_flow` passes `use_cache=(not self._dependencies_ready)` to services
- Services use cache when `use_cache=True`, queue to WAL when cache miss
- Enables 48h offline operation

**Status:** ❌ **VIOLATION** (unless user's changes are applied)

---

#### 3.1.3 WAL Coverage (PARTIAL)

**PRD Requirement:** "Receipts, budget events, and policy snapshots land in WAL-backed queues"

**Current Implementation:**
- Receipts are written to WAL via `OfflineCourier`
- Budget events are NOT persisted to WAL in `runtime.py:execute_flow`
- Policy snapshots are NOT persisted to WAL in `runtime.py:execute_flow`

**User's Intended Changes:**
- Budget snapshots are appended to WAL in `execute_flow`
- Policy snapshots are appended to WAL in `execute_flow`
- WAL drain worker processes queued EPC calls

**Status:** ⚠️ **PARTIAL** (unless user's changes are applied)

---

### 3.2 Initialization Order

**PRD Requirement:** "Initialization order is fixed: IAPS → CFFS → PREE → RLBGS → OTCS → RGES → SSDRS → ETFHF"

**Current Implementation:**
- `runtime.py:__init__` initializes services in order: Identity → Policy → Config → Redaction → RateLimiter → Receipts → Observability → Taxonomy
- Order is: IAPS → PREE → CFFS → SSDRS → RLBGS → RGES → OTCS → ETFHF

**Status:** ❌ **VIOLATION** - Order does not match PRD requirement

**Recommendation:** Reorder initialization to match PRD: IAPS → CFFS → PREE → RLBGS → OTCS → RGES → SSDRS → ETFHF

---

### 3.3 Bootstrap Sequence

**PRD Requirement:** 
- "Dependency health checks are re-run every 30 seconds during bootstrap"
- "Failure to reach ready state within 5 minutes triggers `cccs_bootstrap_timeout` error taxonomy"

**Current Implementation:**
- `bootstrap` method has `poll_interval` parameter (default 5.0s, not 30s)
- `timeout_seconds` parameter (default 300.0s = 5 minutes) ✅
- But bootstrap does not perform API version negotiation per PRD §6.4

**Status:** ⚠️ **PARTIAL COMPLIANCE**

**Recommendation:** 
1. Change default `poll_interval` to 30.0 seconds
2. Add API version negotiation during bootstrap
3. Emit ETFHF entries for version mismatches

---

## 4. COHESIVENESS ANALYSIS

### 4.1 Service Boundaries

**Status:** ✅ **GOOD**

**Analysis:**
- Services are well-separated (Identity, Policy, Config, Receipts, Redaction, RateLimiter, Observability, Errors)
- Each service has a single responsibility
- Adapters provide clean abstraction over EPC/PM services

---

### 4.2 Data Flow

**Status:** ⚠️ **ISSUES IDENTIFIED**

**Analysis:**
- `execute_flow` orchestrates the flow correctly
- But missing WAL persistence for budget and policy snapshots
- Receipt generation does not include all actor provenance fields

**Issues:**
1. `execute_flow` does not persist budget snapshots to WAL
2. `execute_flow` does not persist policy snapshots to WAL
3. Receipt `actor` field is incomplete (missing `provenance_signature`, `salt_version`, `monotonic_counter`)

---

### 4.3 Dependency Management

**Status:** ✅ **GOOD**

**Analysis:**
- Services depend on adapters, not on each other (except runtime orchestration)
- WAL is shared via `OfflineCourier`
- Clean dependency injection via config

---

## 5. CONSISTENCY ANALYSIS

### 5.1 Naming Conventions

**Status:** ✅ **GOOD**

**Analysis:**
- Consistent naming: `*Service`, `*Adapter`, `*Config`
- Method names follow Python conventions
- File names match module names

---

### 5.2 Error Handling Patterns

**Status:** ⚠️ **ISSUES IDENTIFIED**

**Analysis:**
- Most services raise appropriate exceptions
- But `runtime.py:execute_flow` does not consistently wrap exceptions

**Issue:**
```python
# Current (inconsistent):
actor = self._identity.resolve_actor(actor_context)  # May raise ActorUnavailableError
policy_decision = self._policy.evaluate(module_id, inputs)  # May raise PolicyUnavailableError
budget = self._ratelimiter.check_budget(...)  # May raise BudgetExceededError
```

**Recommendation:** Wrap all service calls in try/except and normalize through taxonomy.

---

### 5.3 Async/Sync Patterns

**Status:** ⚠️ **ISSUES IDENTIFIED**

**Analysis:**
- All adapters are async
- Services provide sync wrappers using `loop.run_until_complete`
- But this violates "zero synchronous network calls" requirement

**User's Intended Changes:**
- Services use cache-first approach
- Network calls are queued to WAL for background processing
- Eliminates synchronous network calls on critical path

---

## 6. MISSING FEATURES

### 6.1 Actor Provenance in Receipts

**PRD Requirement:** Receipts must include `actor.provenance_signature`, `salt_version`, `monotonic_counter`

**Current Implementation:**
- `runtime.py:execute_flow` only includes `actor_id`, `actor_type`, `session_id` in receipt
- Missing `provenance_signature`, `salt_version`, `monotonic_counter`

**Recommendation:** Update `execute_flow` to include all `ActorBlock` fields:
```python
actor={
    "actor_id": actor.actor_id,
    "actor_type": actor.actor_type,
    "session_id": actor.session_id,
    "provenance_signature": actor.provenance_signature,
    "salt_version": actor.salt_version,
    "monotonic_counter": actor.monotonic_counter,
}
```

---

### 6.2 Budget Exceeded Receipts

**PRD Requirement:** "Emit `budget_exceeded` receipt" (PRD §5.6)

**Current Implementation:**
- `RateLimiterService.check_budget` raises `BudgetExceededError`
- But `runtime.py:execute_flow` does not emit a receipt when budget is exceeded

**User's Intended Changes:**
- `runtime.py` has `_emit_budget_exceeded_receipt` method
- Called when `BudgetExceededError` is raised

**Status:** ❌ **MISSING** (unless user's changes are applied)

---

### 6.3 Dead Letter Receipts

**PRD Requirement:** "Nothing is dropped without an explicit dead_letter receipt" (PRD §7.1)

**Current Implementation:**
- `WALQueue.drain` logs failures but does not emit dead_letter receipts
- `OfflineCourier.drain` does not have `receipt_emitter` callback

**User's Intended Changes:**
- `WALQueue.drain` accepts `receipt_emitter` callback
- Failed drain attempts emit dead_letter receipts
- `runtime.py:drain_courier` passes `receipt_emitter` to courier

**Status:** ❌ **MISSING** (unless user's changes are applied)

---

### 6.4 PM-7 Merkle Root Capture

**PRD Requirement:** "Courier batches are tamper-evident via Merkle roots logged by PM-7" (PRD §9)

**Current Implementation:**
- `ReceiptService.write_receipt` calls PM-7 but does not capture Merkle root
- Merkle root is not stored in receipt annotations

**User's Intended Changes:**
- PM-7 indexing happens before fsync
- Merkle root and batch handle are captured and stored in receipt annotations

**Status:** ❌ **MISSING** (unless user's changes are applied)

---

## 7. TEST COVERAGE ANALYSIS

**Status:** ✅ **EXCELLENT**

**Analysis:**
- 70 tests covering all CCCS services
- Tests cover adapters, integration, E2E, WAL durability
- All tests passing

**Gaps:**
- No tests for Edge Agent → CCCS integration
- No tests for Cloud Services → CCCS integration
- No tests for 48h offline scenario (unless user's changes include it)

---

## 8. RECOMMENDATIONS

### Priority 1 (CRITICAL)

1. **Verify User's Changes Are Applied**
   - Ensure `IdentityService`, `RateLimiterService`, `PolicyRuntime` reflect user's intended changes
   - Verify WAL queuing and caching logic is implemented
   - Confirm offline-first operation is enabled

2. **Fix Initialization Order**
   - Reorder service initialization to match PRD: IAPS → CFFS → PREE → RLBGS → OTCS → RGES → SSDRS → ETFHF

3. **Complete Receipt Actor Fields**
   - Include `provenance_signature`, `salt_version`, `monotonic_counter` in receipt `actor` field

4. **Implement Edge Agent Integration**
   - Create Python bridge/FFI for Edge Agent to call CCCS
   - Or refactor Edge Agent to use CCCS via HTTP/gRPC

### Priority 2 (HIGH)

5. **Implement Cloud Services Integration**
   - Integrate CCCS runtime into Cloud Services FastAPI apps
   - Use CCCS for identity, policy, receipts

6. **Add Bootstrap API Version Negotiation**
   - Perform API version negotiation during bootstrap
   - Emit ETFHF entries for version mismatches

7. **Fix Bootstrap Poll Interval**
   - Change default `poll_interval` from 5.0s to 30.0s per PRD

### Priority 3 (MEDIUM)

8. **Consistent Error Wrapping**
   - Wrap all service exceptions in `execute_flow` with taxonomy normalization

9. **Add Integration Tests**
   - Test Edge Agent → CCCS integration
   - Test Cloud Services → CCCS integration

---

## 9. CONCLUSION

The CCCS module implementation is **architecturally sound** but has **critical inconsistencies** between the intended changes (as shown in user's attached files) and the actual codebase state. The user's changes implement offline-first operation, WAL queuing, and zero synchronous network calls, which are required by the PRD. However, these changes may not be reflected in the actual codebase.

**Key Findings:**
1. ✅ Type system is consistent
2. ✅ Service boundaries are well-defined
3. ✅ Test coverage is excellent
4. ❌ Code state mismatch (user's changes vs actual codebase)
5. ❌ Missing Edge Agent integration
6. ❌ Missing Cloud Services integration
7. ❌ Initialization order does not match PRD
8. ❌ Receipt actor fields are incomplete
9. ⚠️ Bootstrap sequence partially compliant

**Overall Grade:** ⚠️ **B- (Good foundation, but critical gaps need addressing)**

---

**Report Generated:** 2025-01-27  
**Analyst:** AI Architecture Review System  
**Next Review:** After user's changes are verified and applied

