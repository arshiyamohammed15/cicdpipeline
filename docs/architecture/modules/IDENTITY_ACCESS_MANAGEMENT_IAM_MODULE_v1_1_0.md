# IDENTITY & ACCESS MANAGEMENT (IAM) MODULE — COMPLETE SPECIFICATION (v1.1.0)

**Status:** Implementation-ready • **Updated:** 2025-11-13 06:21:08
**Reason for new version:** Resolve contradictions, add missing contracts, and make the module fully build/test ready.

---

## 0) Changelog (from v1.0.0)
- Aligned **Authentication response SLO** to **≤ 200 ms** and propagated across document.
- Unified **API endpoints**: added `/iam/v1/verify`, `/iam/v1/decision`, `/iam/v1/policies` to the registration header.
- Unified **event taxonomy** to: `authentication_attempt, access_granted, access_denied, privilege_escalation, role_change, policy_violation`.
- Unified **role vocabulary** to `admin, developer, viewer, ci_bot`. Added **Role Taxonomy Mapping** for organizational roles.
- Clarified **tokens**: JWT **signed** with **RS256 (RSA‑2048)**; no JWE by default; PII never embedded in tokens.
- Added **OpenAPI stubs** for core endpoints; introduced **error model**, **rate limits**, and **idempotency** rules.
- Specified **RBAC→ABAC precedence** and **JIT elevation** workflow; formalized **break‑glass** flow.
- Defined **session topology**, **cached‑credentials fallback**, and eviction/invalidation semantics.
- Completed **canonical IAM event & receipt schemas**; set risk score domain to **[0.0, 1.0]** with calibration rules.
- Added **policy store schema & versioning** requirements.
- Added **Transport Security Profile (TLS 1.3)**, **key management & rotation** (KID), and **secrets handling**.
- Completed **audit receipt signing/verification** integration with Evidence & Audit Ledger (Ed25519 receipts).
- Added **performance test traffic mix**, **overload/back‑pressure behaviors**, and **operational runbooks**.
- Declared **multi‑tenant model and quotas**.

---

## 1) Module Identity (Updated Registration)
```json
{
  "module_id": "M21",
  "name": "Identity & Access Governance",
  "version": "1.1.0",
  "description": "Authentication and authorization gatekeeper for ZeroUI ecosystem",
  "supported_events": [
    "authentication_attempt",
    "access_granted",
    "access_denied",
    "privilege_escalation",
    "role_change",
    "policy_violation"
  ],
  "policy_categories": ["security", "compliance"],
  "api_endpoints": {
    "health": "/iam/v1/health",
    "metrics": "/iam/v1/metrics",
    "config": "/iam/v1/config",
    "verify": "/iam/v1/verify",
    "decision": "/iam/v1/decision",
    "policies": "/iam/v1/policies"
  },
  "performance_requirements": {
    "authentication_response_ms_max": 200,
    "policy_evaluation_ms_max": 50,
    "access_decision_ms_max": 100,
    "token_validation_ms_max": 10,
    "max_memory_mb": 512
  }
}
```

---

## 2) Role Taxonomy (Unified) & Mapping
**Canonical RBAC roles:** `admin`, `developer`, `viewer`, `ci_bot`
**Organizational roles (examples):** `executive`, `lead`, `individual_contributor`, `ai_agent`

**Mapping (normative example; adjust via policy):**
| Org Role | Canonical Role |
|---|---|
| executive | admin |
| lead | developer |
| individual_contributor | developer |
| ai_agent | ci_bot |

Notes: Mapping is evaluated **before** authorization; final permissions are determined by RBAC→ABAC evaluation.

---

## 3) AuthN/AuthZ Semantics (Precedence & Flows)
### 3.1 Precedence
1. **Deny overrides** (explicit deny anywhere → deny).
2. **RBAC base** (role → base permissions).
3. **ABAC constraints** (time, device posture, location, risk score).
4. **Policy caps** (tenant/org caps, SoD checks).
5. **Break‑glass** (last resort; post‑facto review).

### 3.2 JIT Elevation Workflow
- **Request:** Subject → `POST /iam/v1/decision` with `action=request_elevation`, desired scope, duration.
- **Approval:** Approver(s) listed in policy; **dual‑approval** if scope == admin.
- **Issued:** Temporary grant with `granted_until` (ISO 8601) and **auto‑revocation** on expiry.
- **Receipt:** Signed decision receipt (Ed25519) written to Evidence & Audit Ledger.
- **Renewal:** Explicit re‑approval only; no silent renewal.

### 3.3 Break‑Glass
- **Trigger:** `crisis_mode=true` **and** policy `iam-break-glass` enabled.
- **Grant:** Minimal time‑boxed admin (default 4h).
- **Evidence:** Incident ID, requester/approver identity, justification text (non‑PII).
- **Review:** Mandatory post‑facto review within 24h; auto‑revoke if not approved.

---

