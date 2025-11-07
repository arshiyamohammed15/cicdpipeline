ZeroUI — Quick Fix (Non‑AI) Framework v1.0

Applies across all modules and triggers. Canonical IDE chain: Status Pill → Diagnostics → Quick Fix → Decision Card → Notification → Receipt → Timeline.

Compiled: 2025-11-07 11:00:32 IST

1. Purpose & Applicability

This Framework standardises how Quick Fix and related solution actions are designed, executed, and validated across all modules and triggers in ZeroUI, without any AI code generation. It converts the non‑AI specification into normative rules, contracts, and checklists that each module MUST follow.

2. Normative Language

MUST: mandatory to claim conformance.

SHOULD: strongly recommended; acceptable deviations MUST be documented per trigger.

MAY: optional behaviour; if used, MUST be receipt‑logged.

3. Invariants (Non‑AI Principles)

Deterministic only — every action is predefined, testable, and reversible.

No source edits by LLM or generative tools. Any change MUST come from a pre‑approved artifact (patch/template) or a deterministic local tool.

User in control — preview → confirm → apply; show a diff for any file change.

Local‑first via Edge Agent; no code/PII leaves the laptop.

Receipts‑first — log INTENT→RESULT with sequence_no and hash chain.

Degraded mode safety — if trust fails, only allow: open_decision_card, navigate, guide.

4. Allowed Quick Fix Types (Authorised Actions)

• Navigate & Reveal: Open exact file/line/range; focus Problems/SCM/Settings.

• Run Deterministic Tool: Invoke a locally installed, allow‑listed tool (see §6).

• Apply Signed Patch (Config/Docs/CI only): Policy‑owned, digitally signed patch; side‑by‑side diff before apply.

• Insert from Signed Template: Insert a signed template; preview required.

• Create Safe Branch / Split PR: Policy‑provided git actions to reduce risk.

• Open Fix Guide (Decision Card): Step‑by‑step instructions; no code content.

• Escalate / Ask for Help: Policy‑driven escalation; evidence IDs only.

• Request Override: Dual‑channel approval; reason/scope/expiry; hard/soft‑block only.

5. Gate × Fix Matrix (Module‑Agnostic)

| Gate | User Sees | Allowed Examples | Disallowed |
| --- | --- | --- | --- |
| Warn | Guidance with preferred action | navigate • run deterministic tool • guide • branch | Any auto‑edit of product code |
| Soft‑block | Must fix or request override | signed patch/template (config/docs/CI) • deterministic tool • guide • escalate | AI edits; unsanctioned scripts |
| Hard‑block | Blocked until fixed/authorised | guide • escalate • request override (dual‑channel) | Any bypass of policy |

6. Deterministic Tools Allow‑List (with Version Pinning)

Modules MUST invoke only allow‑listed tools defined in the active policy snapshot. Versions MUST be pinned and enforced by CI. Dry‑run output MUST match the final diff (idempotence). Example entry:

{
  "tool_id": "LINTER_TOOL",
  "version": "X.Y.Z",
  "command": "linter --fix --format json",
  "working_dir": "${workspace}",
  "dry_run_supported": true,
  "max_runtime_ms": 120000
}

7. LSP Refactor Determinism

Pin language server version and capabilities in policy.

Require a dry‑run preview; the diff MUST match the applied change exactly.

Restrict to explicit line‑range boundaries from diagnostics.

Abort if file changes between preview and apply (re‑preview).

8. RBAC Role Map (Who May Apply What)

| Fix Type | Developer | Reviewer | Approver |
| --- | --- | --- | --- |
| Navigate & Guide | ✓ | ✓ | ✓ |
| Run Deterministic Tool | ✓ | ✓ | ✓ |
| Signed Template (insert) | ✓ | ✓ | ✓ |
| Signed Patch (config/docs/CI) | ✓ | ✓ | ✓ |
| Create Branch / Split PR | ✓ | ✓ | ✓ |
| Escalate / Ask for Help | ✓ | ✓ | ✓ |
| Request Override | — | — | ✓ |

Note: Product‑code editing by automation is NOT permitted.

9. Failure UX (Post‑Confirm)

Render Decision Card in error state; show actionable reason using i18n keys (no literals).

