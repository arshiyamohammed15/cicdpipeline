# PM-2 — Cross-Cutting Concern Services (CCCS)
## Product Requirements Document  
**Version:** 2.0  
**Status:** Definition of Ready = PASS

---

# 1. SUMMARY
Cross-Cutting Concern Services (CCCS) is not a standalone feature module.  
It is the runtime layer inside the Edge Agent and Backend that provides a single, unified SDK for functionalities owned by EPC modules, PM modules, and CCP planes.  
CCCS never re-implements logic. It only provides a runtime façade.

---

# 2. SCOPE
CCCS exposes **8 runtime façade services**:

- **Identity & Actor Provenance (IAPS)**  
- **Policy Runtime & Evaluation Engine (PREE)**  
- **Configuration & Feature Flags (CFFS)**  
- **Receipt Generation (RGES)**  
- **Secure Redaction (SSDRS)**  
- **Rate Limiter & Budget Guard (RLBGS)**  
- **Observability & Trace (OTCS)**  
- **Error Taxonomy Framework (ETFHF)**  

### Mapping to actual owner modules/planes:
| CCCS Service | Owner |
|--------------|--------|
| IAPS | EPC-1 + CCP-1 |
| PREE / CFFS | EPC-3 + EPC-10 + CCP-2 |
| RGES | PM-7 + CCP-3 |
| SSDRS | EPC-2 + CCP-6 |
| RLBGS | EPC-13 |
| OTCS | EPC-4 + EPC-5 + CCP-4 |
| ETFHF | EPC-5 + CCP-4 |

---

# 3. NON-SCOPE
CCCS must **NOT**:
- Implement IAM  
- Store policies or configs  
- Implement budgeting logic  
- Own audit/evidence stores  
- Own observability collectors  
- Store secrets or PII  
- Define new redaction rules  
- Maintain identity kernels  
- Implement indexing or retention  

---

# 4. ARCHITECTURE ROLE
**Functional Modules → CCCS Runtime SDK → EPC/PM/CCP Owners**

CCCS runs inside:
- **Edge Agent** (offline-first)
- **Backend** (Tenant + Product Cloud)

---

# 5. FUNCTIONAL REQUIREMENTS

## 5.1 Identity & Actor Provenance (IAPS)
**Purpose:** Provide standardized actor block.  
**Responsibilities:**
- Collect local metadata  
- Normalize identity with EPC-1  
- Produce standard actor block  

**Must NOT:** Implement IAM, manage keys, store identity.

---

## 5.2 Policy Runtime & Evaluation Engine (PREE)
**Purpose:** Deterministic policy evaluation.  
**Responsibilities:**
- Load signed GSMD snapshots  
- Validate signature  
- Delegate evaluation to EPC-3  

**Must NOT:** Create rules, store policies, hardcode thresholds.

---

## 5.3 Configuration & Feature Flags (CFFS)
**Purpose:** Deterministic config resolution.  
**Responsibilities:**
- Merge local, tenant, product configs  
- Unified lookup APIs  

**Must NOT:** Store configs or rollout logic.

---

## 5.4 Receipt Generation (RGES)
**Purpose:** Generate signed JSONL receipts.  
**Responsibilities:**
- Build receipt  
- Add actor + trace  
- Sign and fsync  
- Send to PM-7 for indexing  

**Must NOT:** Store or index receipts.

---

## 5.5 Secure Redaction (SSDRS)
**Purpose:** Enforce redaction and metadata-only output.  
**Responsibilities:**
- Apply EPC-2 rules  
- Remove PII, secrets, code  

**Must NOT:** Define redaction rules.

---

## 5.6 Rate Limiter & Budget Guard (RLBGS)
**Purpose:** Prevent overspend/runaway compute.  
**Responsibilities:**
- Token-bucket gate  
- Consult EPC-13  
- Emit `budget_exceeded` receipts  

**Must NOT:** Define budgets.

---

