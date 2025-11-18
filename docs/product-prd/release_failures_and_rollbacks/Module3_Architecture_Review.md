# ZeroUI — Module 3 (Release Failures & Rollbacks) Architecture — Technical Review (V1.1, Derived)

> **Source of truth:** `ZeroUI_Module3_Architecture_V1_1.docx` (V1.1). This review restates, organises, and highlights verifiable details from the document only. It flags inconsistencies explicitly and avoids speculation.

---

## 1) Scope and Intent (verbatim-derived)

- **Goal:** Catch risky changes early and make rollbacks rare and safe; do it inside VS Code via small nudges/one‑click actions; every decision is policy‑driven and written as a signed receipt.
- **In‑scope:** VS Code Extension (**presentation only**), **Edge Agent** on the laptop (logic/evaluations/actions/receipts), minimal backend (**Policy Registry** and **Receipt Mirror/Verifier**), flows for pre‑submit risk clarity, release gates, canary/load checks, DB safety, observability gating, freeze windows, overrides, receipts.
- **Out‑of‑scope:** non‑Module‑specific dashboards, external ROI reporting, non‑critical admin consoles.

> **Editorial inconsistency to fix:** The document title names **Module 3** (Release Failures & Rollbacks) but several sections and headings say “**Module 1**”. Treat this as a naming error in the source that should be corrected in the next revision.

---

## 2) System Overview and Principles

- **Three places working together:**
  1) **Laptop** (Edge Agent + Extension): evaluates, runs safe actions, writes receipts.
  2) **Client Cloud:** hosts tenant policy snapshots, optionally mirrors receipts.
  3) **Product Cloud:** publishes Gold‑Standard policy templates (GSMD) tenants adopt.
- **Key principles:** policy‑driven (no hard‑coded thresholds/messages), **extension = presentation only** (renders from last receipt), **deterministic** (same inputs + policy → same decision), **privacy‑first** (no raw code leaves the laptop; evidence is links only), **actor parity** (humans and AI agents follow the same rules).

---

## 3) Component Breakdown

### 3.1 VS Code Extension (presentation only)
- **Surfaces:** Status Bar Pill, Problems Panel, Zero‑UI Decision Panel, Evidence Drawer, Toast, Receipt Viewer.
- **Responsibilities:** only render from receipts; offer ≤3 actions per decision; send commands to the Agent; **never compute risk**.
- **IPC:** local HTTP/IPC to the Edge Agent.

### 3.2 Edge Agent (logic & receipts)
- **Services (logical):**
  **Signal Collector** (diff stats, coverage deltas, flaky tests, migration patterns, OTel checks);
  **Policy Cache** (pulls signed policy snapshot; atomic swap);
  **Evaluator** (rules → decision, reasons[], actions[]);
  **Action Runner** (safe actions: generate test stub, wrap with flag, canary probe, etc.);
  **Receipt Writer** (append‑only JSONL with fsync; rotation & recovery);
  **Exporter (optional)** (mirror receipts when policy allows).

### 3.3 Backend (minimal for Module 3)
- **Policy Registry:** signed/immutable snapshots, version history, changelog.
- **Receipt Mirror & Verifier:** schema + signature validation; **evidence index of links only**.

---

## 4) Data Contracts (extracts)

> The doc labels these as *illustrative minima*; the policy in effect drives exact fields.

### 4.1 Decision: Request → Response (Extension ↔ Agent)
**Request (Extension → Agent)**
```json
{
  "context": {
    "event": "pre_submit|pr_opened|manual_check",
    "actor_id": "...",
    "actor_type": "human|ai_agent",
    "repo_id": "...",
    "branch": "..."
  }
}
```
**Response (Agent → Extension)**
```json
{
  "decision_id": "uuid",
  "decision": "PASS|WARN|SOFT_BLOCK|HARD_BLOCK",
  "policy_id": "POL-...",
  "policy_snapshot_hash": "sha256:...",
  "why": ["Large diff", "Missing rollback plan"],
  "actions": [
    {"id":"add_test_stub","label":"Add test stub","priv":"non_priv"},
    {"id":"wrap_with_flag","label":"Wrap with feature flag","priv":"requires_approval"}
  ],
  "evidence_links": ["time-scoped://..."],
  "receipt_id": "rcpt_..."
}
```

