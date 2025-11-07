
Wire-On / Wire-Off Module Framework — Version 2.1
Date: 2025-11-07

0) Change Log (Surgical Redlines Incorporated)
• Defined grammar for module_id; mandated SemVer for version; formalised requires comparator grammar.
• Marked entrypoints init/start/stop/health as REQUIRED with stable Ok/Err contracts.
• Standardised health payload and gating rules for ok/degraded/fail.
• Enforced 1:1 mapping between provides and Capabilities Registry entries when module is ON.
• Extended Wiring Snapshot: signing_kid, canonical JSON signing, prev_snapshot_id, revision (anti-replay).
• Added policy compatibility check with policy_version_ids.
• Hardened edges: existence validation, topic charset/length, rejection of edges to OFF modules, duplicate prevention.
• Guard precedence clarified: require_quiescence and drain_window_ms; introduced drain_policy (discard|persist_to_dlq).
• Receipts now include prev_state, new_state, duration_ms, orchestrator_id, error_code, error_detail; specified timestamp format.
• Apply lock (concurrency=1), explicit 409 for concurrent applies; cycle detection with error_code.
• Crash safety: atomic current_state.json, plan_id checkpoints, resume/rollback rules.
• Null Adapter contract defined (capability_unavailable) for OFF modules; isolation guaranteed.
• Access control for apply and read-only Capabilities Registry API with ETag/TTL; no secrets/PII in snapshots/receipts.

1) Precise Definitions
• Module: A deployable unit implementing a fixed contract (ID, version, capabilities, inputs/outputs, lifecycle hooks).
• Wire-On: Orchestrator connects module inputs/outputs, starts it, and exposes capabilities to the system.
• Wire-Off: Orchestrator atomically detaches the module, stops it, removes capabilities from the registry.
• Wiring Snapshot: A signed, append-only JSON document declaring module states and edges; includes anti-replay fields.

2) Contracts

2.1) Module Manifest (Normative)
Required keys:
- module_id: "M" + 2 digits + "." + lower-snake-case name; charset [a-z0-9_.]; max length 64; globally unique; case-sensitive.
- version: SemVer X.Y.Z (semantic ordering).
- provides: array of capability identifiers (strings). Each provided capability MUST appear in the Capabilities Registry when module=ON.
- requires: array of service/capability constraints using comparator grammar (see 2.1.1).
- subscriptions: array of topics consumed.
- publications: array of topics produced.
- entrypoints: REQUIRED object with keys {init, start, stop, health}.
- health: REQUIRED object defining probe_kind and probe_target.

2.1.1) requires Comparator Grammar (EBNF)
requirement := name [ "@" comparator version ]
name       := 1*( ALNUM | "_" | "." | "-" )
comparator := ">=" | "<=" | "=" | ">" | "<"
version    := SemVer (X.Y.Z)

2.1.2) Entrypoints Contracts (Stable)
- init(context)  -> Ok | Err {code, message}
- start(context) -> Ok | Err {code, message}
- stop(context)  -> Ok | Err {code, message}
- health()       -> { "status": "ok" | "degraded" | "fail", "details": { … } }

2.1.3) Health Gating
- Wire-on proceeds when status=ok.
- If status=degraded, proceed only when guards.allow_degraded_on=true.
- If status=fail, wire-on MUST rollback.

2.1.4) Topics and Capabilities
- Topics charset: [a-z0-9._-], max length 64.
- Capability identifiers follow name grammar above.

Example Manifest (updated):
{
  "module_id": "M01.release_failures_and_rollbacks",
  "version": "1.2.3",
  "provides": ["risk_gate", "receipts_sink"],
  "requires": ["event_bus.core@>=1.0", "policy.registry@>=1.0"],
  "subscriptions": ["events.pr.opened", "events.build.finished"],
  "publications": ["risk.decisions"],
  "entrypoints": { "init": "module.init", "start": "module.start", "stop": "module.stop", "health": "module.health" },
  "health": { "probe_kind": "http|ipc|func", "probe_target": "127.0.0.1:7011/health" }
}