## 4) Tokens, Sessions, & Fallback
- **Tokens:** JWT **signed** with **RS256 (RSA‑2048)**; 1h expiry; refresh at 55m. **No JWE** by default.
- **Claims:** Only minimal IDs and scopes; **no PII**; include `kid`, `iat`, `exp`, `aud`, `iss`, `sub`, `scope`.
- **Session topology:** Stateless JWT for APIs; optional server session index for revocation lists.
- **Revocation:** Maintain `jti` denylist with **TTL=exp**; propagate within 5s.
- **Cached‑credentials fallback (IdP outage):** limited scope token (read‑only) with `max_ttl=15m`; banner `degraded=true`; all writes require re‑auth on recovery.

---

## 5) Transport & Key Management
- **Transport Security Profile:** TLS 1.3 only; ciphersuites: AES‑256‑GCM‑SHA384 or CHACHA20‑POLY1305‑SHA256; min ECDHE P‑256.
- **mTLS** between internal services; **HSTS** on public edge.
- **Key Management:** All signing keys have **KID**; rotation every **90 days** or on suspicion; previous key retained in verify set for token lifetime + 24h; **no private keys in containers** (use OS/TPM/HSM).
- **Secrets handling:** Store in secure secret manager; rotate quarterly; access via short‑lived service identities.

---

## 6) API Contracts (OpenAPI Stubs)
> Machine‑readable OpenAPI (YAML) is embedded for the three core endpoints.

```yaml
openapi: 3.0.3
info:
  title: ZeroUI IAM Core
  version: 1.1.0
servers:
  - url: https://{tenant}.api.zeroui/iam/v1
paths:
  /verify:
    post:
      operationId: verifyIdentity
      summary: Verify identity/token
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [token]
              properties:
                token: { type: string }
      responses:
        '200':
          description: Token valid
          headers:
            X-Request-ID: { schema: { type: string } }
          content:
            application/json:
              schema:
                type: object
                required: [sub, scope, valid_until]
                properties:
                  sub: { type: string }
                  scope: { type: array, items: { type: string } }
                  valid_until: { type: string, format: date-time }
        '401': { $ref: '#/components/responses/AuthFailed' }
        '429': { $ref: '#/components/responses/RateLimited' }
        '5XX': { $ref: '#/components/responses/ServerError' }
  /decision:
    post:
      operationId: accessDecision
      summary: Evaluate an access decision or JIT elevation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DecisionRequest'
      responses:
        '200':
          description: Decision rendered
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DecisionResponse'
        '400': { $ref: '#/components/responses/BadRequest' }
        '401': { $ref: '#/components/responses/AuthFailed' }
        '403': { $ref: '#/components/responses/Forbidden' }
        '409': { $ref: '#/components/responses/Conflict' }
        '429': { $ref: '#/components/responses/RateLimited' }
        '5XX': { $ref: '#/components/responses/ServerError' }
  /policies:
    put:
      operationId: upsertPolicies
      summary: Upsert policy bundle (versioned)
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PolicyBundle'
      responses:
        '202':
          description: Accepted; policy release queued
        '400': { $ref: '#/components/responses/BadRequest' }
        '401': { $ref: '#/components/responses/AuthFailed' }
        '409': { $ref: '#/components/responses/Conflict' }
components:
  responses:
    BadRequest:
      description: Invalid input
      content:
        application/json:
          schema: { $ref: '#/components/schemas/Error' }
    AuthFailed:
      description: Authentication failed
      content:
        application/json:
          schema: { $ref: '#/components/schemas/Error' }
    Forbidden:
      description: Insufficient privileges
      content:
        application/json:
          schema: { $ref: '#/components/schemas/Error' }
    Conflict:
      description: Resource state conflict
      content:
        application/json:
          schema: { $ref: '#/components/schemas/Error' }
    RateLimited:
      description: Rate limit exceeded
      headers:
        Retry-After: { schema: { type: integer, format: int32 } }
      content:
        application/json:
          schema: { $ref: '#/components/schemas/Error' }
    ServerError:
      description: Internal server error
      content:
        application/json:
          schema: { $ref: '#/components/schemas/Error' }
  schemas:
    Error:
      type: object
      required: [error_code, message]
      properties:
        error_code:
          type: string
          enum: [BAD_REQUEST, AUTH_FAILED, FORBIDDEN, CONFLICT, RATE_LIMITED, SERVER_ERROR]
        message: { type: string }
        correlation_id: { type: string }
        retriable: { type: boolean }
    DecisionRequest:
      type: object
      required: [subject, action, resource]
      properties:
        subject:
          type: object
          required: [sub, roles]
          properties:
            sub: { type: string }
            roles: { type: array, items: { type: string, enum: [admin, developer, viewer, ci_bot] } }
            attributes:
              type: object
              additionalProperties: true
        action: { type: string }
        resource: { type: string }
        context:
          type: object
          properties:
            time: { type: string, format: date-time }
            device_posture: { type: string, enum: [secure, unknown, insecure] }
            location: { type: string }
            risk_score: { type: number, minimum: 0.0, maximum: 1.0 }
        elevation:
          type: object
          properties:
            request: { type: boolean }
            scope: { type: array, items: { type: string } }
            duration: { type: string }
    DecisionResponse:
      type: object
      required: [decision, reason, receipt_id]
      properties:
        decision: { type: string, enum: [ALLOW, DENY, ELEVATION_REQUIRED, ELEVATION_GRANTED] }
        reason: { type: string }
        expires_at: { type: string, format: date-time }
        receipt_id: { type: string }
    PolicyBundle:
      type: object
      required: [bundle_id, version, policies]
      properties:
        bundle_id: { type: string }
        version: { type: string }
        effective_from: { type: string, format: date-time }
        policies:
          type: array
          items:
            type: object
            required: [id, rules]
            properties:
              id: { type: string }
              rules: { type: array, items: { type: object } }
              status: { type: string, enum: [draft, released, deprecated] }
```
**Error Model:** All responses include `X-Request-ID` header; clients must echo `X-Idempotency-Key` for write‑like operations.
**Rate limits:** Default **50 RPS/client**, burst **200** for 10s; 429 with `Retry-After`. Tenant/global limits configurable per policy.
**Idempotency:** Required for `/policies` via `X-Idempotency-Key`; server ensures single application per key within 24h window.