### 4.2 Decision Receipt (append‑only JSONL; one object per line)
```json
{
  "receipt_id": "rcpt_...",
  "time_utc": "2025-10-23T06:40:00Z",
  "monotonic_ms": 123456789,
  "actor": {"id":"...","type":"human|ai_agent"},
  "repo": {"id":"...","branch":"..."},
  "policy": {"id":"POL-...","snapshot_hash":"sha256:...","version_ids":["v1.2","m1.4"]},
  "input": {"files": 9, "loc": 612, "coverage_delta": -3.2, "db_ops": ["drop"], "otel_check": "missing"},
  "decision": "SOFT_BLOCK",
  "reasons": ["LOC>limit","Rollback plan missing"],
  "actions": [{"id":"split_change","state":"suggested"}],
  "evidence": [{"type":"trace","handle":"link://...","redacted":true}],
  "signature": {"alg":"ed25519","kid":"key1","sig":"base64..."}
}
```

### 4.3 Feedback Receipt (one pattern per decision)
```json
{
  "receipt_id": "rcpt_feedback_...",
  "decision_id": "...",
  "pattern_id": "FB-03-OUTCOME|FB-02-TIME|FB-01-MIN",
  "choice": "Worked|Partly worked|Didn't work",
  "required_tag_if_negative": "insufficient_permissions|policy_wrong|too_noisy|...",
  "policy_snapshot_hash": "sha256:..."
}
```

### 4.4 Evidence Link (link‑only)
```json
{
  "type": "trace|log|metric|canary|url",
  "scheme": "otel://|log://|metric://|canary://|url",
  "handle": "time-scoped://...",
  "ttl_ms": 600000,
  "created_utc": "2025-10-23T06:40:00Z",
  "scope": "tenant|local",
  "on_expiry": "show_hint|silent",
  "redacted": true
}
```

---

## 5) Policy & Evaluation Model (Module 3)

- **Rule families (examples):**
  R_OVERSIZE (files, LOC, branch age) → decision bands;
  R_DB_SAFE_CHANGE → expand/migrate/contract checks;
  R_OTEL_MIN → minimal tracing/logging presence;
  R_CANARY_SCORE → weights for p95/error%/saturation; score bands;
  R_FREEZE_WINDOW → UTC ranges + exceptions;
  R_FLAG_GUARD → feature‑flag metadata (owner, kill path, expiry).
- **Evaluation loop (Agent):** load signed snapshot (cached; atomic swap) → collect signals (diff, tests, env, DB ops, OTel, optional canary) → evaluate rules → write receipt (fsync) → return response.
- **Heavy checks (canary/load smoke):** on‑demand only; show progress; never block the UI thread.

---

## 6) Core Flows (Module 3)

1. **Pre‑Submit Risk Clarity** — save → `/evaluate` → receipt → Status Pill → Decision Panel (≤3 actions) → optional action → new receipt.
2. **Release Gate: Rollback Plan Required** — PR template fields (rollout/rollback) checked; missing → Problems Panel + SOFT_BLOCK; quick‑fill → PASS (+ receipt).
3. **Canary / Load Smoke (on demand)** — run 30–60s probe; score vs policy; below limit → BLOCK with reasons + links; evidence links are **time‑scoped** (no raw payload).
4. **DB Safe Change** — scan migrations; flag DROP/RENAME without expand; suggest safe template; generating patch writes a receipt.
5. **Observability Gating** — check minimal OTel setup + exemplar linkage; missing → WARN/BLOCK + paste‑ready snippet.
6. **Freeze Windows & Overrides** — within freeze window, risky merges → HARD_BLOCK; break‑glass override is time‑boxed with dual approval; receipt logs scope/expiry.
7. **Offline/Degraded** — if policy unavailable: warn‑only; privileged actions disabled; receipt records degrade.

---

## 7) Interfaces (Edge Agent)

- **Local endpoints:**
  `POST /v1/evaluate` (decision response) • `POST /v1/actions/{action_id}` (run action → receipt_id) • `GET /v1/receipts/last?context=pre_submit` (last decision receipt) • `GET /v1/policy/current` (policy metadata) • `POST /v1/feedback` (feedback receipt).
- **Backend endpoints (minimal):**
  `GET /v1/policy/current` (signed snapshot payload) • `POST /v1/receipts/ingest` (optional mirror; schema + signature verified).

> The acceptance checklist also states the **interfaces specify error/auth/envelope/idempotency** and support **progress/cancel** for long‑running actions. Treat these as architectural requirements tied to the endpoints above.

---