Offer safe fallbacks: open guide • navigate • escalate • request override (where policy permits).

Write a T2 failure receipt including error category and evidence IDs; no stack traces or PII.

Suggested i18n keys (examples):

{
  "dc.error.title": "action_failed_title",
  "dc.error.reason": "action_failed_reason_generic",
  "dc.error.actions.escalate": "action_escalate",
  "dc.error.actions.openGuide": "action_open_guide"
}

10. Policy Contract — Fix Entry (Module‑Agnostic)

{
  "fix_id": "FIX-XXX-001",
  "title_key": "fix.title.key",
  "type": "navigate|run_tool|signed_patch|insert_template|branch|guide|escalate|override_request",
  "applies_to": { "event_type": "ENUM.EVENT.TYPE" },
  "artifact_ref": "sha256:...",
  "tool_ref": "LINTER_TOOL@X.Y.Z",
  "preview": "none|side_by_side|diff_only",
  "requires_role": ["developer","reviewer","approver"],
  "rbac": { "apply_roles": ["developer"] },
  "rollback": "git_revert_last_patch",
  "i18n": { "primary_key": "fix.primary", "secondary_key": "fix.secondary" }
}

11. Receipt Contract — INTENT → RESULT (Extended)

{
  "ts": "<iso8601>",
  "trigger_id": "<ID>",
  "module": "<MODULE_ID>",
  "phase": "<PHASE>",
  "signals_snapshot": { "file_path": "<path>", "line_range": [start,end] },
  "policy_snapshot_hash": "sha256:<policy>",
  "t1_action": {
    "fix_id": "FIX-XXX-001",
    "type": "signed_patch",
    "decision": "apply|cancel",
    "time_to_action_ms": 0
  },
  "t2_result": {
    "status": "success|failed|abandoned",
    "error_category": "none|tool_error|signature_invalid|conflict",
    "evidence": { "files_changed": 1, "artifact_ref": "sha256:..." }
  },
  "zu": { "repo_id": "<opaque>", "workspace_id": "<opaque>" },
  "sequence_no": 0,
  "prev_receipt_hash": "sha256:...",
  "receipt_hash": "sha256:..."
}

12. Execution Path (Extension ↔ Edge Agent)

Diagnostics raise event with Enum IDs → Quick Fix menu materialises from policy snapshot.

User selects a fix → Decision Card shows “What will happen” & i18n copy.

Extension calls Edge Agent with {fix_id, context}; agent verifies signature/KID or tool allow‑list.

Agent performs dry‑run → returns preview/diff → extension shows Diff for confirm (if applicable).

On confirm, agent applies action → emits receipt (sequence_no/hash chain).

Extension updates surfaces (Notification for soft/hard‑block only) → Timeline shows receipt summary.

13. CI Assertion Pack (Executable Checklist)

If policy defines a Quick Fix for a diagnostic, at least one is offered and the preferred matches policy.

Only allow‑listed tools with exact versions are invoked; dry‑run diff equals final change.

Any signed patch/template verifies signature/KID before apply.

Receipts validate against schema and maintain hash‑chain continuity; sequence_no increments.

All user‑visible strings come from the i18n table; no literals.

No UI thread blocking; latency budgets met for all surfaces.

RBAC: only authorised roles can apply each fix type.

Degraded mode: only open_decision_card/navigate/guide are enabled on trust failure.

14. Module Integration Procedure (Apply Framework per Trigger)

Register trigger/event types in Enum Registry (no free‑text).

Author the Quick Fix catalog in the policy snapshot using §10.

If using tools, add allow‑list entries with pinned versions (§6).

Provide i18n string keys for all user‑visible copy (§9).

Define RBAC per fix type (§8).

Implement extension surfaces to read policy → render Quick Fix → open Decision Card.

Implement Edge Agent actions: verify signature/KID or tool allow‑list → dry‑run → apply → receipt.

Write CI assertions from §13 for the new trigger.

Sign the policy snapshot and publish the public key (KID) to trust store.

Run acceptance tests; merge only on full pass.

15. Degraded Mode Allow‑List (Explicit)

open_decision_card

navigate

guide

16. Identifier Glossary (Enum Registry)

- module_id

- event_type

- action_type

- reason

- fix_id

- surface_id

- tool_id