2.2) Wiring Snapshot (Policy-as-Code; Signed; Anti-Replay)
Normative rules:
- snapshot_id: SHA-256 over canonical JSON (sorted keys, UTF-8, LF).
- signing_kid: key identifier of the signer.
- signature: Ed25519 signature over canonical JSON.
- prev_snapshot_id: snapshot_id of the last successfully applied snapshot.
- revision: monotonic integer incremented by 1 each apply.
- policy_version_ids: orchestrator MUST refuse apply if any ON module requires incompatible policy versions.
- modules: mapping of module_id -> {"state": "on|off|dry_run"}
- edges: validated list (see 2.2.1).
- guards: see 2.2.2.
- timestamps: ISO 8601 UTC with optional 0–9 fractional seconds.

2.2.1) Edges Validation
- Each edge must reference known module IDs or reserved endpoints (e.g., "core.router").
- Topics charset: [a-z0-9._-], max length 64.
- Orchestrator MUST reject edges that terminate at modules with state=off.
- Duplicate edges are rejected.
- Post-apply, runtime edge registry MUST equal the snapshot; on mismatch, fail apply with error_code="edge_mismatch" and revert to pre-apply state.

2.2.2) Guards
- on_timeout_ms, off_timeout_ms (milliseconds; monotonic clock for durations).
- require_quiescence: when true, orchestrator waits until input queue size==0 up to drain_window_ms.
- drain_window_ms: maximum wait for quiescence.
- drain_policy: "discard" | "persist_to_dlq". For DLQ, configure a known DLQ destination.
- allow_degraded_on: boolean. See 2.1.3.

Updated Snapshot Example:
{
  "snapshot_id": "sha256:...",
  "signing_kid": "kid-2025-11-main",
  "signature": "ed25519:...",
  "prev_snapshot_id": "sha256:...",
  "revision": 17,
  "policy_version_ids": ["GSMD-2025.11.07"],
  "timestamp": "2025-11-07T10:30:00Z",
  "modules": {
    "M01.release_failures_and_rollbacks": { "state": "on" },
    "M02.merge_conflicts_and_delays":    { "state": "off" },
    "M03.technical_debt":                { "state": "on" },
    "M04.observability":                 { "state": "on" }
  },
  "edges": [
    { "from": "M01", "pub": "risk.decisions", "to": "core.router", "sub": "risk.decisions" },
    { "from": "core.git", "pub": "events.pr.opened", "to": "M01", "sub": "events.pr.opened" }
  ],
  "guards": {
    "on_timeout_ms": 5000,
    "off_timeout_ms": 5000,
    "require_quiescence": true,
    "drain_window_ms": 1500,
    "drain_policy": "discard",
    "allow_degraded_on": false
  }
}

2.3) Wire Transition Receipts (Append-Only JSONL; Durable)
Normative rules:
- One receipt per transition; plus one Apply Receipt per apply.
- Append-only file with fsync: per-line or batch<=50ms; rotate by size/time; retain ≥90 days; gzip allowed.
- No secrets/PII/code in receipts.

Receipt (transition) — Updated Fields:
{
  "ts": "2025-11-07T10:31:03.412Z",
  "orchestrator_id": "orch-01",
  "repo_id": "your-repo-uuid",
  "module_id": "M01.release_failures_and_rollbacks",
  "action": "wire_on",
  "prev_state": "off",
  "new_state": "on",
  "snapshot_id": "sha256:...",
  "result": "success",
  "duration_ms": 423,
  "error_code": null,
  "error_detail": null,
  "evidence": {
    "health_ok": true,
    "subscriptions_bound": ["events.pr.opened"],
    "publications_bound": ["risk.decisions"]
  }
}

Apply Receipt (summary of a plan_id):
{
  "ts": "2025-11-07T10:31:05.002Z",
  "orchestrator_id": "orch-01",
  "plan_id": "apply-000017",
  "snapshot_id": "sha256:...",
  "revision": 17,
  "counts": { "wire_on": 2, "wire_off": 1, "noop": 9, "skipped_due_to_dependency": 0, "failed": 0 },
  "result": "success",
  "error_code": null
}

3) Deterministic Orchestrator (Algorithm; Idempotent)