## 8) Local Storage Layout (Laptop)

```
%USERPROFILE%\.zeroui  policy\current.snapshot.json
  receipts\{repo_id}\{yyyy}\{mm}\{dd}
eceipts.jsonl
  trust\public_keys.json
  logsgent.log
```
- **Rotation:** size‑based or daily; partial‑line recovery on startup.

---

## 9) Performance & Reliability SLOs

- Pre‑submit evaluation **p95 ≤ 500 ms** (with cached policy).
- Receipt write **p95 ≤ 20 ms** (fsync).
- Heavy probes **show progress** and do **not** block the UI thread.
- **≥99.9%** valid receipts (schema + signature).

---

## 10) Security & Privacy

- **No source code egress**; evidence is links only, **time‑scoped** and **redacted**.
- **Signed policy snapshots**; trusted keys in local `trust/`.
- **Receipts signed**; mirror only if tenant policy allows.
- **Privileged actions** require approval (dual‑channel) and are rate‑limited.

---

## 11) Observability (of the product itself)

- **Metrics (Agent):** decision latency, policy age, action success %, receipt fsync time, probe duration.
- **Logs:** structured JSON (no secrets); correlate via `decision_id` / `receipt_id`.
- **Health:** liveness/readiness for the local service; self‑check writes a receipt.

---

## 12) Testing & Validation

- **Unit:** evaluator rules; parsers (DB, OTel, diff); action runners.
- **Contract:** JSON Schemas for decisions/receipts/feedback; OpenAPI + Spectral for APIs.
- **Functional:** oversize; missing rollback plan; freeze windows; OTel missing; canary decision bands; degraded modes.
- **E2E:** save→evaluate→receipt→render; action→receipt→toast; long‑running (progress/cancel).
- **Mapping matrix (examples):**
  - evaluate happy path → decision receipt present; envelope `ok=true`
  - stale policy → degraded (`degrade_reason=policy_stale`); privileged action → HTTP 409
  - canary timeout → HTTP 503; terminal receipt `action_state=timed_out`
  - evidence expired → UI hint + feedback receipt recorded

---

## 13) Deployment & Packaging

- **Edge Agent:** Python 3.11, packaged for Windows (PyInstaller EXE); auto‑update channel.
- **Extension:** VSIX; reads only local Agent endpoints.
- **Backend:** minimal FastAPI per tenant (policy/ingest).

---

## 14) Versioning & Compatibility

- **Policy snapshots** are immutable; the Extension renders `policy_id` + `policy_snapshot_hash`.
- **Receipt schema** uses semver; mirror accepts older major for a bounded window before enforcing current.
- **Breaking changes:** agent keeps write‑new/read‑old adapter for ≥1 release; mirror enforces a compatibility window.

---

## 15) Risks & Mitigations (documented)

- **False positives** → feedback receipts + policy simulator before enforce.
- **Policy staleness** → warn‑only degrade; surface policy age in UI.
- **Long probes** → on‑demand with progress; allow cancel.
- **Local corruption** → rotation, partial‑line recovery, integrity checks.

---

## 16) Acceptance Checklist (from the doc)

- Extension never computes risk; renders from last receipt.
- ≤3 actions per decision; safety badges; privileged actions disabled in degraded.
- All outputs include `policy_id` + `policy_snapshot_hash`.
- Receipts append‑only, signed, fsync; schema validated in CI; rotate @10MB/daily; partial‑line recovery.
- Interfaces specify error/auth/envelope/idempotency; long‑running actions support progress/cancel.
- Oversize, rollback‑plan, OTel, DB‑safe, freeze, canary flows work end‑to‑end.
- Offline: warn‑only; receipts still written.
- Observability metrics include names/units/dimensions.
- Key rotation/revocation procedures documented; degrade on revoke.

---

## 17) Review Notes (facts-only)

1. **Naming mismatch:** The doc is titled for **Module 3**, yet multiple section headers say **Module 1**. Mark this as a editorial inconsistency to correct in the next revision.
2. **Interfaces detail level:** The acceptance checklist references error/auth/envelope/idempotency and long‑running progress/cancel, which the endpoint list implies. If there is a separate Error/Auth section, link it explicitly from the Interfaces chapter in the next revision.
3. **Schema extracts:** The appendix includes minimal JSON schema extracts for decision, receipt, and feedback. Keep them in repo contracts and validate in CI to uphold the 99.9% valid‑receipt SLO.

---

**End of review.**