## 5.7 Observability & Trace (OTCS)
**Purpose:** Unified tracing and logging.  
**Responsibilities:**
- Generate trace_id/span_id  
- Structured logs  
- Attach trace to receipts  

**Must NOT:** Implement collectors or alerts.

---

## 5.8 Error Taxonomy Framework (ETFHF)
**Purpose:** Normalize errors.  
**Responsibilities:**
- Map exceptions → canonical codes  

**Must NOT:** Define new categories.

---

## 5.9 Initialization & Bootstrap
**Purpose:** Define deterministic startup sequence and dependency handling for Edge Agent and Backend runtimes.  
**Requirements:**
- Initialization order is fixed: IAPS → CFFS → PREE → RLBGS → OTCS → RGES → SSDRS → ETFHF. Each stage must report readiness before progressing.
- CCCS loads only after EPC-1 (identity), EPC-3 (policy/config), and EPC-13 (budget) service stubs are present in the process.
- **Edge Agent (offline-first):** May enter degraded mode if upstream EPC services are unreachable; actions that rely on missing dependencies must fail closed with canonical error codes.
- **Backend:** Startup blocks until all EPC dependencies respond healthy; degraded startup is not permitted in multi-tenant planes.
- Bootstrap creates WAL-backed queues before any façade service becomes available to ensure durable capture of receipts and budgets.
- Dependency health checks are re-run every 30 seconds during bootstrap; failure to reach ready state within 5 minutes triggers `cccs_bootstrap_timeout` error taxonomy.

---

# 6. CONTRACTS (FAÇADE APIS)

### Actor Block
```
actor: {
  actor_id: string,
  actor_type: string,
  session_id: string,
  provenance_signature: string
}
```

### Identity Resolution (IAPS)
```
resolve_actor(context) → {
  actor,
  provenance_proof,
  normalization_version,
  warnings[]
}
```
- `context` includes device_id, tenant_id, runtime clock.
- Fails closed with `actor_unavailable` error taxonomy.

### Policy Evaluation
```
evaluate_policy(module_id, inputs) → {
  decision,
  rationale,
  policy_version_ids,
  policy_snapshot_hash
}
```

### Configuration Resolution (CFFS)
```
get_config(key, scope, overrides?) → {
  value,
  source_layers,
  config_snapshot_hash
}
```
- Deterministic merge order: local → tenant → product.
- Emits `config_gap` warning if key missing across all layers.

### Receipt Generation
```
write_receipt(input, result, annotations?) → {
  receipt_id,
  courier_batch_id,
  fsync_offset
}
```
- Mutations limited to metadata enrichment hooks: `before_sign`, `before_flush`.
- Returns courier batch reference for offline drain visibility.
- **Receipt schema compliance:** All receipts MUST conform to the canonical schema enumerated in `docs/architecture/receipt-schema-cross-reference.md`, inheriting the required fields (receipt_id, gate_id, policy_version_ids, snapshot_hash, timestamp_utc, timestamp_monotonic_ms, inputs, decision.{status,rationale,badges}, result, actor, degraded, signature). Deviations are disallowed.

### Rate Limiting
```
check_budget(action_id, cost) → { allowed, reason }
```

### Observability
```
start_span(name)
log_info(message)
log_error(message)
```

### Secure Redaction (SSDRS)
```
apply_redaction(payload, policy_hint) → {
  redacted_payload,
  removed_fields[],
  rule_version
}
```
- Never mutates source payload; returns detached copy.
- Raises `redaction_blocked` if EPC-2 ruleset missing.

### Error Taxonomy (ETFHF)
```
normalize_error(error, context) → {
  canonical_code,
  severity,
  retryable,
  user_message,
  debug_id
}
```
- Canonical codes sourced from EPC-5 manifests; CCCS only maps.

### API Versioning
- CCCS façade APIs follow semantic versioning (`MAJOR.MINOR.PATCH`).
- Backward-compatible additions bump the MINOR version; bug fixes bump PATCH.
- Breaking changes require a MAJOR version update and dual-publish period of ≥2 releases.
- Version negotiation occurs during bootstrap; mismatches emit `version_mismatch` via ETFHF.