3.1) Apply Procedure
1. Load snapshot; verify signature over canonical JSON; verify signing_kid is trusted.
2. Check anti-replay: prev_snapshot_id must equal last applied; revision must be last_revision+1.
3. Discover manifests; validate contracts and requires comparators.
4. Build plan: topologically sort by requires/provides; detect cycles → fail with error_code="cycle_detected".
5. Acquire global apply lock; concurrent apply returns 409.
6. Persist current_state.json atomically; create plan_id and write checkpoint.
7. Transitions — OFF first, then ON:
   a) Wire-Off: unbind publications; unsubscribe inputs; if require_quiescence, wait up to drain_window_ms; apply drain_policy; call stop; emit receipt.
   b) Wire-On: call init then start; bind subscriptions then publications; health gate; on failure, revert bindings and stop; emit receipt.
8. Verify runtime edges == snapshot edges; on mismatch → fail with edge_mismatch; revert to pre-apply state.
9. Publish Capabilities Registry and ETag; write Apply Receipt; release lock.

3.2) Failure Containment
- On a module failure, continue for unaffected modules; dependent modules are marked skipped_due_to_dependency with receipts.
- On crash, resume from last checkpoint; idempotent transitions ensure consistent state.

4) Wiring Edges (Bus/Ports; No Direct Hard References)
- Orchestrator owns bind/unbind.
- Consumers MUST not reference providers directly; all traffic via declared topics/ports.
- Reserved endpoints (e.g., "core.router") are allowed and MUST be documented in platform manifest.

5) Minimal Interfaces (Language-Agnostic)
Module:
- init(context)  -> Ok | Err {code, message}
- start(context) -> Ok | Err {code, message}
- stop(context)  -> Ok | Err {code, message}
- health()       -> {status, details}

Orchestrator:
- apply(snapshot) → emits per-transition receipts + one Apply Receipt; returns summary {plan_id, counts, result}.

6) Validation & Acceptance Criteria (Testable)
1. Policy-driven toggling via snapshot only. (PASS)
2. Deterministic re-apply ⇒ no-op (Apply Receipt shows counts=0). (PASS)
3. Isolation: OFF module does not break others; Null Adapter returns capability_unavailable. (PASS)
4. Atomicity & rollback: failure leaves system consistent; receipts evidence. (PASS)
5. Auditability: One receipt per transition plus Apply Receipt; durable JSONL. (PASS)
6. Dependency safety: comparator grammar enforced; cycle detection. (PASS)
7. Drain & Quiescence: precedence and drain_policy enforced. (PASS)
8. Health gates: ok proceed; degraded per guard; fail rolls back. (PASS)
9. Hot reload: apply without full system restart. (PASS)
10. No hidden edges: post-apply verification and revert on mismatch. (PASS)

7) Operational Flow (CLI/API)
- Prepare new Wiring Snapshot JSON (with prev_snapshot_id and revision).
- Sign canonically (sorted keys, UTF-8, LF) with signing_kid; compute snapshot_id (sha256 over canonical JSON).
- Run orchestrator.apply(snapshot).
- Observe transition receipts and Apply Receipt; query /capabilities (ETag changes).

8) Security & Access Control
- Only authenticated principals with role orchestrator.apply may call apply; every attempt emits an access receipt.
- Trusted signing_kid set is versioned and rotated per policy.
- No secrets/PII/code in snapshots or receipts.

9) Crash Safety & Durability
- current_state.json persisted atomically (temp file + fsync + rename).
- plan_id checkpoints persisted before each transition.
- Receipts written append-only with fsync guarantees (per-line or ≤50ms batch); rotated and retained.

10) Null Adapter Contract (When Module is OFF)
- Calls to capability X MUST return a stable outcome without exceptions across process boundaries:
  { "error": "capability_unavailable", "capability": "X" }
- System behaviour remains deterministic; consumers must handle this code gracefully.

11) Capabilities Registry (Read-Only API)
- GET /capabilities → { "generated_at": timestamp, "revision": N, "etag": "...", "capabilities": [...] }
- ETag changes on every successful apply; generated_at equals Apply Receipt ts.
- Registry MUST include all provides from modules with state=on.

12) Timekeeping
- All durations computed from system monotonic clock.
- All timestamps are ISO 8601 UTC with optional 0–9 fractional seconds.
