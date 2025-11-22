# Detection Engine Core - Product Requirements Document (PRD)

Product: ZeroUI  
Module: Detection Engine Core (M05)  
Document type: Implementation-ready PRD  
Status: Pending (docs/architecture/Module_Implementation_Prioritization_Reordered.md)  

## Sources (fact-checked)
- Module listing and code mapping: docs/product-prd/FUNCTIONAL_MODULES_AND_CAPABILITIES.md; docs/architecture/modules-mapping-and-gsmd-guide.md (`src/vscode-extension/modules/m05-detection-engine-core/`, `gsmd/gsmd/modules/M05/`).
- VS Code module contract: docs/architecture/architecture-vscode-modular-extension.md; current manifest and skeleton code in `src/vscode-extension/modules/m05-detection-engine-core/`; UI wrapper in `src/vscode-extension/ui/detection-engine-core/ExtensionInterface.ts`.
- Service structure: docs/architecture/zeroui-hla.md and docs/architecture/zeroui-lla.md list `src/cloud-services/product-services/detection-engine-core/` (directory exists but is empty).
- GSMD baseline snapshots: `gsmd/gsmd/modules/M05/*/v1/snapshot.json` (evaluation_points, overrides, rollout, observability, evidence map, receipts required/optional).
- Contracts: `contracts/detection_engine_core/` (OpenAPI stub, placeholder schemas, feedback receipt schema, example payloads) and placement log `PLACEMENT_REPORT.json`.
- Receipt schemas and cross-reference: docs/architecture/receipt-schema-cross-reference.md; `src/edge-agent/shared/receipt-types.ts`; GSMD `receipts_schema` (required and optional fields).
- Trust and privacy constraints: docs/architecture/modules/Trust_as_a_Capability_V_0_1.md (Decision Receipt schema, privacy redaction rules, receipt performance budgets, actor.type governance).
- Accuracy rule: docs/constitution/MASTER GENERIC RULES.json (Rule R-036 "Detection Engine - Be Accurate"); validator enforcement in `validator/rules/problem_solving.py`.
- Signal dependency: docs/architecture/modules/Signal_Ingestion_and_Normalization_Module_PRD_v1_0.md (detection engines act on normalized signals; SIN does not define detection logic).
- AI assistance detection signals: `src/edge-agent/shared/ai-detection/AIAssistanceDetector.ts`.

## 1. Module summary and scope
- Module identity: Detection Engine Core (M05) is one of the 20 functional modules (docs/product-prd/FUNCTIONAL_MODULES_AND_CAPABILITIES.md) and is mapped to `src/vscode-extension/modules/m05-detection-engine-core/` and `gsmd/gsmd/modules/M05/` (docs/architecture/modules-mapping-and-gsmd-guide.md).
- Surfaces defined in architecture:
  - VS Code module (manifested commands, status pill, decision card sections, quick actions) per docs/architecture/architecture-vscode-modular-extension.md; current implementation is a skeleton.
  - Cloud service under `src/cloud-services/product-services/detection-engine-core/` following the FastAPI pattern shown in docs/architecture/zeroui-hla.md and docs/architecture/zeroui-lla.md (present but empty).
  - Contracts under `contracts/detection_engine_core/` (OpenAPI 0.1.0 stub, placeholder schemas, feedback receipt schema).
  - GSMD policy snapshots for M05 (messages, gate_rules, evidence_map, observability, overrides, rollout, receipts_schema, risk_model, checklist, triggers).
- Upstream dependency: consumes normalized signals provided by the Signal Ingestion & Normalization module; SIN explicitly states detection engines act on normalized signals and that SIN does not define detection logic (docs/architecture/modules/Signal_Ingestion_and_Normalization_Module_PRD_v1_0.md).
- Cross-cutting obligations: system-wide Decision Receipt, privacy, override, and actor.type rules apply (docs/architecture/modules/Trust_as_a_Capability_V_0_1.md).