---

# 7. END-TO-END FLOW
1. Resolve actor (IAPS)  
2. Merge config (CFFS)  
3. Evaluate policy (PREE)  
4. Check budgets (RLBGS)  
5. Generate trace (OTCS)  
6. Build & sign receipt (RGES)  
7. Apply redaction (SSDRS)  
8. PM-7 indexes  

## 7.1 Offline & Failure Handling
- **Durable queues:** Receipts, budget events, and policy snapshots land in WAL-backed queues per runtime. Nothing is dropped without an explicit `dead_letter` receipt.
- **Retry windows:** Edge Agent retries EPC handoffs for 72h with exponential backoff (max backoff 5 min). Backend retries for 6h with max 1 min backoff before paging operations.
- **Degraded behaviours:**  
  - Missing GSMD snapshot → block action with `policy_unavailable`.  
  - PM-7 courier unavailable → continue local fsync and mark courier batches `pending_sync`.  
  - Redaction rule drift → emit `redaction_blocked` and halt response emission.  
  - Budget service unreachable → default deny to prevent overspend.  
- **State reconciliation:** Courier batches carry monotonic sequence numbers; Backend dedupes receipts and budgets once connectivity returns.

---

# 8. PERFORMANCE REQUIREMENTS
- Policy eval <150ms  
- Receipt overhead <5ms  
- Config merge <3ms  
- Rate limit eval <5ms  
- Zero synchronous network calls on critical path (Edge + Backend)  
- Asynchronous courier drains must clear within 30s once connectivity resumes  

---

# 9. SECURITY REQUIREMENTS
- Sign all receipts using EPC-1 managed Ed25519 keys; private keys never leave HSMs.  
- Redaction mandatory before any payload exits CCCS memory boundary.  
- No secrets/PII stored; transient buffers zeroed immediately after use.  
- No network policy evaluation; GSMD snapshots validated offline via EPC-3 signature chain.  
- Identity hashed via EPC-1 salt; salts rotate every 24h and versions recorded in receipts.  
- Courier batches are tamper-evident via Merkle roots logged by PM-7.  
- Provenance proofs attach monotonic counters to defeat replay and downgrade attempts.  

---

# 10. TEST PLAN

## 10.1 Unit Tests
- Identity deterministic (stable actor_id given identical inputs)  
- Identity failure handling (missing EPC-1 metadata, clock skew)  
- Policy signature validation (valid/invalid/corrupted snapshot)  
- Policy denial determinism under concurrent requests  
- Config merge precedence plus `config_gap` warning emission  
- Config checksum mismatch handling  
- Receipt fsync + signature, courier sequence continuity  
- Receipt mutation hook ordering guarantees  
- Redaction correctness and blocked rule scenarios  
- Rate limiting behaviour and deny-by-default when EPC-13 unavailable  
- Trace correlation plus span lineage across retries  
- Error taxonomy mapping including unknown exception fallback

## 10.2 Integration Tests
- Policy → Receipt end-to-end with offline courier replay  
- Budget enforcement for burst + sustained traffic, including deny fallback  
- Trace propagation with concurrent spans and receipt linking  
- Redaction + receipt + PM-7 courier replay  
- Config override propagation from tenant to Edge Agent

## 10.3 E2E Tests
- FM → CCCS → EPC/PM/CCP → Deterministic result  
- Edge Agent offline 48h → reconnect → zero data loss  
- Security attestation: forged receipt, replay attempt, tamper detection

---

# 11. DIRECTORY STRUCTURE
```
shared_libs/cccs/
    identity/
    policy/
    config/
    receipts/
    redaction/
    ratelimit/
    observability/
    errors/
```

---

# 12. ACCEPTANCE CRITERIA
- No duplication with EPC/PM/CCP  
- All tests pass  
- Receipts schema-valid  
- Deterministic offline runtime  
- Mandatory redaction  
- No hardcoded rules  

**DEFINITION OF READY = PASS**