---

## 7) Canonical Events & Receipts
**Event names:** `authentication_attempt, access_granted, access_denied, privilege_escalation, role_change, policy_violation`

**Receipt (IAM extension):**
```json
{
  "receipt_id": "uuid",
  "ts": "2025-11-13T00:00:00Z",
  "module": "IAM",
  "event": "access_granted",
  "iam_context": {
    "user_id": "uuid",
    "auth_method": "sso|mfa|api_key|break_glass",
    "access_level": "admin|developer|viewer|ci_bot",
    "permissions_granted": ["read", "write"],
    "risk_score": 0.62
  },
  "decision": "ALLOW",
  "policy_id": "iam-dev-access",
  "evaluator": "rbac_abac_v1",
  "evidence": {"jti": "uuid", "kid": "key-2025q4"},
  "sig": "eddsa-ed25519-base64"
}
```
- **Risk score domain:** `[0.0, 1.0]`; calibrated on false‑positive budget < 1%.
- **Signing:** Receipts are **Ed25519‑signed**; verification public keys distributed via Evidence & Audit Ledger trust store.

---

## 8) Policy Store (Schema & Versioning)
```json
{
  "policy_id": "iam-dev-access",
  "version": "2025.11.0",
  "created_at": "2025-11-13T05:00:00Z",
  "effective_from": "2025-11-14T00:00:00Z",
  "status": "released",
  "scope": ["tenant:acme"],
  "rbac": {"roles": ["developer"], "permissions": ["read", "write", "execute"]},
  "abac": {"constraints": [{"mfa_required": true}, {"time_window": "06:00-22:00"}]},
  "sod": [ {"mutually_exclusive": ["deployer", "approver"]} ],
  "approvals": [ {"role": "admin", "count": 1} ],
  "audit": {"created_by": "uuid", "change_reason": "Quarterly review"}
}
```
- **Releases:** Immutable release artifacts with SHA‑256 `snapshot_id`; prior versions retained; deprecation requires explicit end‑of‑life date.

---

## 9) Performance, Tests & Overload Behavior
**Throughput:** Auth 500/s; Policy 1000/s; Token 2000/s.
**Traffic mix for tests:** 70% verify, 25% decision, 5% policies.
**Load:** 2× expected peak; **Stress:** 5×; **Endurance:** 72h.
**Overload:** Prefer **shed new elevation / policy writes** first; preserve verify/decision read‑paths. Return `503` with `Retry-After` and emit `OVERLOAD` event.

---

## 10) Operations & Runbooks
- **Key rotation:** rotate signing keys (RS256) every 90d; publish new KID; stage dual‑sign verify window.
- **Revocation drill:** monthly test of jti denylist propagation.
- **Break‑glass drill:** quarterly, with evidence review.
- **Backup/restore:** policy store hourly incremental + daily full; RPO 15m; RTO 1h (unchanged).
- **Multi‑tenant model:** tenant‑scoped keys, rate limits, quotas (users 50k, policies 5k, concurrent sessions 10k).

---

## 11) Dependencies (unchanged, clarified)
- **M32 Identity & Trust Plane** (device/service identities, mTLS).
- **M27 Evidence & Audit Ledger** (receipt store/signing trust).
- **M29 Data & Memory Plane** (policy/index storage, caches).

---

## 12) Compliance Mapping (evidence hooks)
- **SOC 2** CC6.x: decision receipts, access reviews, SoD checks, jti denylist evidence.
- **GDPR 25/32:** data minimization (no PII in tokens), transport profile, key rotation logs.
- **HIPAA:** access control events + immutable audit with rapid retrieval.

---

## 13) MMM Framework Integration
- **Mirror:** expose per‑actor access history metrics.
- **Mentor:** guided JIT elevation with reason templates.
- **Multiplier:** org roll‑ups of policy hygiene and SoD adherence.