## 2. Current state (repository inventory)
- VS Code module manifest defines two commands (`zeroui.m05.showDecisionCard`, `zeroui.m05.viewReceipt`) but providers and handlers are empty skeletons (src/vscode-extension/modules/m05-detection-engine-core/module.manifest.json, index.ts, commands.ts, providers/*, actions/*, __tests__/*).
- **Module ID case issue**: The current skeleton implementation in `index.ts` returns `id: "M05"` (uppercase), but the architecture contract in `docs/architecture/architecture-vscode-modular-extension.md` requires module IDs to be lowercase (`'m01'|'m02'|...|'m20'`). The implementation must be corrected to return `id: "m05"` (lowercase) to match the architecture contract.
- UI wrapper exposes commands `zeroui.detection.engine.core.showDashboard` and `zeroui.detection.engine.core.refresh` and a tree view `zerouiDetectionEngineCore`, all using placeholder handlers (src/vscode-extension/ui/detection-engine-core/ExtensionInterface.ts, UIComponentManager.ts).
- Cloud service directory exists but contains no files (src/cloud-services/product-services/detection-engine-core/).
- Contracts are placeholders except for the concrete feedback receipt schema (required fields: feedback_id, decision_receipt_id, pattern_id enum FB-01..04, choice enum worked/partly/didnt, tags, actor.repo_id, timestamp_utc, signature) and example JSONs (contracts/detection_engine_core/schemas/*.json, examples/*.json, openapi/openapi_detection_engine_core.yaml).
- GSMD M05 snapshots are populated with generic values: evaluation_points `["pre-commit","pre-merge","pre-deploy","post-deploy"]` (embedded in each snapshot file under the `evaluation_points` field), overrides modes `[off,warn,soft,hard]` with dual_channel true and expiry PT2H, rollout default_mode warn with cohorts `["service:a","env:staging"]`, observability metrics `["zero_ui.policy.decision"]`, evidence selectors for artifacts and otel logs (structured as `{"kind": "artifact", "selector": "path:/**/artifacts/**"}` and `{"kind": "log", "selector": "otel:service/**"}`), privacy redactions for email and ticket_url, receipts.required `[decision,rationale,policy_snapshot_hash,policy_version_ids,evaluation_point,actor_id,repo_id,timestamps.hw,signature]`, optional `[advisories[],evidence_ids[],cohort]`, plus gold/deny test fixtures.
- Receipt schema cross-reference and TypeScript interfaces are defined and used across the codebase (`src/edge-agent/shared/receipt-types.ts`; docs/architecture/receipt-schema-cross-reference.md).
- Constitution rule R-036 requires accuracy and reliability, validation before reporting, and maintaining high precision/recall; validator/rules/problem_solving.py checks for confidence reporting, accuracy metrics (precision/recall/F1/false positive/false negative), uncertainty handling, and learning from corrections in detection outputs.

## 3. Functional requirements

### 3.1 Inputs and evaluation points
- Detection Engine Core shall operate on normalized signals emitted by SIN; SIN already provides the canonical SignalEnvelope and explicitly delegates detection/ML to downstream engines (docs/architecture/modules/Signal_Ingestion_and_Normalization_Module_PRD_v1_0.md).
- Supported evaluation points are fixed by GSMD snapshots: pre-commit, pre-merge, pre-deploy, post-deploy. Evaluation points are embedded in each GSMD snapshot file under the `evaluation_points` field (not in a separate dedicated snapshot file). All snapshot files in `gsmd/gsmd/modules/M05/*/v1/snapshot.json` contain this field. Any change to evaluation points must be reflected in all GSMD snapshots to keep invariants intact.

### 3.2 Decisions and receipts
- Decisions shall use the status set defined in GSMD and receipt types: pass, warn, soft_block, hard_block (docs/architecture/receipt-schema-cross-reference.md; `decision.status` enum in src/edge-agent/shared/receipt-types.ts).
- Every automated action from this module shall emit a Decision Receipt conforming to TR-1.2.1 (docs/architecture/modules/Trust_as_a_Capability_V_0_1.md) and the GSMD-required fields (receipts_schema required/optional arrays for M05). Required fields per GSMD snapshot include: decision, rationale, policy_snapshot_hash, policy_version_ids, evaluation_point, actor_id, repo_id, timestamps.hw, signature; optional: advisories[], evidence_ids[], cohort (gsmd/gsmd/modules/M05/receipts_schema/v1/snapshot.json).
- **CRITICAL: Field name mapping**: GSMD snapshots use field name `policy_snapshot_hash` (as listed in receipts_schema required array), but the TypeScript `DecisionReceipt` interface in `src/edge-agent/shared/receipt-types.ts` uses `snapshot_hash` (without "policy_" prefix). This discrepancy must be resolved before implementation. Either: (1) update GSMD snapshots to use `snapshot_hash` to match TypeScript interface, OR (2) update TypeScript interface to use `policy_snapshot_hash` to match GSMD. The Trust document TR-1.2.1 also uses `snapshot_hash`, suggesting GSMD should be updated to match.
- **Field structure mapping**: GSMD field names `actor_id` and `repo_id` (listed as separate required fields) map to the nested TypeScript structure `actor.repo_id` and `actor.machine_fingerprint?` in the `DecisionReceipt` interface. This is a naming convention difference: GSMD uses dot-notation field names that correspond to nested object properties in the implementation.
- Receipts shall include actor.type when reliable signals are available, using the conservative detection rules in `src/edge-agent/shared/ai-detection/AIAssistanceDetector.ts` (TR-6.2.2/6.2.4 in docs/architecture/modules/Trust_as_a_Capability_V_0_1.md).
- Receipts shall honor privacy constraints from Trust_as_a_Capability_V_0_1.md (metadata-only inputs, no raw source/PII) and the GSMD privacy redactions (email, ticket_url).
- Receipt generation must respect the performance budgets defined for Decision Receipts: <=50ms p95 (pre-commit), <=100ms p95 (pre-merge), <=200ms p95 (pre-/post-deploy) as listed in docs/architecture/modules/Trust_as_a_Capability_V_0_1.md NFR-T-1.1.

### 3.3 Accuracy and quality obligations (Rule R-036)
- Comply with constitution rule R-036 "Detection Engine - Be Accurate": ensure detection accuracy, minimize false positives, validate detection results before reporting, and maintain high precision/recall (docs/constitution/MASTER GENERIC RULES.json).
- The validator expectations in `validator/rules/problem_solving.py` must be satisfied: provide confidence level reporting, expose accuracy metrics (precision, recall, F1, false_positive, false_negative, error_rate), handle uncertainty explicitly, and support learning from corrections/feedback.
- Detection outputs shall not claim certainty when signals are ambiguous; ambiguous cases must follow the conservative actor/type handling noted above.

### 3.4 Observability, evidence, and privacy
- Observability metrics must, at minimum, emit `zero_ui.policy.decision` with exemplars as defined in GSMD observability snapshot (gsmd/gsmd/modules/M05/observability/v1/snapshot.json). Extend with Trust rule TR-5 metrics derived from receipts: rule_fire_count, override_count, incident_count, incident_count_no_fire (docs/architecture/modules/Trust_as_a_Capability_V_0_1.md).
- Evidence map defaults are structured objects in GSMD snapshot (gsmd/gsmd/modules/M05/evidence_map/v1/snapshot.json): `{"kind": "artifact", "selector": "path:/**/artifacts/**"}` and `{"kind": "log", "selector": "otel:service/**"}`. The shorthand notation `artifact:path:/**/artifacts/**` and `log:otel:service/**` refers to these structured objects. Keep GSMD synchronized if selectors change.
- Privacy redactions must include at least email and ticket_url as listed in GSMD privacy fields; any broader data handling changes require GSMD updates and alignment with Trust TR-4 (metadata-first, opt-in expansion).

### 3.5 Rollout, overrides, and modes
- Supported modes per GSMD overrides: off, warn, soft, hard; dual_channel true; expiry PT2H; authoriser_roles placeholder array. Changes to modes or expiries must be reflected in GSMD overrides snapshot.
- Default rollout is warn with cohorts `service:a` and `env:staging` and ladder warn->soft->hard (gsmd/gsmd/modules/M05/rollout/v1/snapshot.json). Implementation may adjust cohorts/ladder but must update GSMD snapshot accordingly.
- Overrides must be captured in receipts (override reason, approver, timestamp, optional override_id) per TR-3.2 (docs/architecture/modules/Trust_as_a_Capability_V_0_1.md) and the DecisionReceipt interface in src/edge-agent/shared/receipt-types.ts.

### 3.6 Feedback capture
- Feedback receipts must follow the schema in `contracts/detection_engine_core/schemas/feedback_receipt.schema.json` (feedback_id, decision_receipt_id, pattern_id enum FB-01..04, choice enum worked/partly/didnt, tags array, actor.repo_id required, timestamp_utc, signature). Examples exist in `contracts/detection_engine_core/examples/feedback_receipt_valid.json`.
- Feedback should be linkable to Decision Receipts via decision_receipt_id to support "learning from corrections" obligations in the validator.

### 3.7 Contracts and API surface
- The OpenAPI file for this module is currently empty (contracts/detection_engine_core/openapi/openapi_detection_engine_core.yaml). It must be populated to describe local APIs for decisions, evidence links, and feedback; keep it consistent with JSON Schemas.
- Schema placeholders (decision_response.schema.json, envelope.schema.json, evidence_link.schema.json, receipt.schema.json) must be replaced with concrete constraints that match the DecisionReceipt interface and GSMD receipts_schema requirements. Evidence link fields must include type, href, and label as in `examples/evidence_link_valid.json`.
- Placement tracking: update `contracts/detection_engine_core/PLACEMENT_REPORT.json` whenever schemas/examples change to preserve contract auditability.

### 3.8 VS Code extension integration
- Implement module contract per docs/architecture/architecture-vscode-modular-extension.md: provide concrete implementations for commands (`zeroui.m05.showDecisionCard`, `zeroui.m05.viewReceipt`), status pill provider, decision card sections, diagnostics, evidence drawer, and quick actions. Align manifests with static contribution rules (commands must be declared at package time).
- Wire the UI wrapper commands `zeroui.detection.engine.core.showDashboard` and `zeroui.detection.engine.core.refresh` to actual data sources and dashboards using the PlaceholderUIComponentManager hooks (src/vscode-extension/ui/detection-engine-core/*). Ensure module id/context keys use canonical slug m05.
- Ensure context keys and module id use canonical slug `m05` in extension contributions; keep activation fast (architecture hard constraint).

### 3.9 Service boundary
- Implement the product-service under `src/cloud-services/product-services/detection-engine-core/` using the FastAPI pattern documented in docs/architecture/zeroui-hla.md and docs/architecture/zeroui-lla.md (main.py, routes.py, services.py, models.py). No business logic currently exists; add only within this boundary.
- Service endpoints must align with the contracts above and emit Decision Receipts via the shared ReceiptGenerator (src/edge-agent/shared/storage/ReceiptGenerator.ts) or equivalent server-side writer, including actor.type when detectable.

### 3.10 Tests and fixtures
- Maintain and extend the existing contract loader test `tests/contracts/detection_engine_core/validate_examples.py` to cover updated examples/schemas.
- Add module-level Jest tests under `src/vscode-extension/modules/m05-detection-engine-core/__tests__/` for commands, status pill, and decision card rendering once implemented.
- GSMD test fixtures (gold-path expects decision pass; deny-path expects hard_block) must remain valid or be updated alongside GSMD snapshots to reflect real logic.
- Trust rule validation: ensure outputs satisfy validator/rules/problem_solving.py checks (confidence, accuracy metrics, uncertainty, learning).

### 3.11 Runtime policy (fail-open/closed)
- Define and document fail-open or fail-closed behavior for each evaluation point (pre-commit, pre-merge, pre-deploy, post-deploy) and mirror the chosen policy in `gsmd/gsmd/modules/M05/gate_rules/v1/snapshot.json`. Keep schema_version and version.major unchanged.

### 3.12 Performance validation
- Measure and record receipt-generation latency against NFR-T-1.1 budgets by surface (<=50ms pre-commit, <=100ms pre-merge, <=200ms pre-/post-deploy) and expose degraded mode explicitly via the DecisionReceipt `degraded` flag. Document results and guardrails in gate rules if degraded handling differs by evaluation point.

## 4. Non-functional requirements
- Receipt generation latency budgets per Trust_as_a_Capability_V_0_1.md NFR-T-1.1 (50ms/100ms/200ms p95 by surface) apply to Detection Engine Core outputs.
- Storage: receipts must be append-only and signed (per ReceiptStorageService patterns in src/edge-agent/shared/storage/ReceiptStorageService.ts and GSMD receipts_schema required signature).
- Reliability: follow Trust NFR-T-2 degraded-mode behaviour (explicit degraded flag in DecisionReceipt interface) and document whether detection decisions fail-open or fail-closed for each evaluation point; reflect this policy in GSMD gate_rules snapshot when defined.

## 5. Alignment and change management
- Keep GSMD snapshots (`gsmd/gsmd/modules/M05/*/v1/snapshot.json`) authoritative for evaluation_points, overrides, rollout, observability, evidence map, and receipts_schema; any implementation change must be mirrored in these snapshots to preserve CI checks described in docs/architecture/modules-mapping-and-gsmd-guide.md.
- Keep contracts (`contracts/detection_engine_core/*`) in sync with implementation and GSMD; update examples alongside schema changes.
- Maintain VS Code manifest consistency with architecture-vscode-modular-extension hard constraints (static contributions, module slugging).
- Changes to accuracy behaviour must continue to satisfy constitution rule R-036 and the validator checks; do not reduce accuracy/precision without updating governing rules if applicable.
- Performance, degraded-mode handling, and fail-open/closed choices must be documented in gate rules and receipts and kept aligned with GSMD and Trust constraints without altering schema_version or version.major.

## 6. Open gaps to close
- **CRITICAL**: Resolve field name mismatch between GSMD `policy_snapshot_hash` and TypeScript `snapshot_hash` before implementation (see Section 3.2 for details).
- **CRITICAL**: Fix module ID case in `src/vscode-extension/modules/m05-detection-engine-core/index.ts` to return `"m05"` (lowercase) instead of `"M05"` (uppercase) to match architecture contract.
- Populate the OpenAPI spec and concrete JSON Schemas for decision_response, envelope, evidence_link, and receipt; current files are placeholders.
- Implement detection logic and decision calculation in `src/cloud-services/product-services/detection-engine-core/` and wire it to emit Decision Receipts (with actor.type when detectable).
- Implement the VS Code module surfaces (`src/vscode-extension/modules/m05-detection-engine-core/*` and `ui/detection-engine-core/ExtensionInterface.ts`) with real commands, status pill, decision card sections, diagnostics, evidence drawer, and quick actions.
- Wire feedback capture using `contracts/detection_engine_core/schemas/feedback_receipt.schema.json` so feedback links to decision_receipt_id and supports learning from corrections.
- Define fail-open/closed policy per evaluation point and update `gsmd/gsmd/modules/M05/gate_rules/v1/snapshot.json` accordingly without changing schema_version or version.major.
- Extend observability with TR-5 rule-level metrics (rule_fire_count, override_count, incident_count, incident_count_no_fire) derived from receipts; reflect any additions in GSMD observability snapshot.
- Validate latency against NFR-T-1.1 budgets and document degraded-mode handling in receipts and gate rules if behaviour differs by evaluation point.
- Replace placeholder cohorts/overrides/rollout values in GSMD snapshots with real rollout policy if different, keeping schema_version and version.major intact.

---

This PRD is fully derived from repository artifacts listed in the Sources section; no external assumptions are introduced. Changes must stay synchronized across GSMD, contracts, VS Code extension, and service boundaries to remain compliant with existing invariants and constitutional accuracy requirements.
