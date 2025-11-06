# ZeroUI VS Code Extension — Modular Architecture & Enforcement Guide

> **Scope (deterministic):** This document defines **how the VS Code extension is structured and enforced** in this repository. It applies to the IDE-only surfaces (Status Pill → Decision Card → Evidence Drawer → Quick Actions → Receipt), with **no web UI**. It specifies folder layout, module contracts, build-time contribution generation, context keys, performance budgets, tests, and CI gates. It does not describe server endpoints or policy content.

---

## 1. Hard Constraints (VS Code Extension Host)

1. **Static `package.json` contributions.** Commands/menus/views/keybindings/configuration **must be present at package time**. Generation is allowed **before** packaging; runtime mutation is not.
2. **Fast activation.** `activate()` must return quickly; heavy work is deferred to command handlers.
3. **Context keys drive menus.** Use `vscode.commands.executeCommand('setContext', key, value)`. Menus evaluate `when` clauses over these keys.
4. **One or many Status Bar items.** Either is allowed. This guide standardizes on a **single shared item** with composition logic.
5. **Single extension artifact.** All Modules exist under one extension. No multi-extension packaging.

---

## 2. Directory Layout (authoritative)

```
src/
  core/                                # Shared framework (no product logic)
    command-registry/
    context-keys/
    decision-card/                     # Webview host
    evidence-drawer/                   # Drawer host
    problems-publisher/                # Diagnostics collection
    quick-actions/
    receipts/
    status-pill/
    telemetry/
    ipc-client/                        # Local IPC/HTTP to Edge Agent
    types/
  modules/                             # One folder per Module (m01..m20)
    m01-mmm-engine/
      module.manifest.json
      index.ts                         # export registerModule(context, deps): ZeroUIModule
      commands.ts
      providers/                       # status pill, diagnostics
      views/                           # DecisionCard sections, Drawer panes
      actions/                         # Quick actions (invoke Agent)
      __tests__/
    m02-cross-cutting-concern-services/
    m03-release-failures-rollbacks/
    m04-signal-ingestion-normalization/
    m05-detection-engine-core/
    m06-legacy-systems-safety/
    m07-technical-debt-accumulation/
    m08-merge-conflicts-delays/
    m09-compliance-security-challenges/
    m10-integration-adapters/
    m11-feature-dev-blind-spots/
    m12-knowledge-silo-prevention/
    m13-monitoring-observability-gaps/
    m14-client-admin-dashboard/
    m15-product-success-monitoring/
    m16-roi-dashboard/
    m17-gold-standards/
    m18-knowledge-integrity-discovery/
    m19-reporting/
    m20-qa-testing-deficiencies/
  extension.ts                         # Thin bootstrap (≤ 80 lines)
  module-loader.ts                     # Static imports & module assembly
  build/
    generate-contrib.ts                # Build-time: merge Module manifests → package.json.contributes
```

**Mapping (canonical slugs):** `m01`…`m20` as shown above. Filenames and command IDs must use these slugs exactly.

---

## 3. Command Naming & Menus (deterministic)

**Command ID pattern:** `zeroui.<moduleSlug>.<action>`

Examples:
```
zeroui.m03.showDecisionCard
zeroui.m03.runCanaryProbe
zeroui.m03.viewReceipt
zeroui.m03.quickFix.addTestStub
zeroui.m09.runSecurityScan
zeroui.m01.mmm.refresh
```

**Context keys:** `zeroui.module` (string), `zeroui.degraded` (boolean), `zeroui.hasReceipt` (boolean).  
Use them in `when` clauses, e.g. for Module 3 menu items:
```
"when": "zeroui.module == 'm03' && !zeroui.degraded"
```

---

## 4. Module Contract (TypeScript)

```ts
// src/core/types/module.ts
import * as vscode from 'vscode';

export interface ZeroUICommand {
  id: string;                                   // e.g., 'zeroui.m03.runCanaryProbe'
  title: string;                                // palette title
  handler: (args?: unknown) => Promise<void> | void;
  category?: string;
}

export interface StatusPillProvider {
  getText(): Promise<string>;                   // e.g., "Risk: High"
  getTooltip(): Promise<string>;
  onClickCommandId?: string;                    // often -> showDecisionCard
}

export interface DecisionCardSection {
  id: string;
  render(webview: vscode.Webview, panel: vscode.WebviewPanel): Promise<void>;
}

export interface EvidenceDrawerProvider {
  listItems(): Promise<readonly {label: string; open: () => Promise<void>}[]>;
}

export interface ProblemsPublisher {
  computeDiagnostics(): Promise<readonly vscode.Diagnostic[]>;
}

export interface QuickAction {
  id: string;                                   // command id
  label: string;
}

export interface ZeroUIModule {
  id: 'm01'|'m02'|'m03'|'m04'|'m05'|'m06'|'m07'|'m08'|'m09'|'m10'|
      'm11'|'m12'|'m13'|'m14'|'m15'|'m16'|'m17'|'m18'|'m19'|'m20';
  title: string;

  commands(): ZeroUICommand[];                  // static ids (declared in manifest)
  statusPill?(): StatusPillProvider;
  decisionCard?(): DecisionCardSection[];
  evidenceDrawer?(): EvidenceDrawerProvider;
  problems?(): ProblemsPublisher;
  quickActions?(): QuickAction[];

  activate(context: vscode.ExtensionContext, deps: CoreDeps): Promise<void>;
  deactivate?(): Promise<void>;
}
```

Each Module exports `registerModule(context, deps): ZeroUIModule` from `index.ts`.

---

## 5. Module Manifest (per-folder) & JSON Schema

**Location:** `src/modules/<slug>/module.manifest.json`

**Fields (static, enforced):**
```json
{
  "id": "m03",
  "title": "Release Failures & Rollbacks",
  "commands": [
    { "id": "zeroui.m03.showDecisionCard", "title": "Show Decision Card" },
    { "id": "zeroui.m03.viewReceipt",      "title": "View Last Receipt"  },
    { "id": "zeroui.m03.runCanaryProbe",   "title": "Run Canary Probe"   },
    { "id": "zeroui.m03.quickFix.addTestStub", "title": "Quick Fix: Add Test Stub" }
  ],
  "menus": {
    "commandPalette": [
      "zeroui.m03.showDecisionCard",
      "zeroui.m03.viewReceipt",
      "zeroui.m03.runCanaryProbe",
      "zeroui.m03.quickFix.addTestStub"
    ]
  },
  "views": [],
  "keybindings": [],
  "configuration": []
}
```

**Schema (minimal):**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["id","title","commands","menus","views","keybindings","configuration"],
  "additionalProperties": false,
  "properties": {
    "id": {"enum": ["m01","m02","m03","m04","m05","m06","m07","m08","m09","m10","m11","m12","m13","m14","m15","m16","m17","m18","m19","m20"]},
    "title": {"type": "string", "minLength": 1},
    "commands": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id","title"],
        "additionalProperties": false,
        "properties": {
          "id": {"type": "string", "pattern": "^zeroui\\.m\\d{2}\\.[a-zA-Z0-9_.-]+$"},
          "title": {"type": "string", "minLength": 1}
        }
      }
    },
    "menus": {"type": "object"},
    "views": {"type": "array"},
    "keybindings": {"type": "array"},
    "configuration": {"type": "array"}
  }
}
```

---

## 6. Build-Time Generation (`build/generate-contrib.ts`)

**Goal:** Merge all `module.manifest.json` files into a **single** `package.json.contributes` object.

**Deterministic rules:**
- Fail if **duplicate command IDs** or duplicate view IDs exist.
- Fail if a command ID does **not** match `^zeroui\.m\d{2}\.`.
- Fail on unknown `when` context keys (allow-list: `zeroui.module`, `zeroui.degraded`, `zeroui.hasReceipt`).
- Output sections: `commands`, `menus`, and (if provided) `views`, `keybindings`, `configuration`.
- Write to `package.json` **before packaging**.
- Emit a stable sorted order (by Module id, then command id).

**Pseudocode outline:**
```ts
// 1) Load all src/modules/*/module.manifest.json
// 2) Validate against schema and naming
// 3) Accumulate contributes.* sections
// 4) Sort deterministically
// 5) Merge into package.json (replace contributes)
// 6) Write package.json; exit non-zero on any error
```

---

## 7. Bootstrap & Loader (thin `extension.ts`)

**`extension.ts` (example skeleton):**
```ts
import * as vscode from 'vscode';
import { loadAllModules } from './module-loader';
import { makeCoreDeps } from './core/deps';

export async function activate(context: vscode.ExtensionContext) {
  const deps = makeCoreDeps(context); // ipc, receipts, status-pill, telemetry, config
  const modules = await loadAllModules(context, deps);

  for (const m of modules) {
    for (const cmd of m.commands()) {
      const disp = vscode.commands.registerCommand(cmd.id, cmd.handler);
      context.subscriptions.push(disp);
    }
    await m.activate(context, deps);
  }
}

export async function deactivate() { /* if needed */ }
```

**`module-loader.ts` (static imports):**
```ts
import { registerModule as m01 } from './modules/m01-mmm-engine';
import { registerModule as m02 } from './modules/m02-cross-cutting-concern-services';
// … up to m20

export async function loadAllModules(context, deps) {
  return [
    m01(context, deps),
    m02(context, deps),
    // … m20(context, deps)
  ];
}
```

> **Note:** Static imports keep bundlers deterministic. When adding a Module, update this file and the manifest list in the generator (a single source of truth).

---

## 8. Shared UI Hosts (strict separation)

- **Status Pill:** `core/status-pill/` composes text & tooltip by querying each Module’s `StatusPillProvider`. Render time budget **≤ 50 ms** initial.
- **Decision Card:** Single Webview host in `core/decision-card/`. Modules contribute **sections** that render within isolated DOM roots. Host → section messages include `{ moduleId, type, payload }` and are validated.
- **Evidence Drawer:** `core/evidence-drawer/` lists items provided by each Module; opening an item runs its `open()` method.
- **Problems Publisher:** `core/problems-publisher/` owns the diagnostic collection. Modules provide `computeDiagnostics()`; host applies them.

**Isolation requirements (enforced in code):**
- Each section’s DOM under `#zeroui-section-<moduleId>-<sectionId>`.
- Message contract: `{ moduleId: 'mXX', type: string, payload: object }`. Reject if `moduleId` mismatches sender.
- No cross-module imports inside Modules. Only `core/*` may be imported by Modules.

---

## 9. Context Keys Manager

- Initialize: `zeroui.module = 'mXX'` when a Module’s surfaces are in focus; default `'m01'` (or `'none'` if no focus).
- Update on: editor change, panel visibility changes, receipt updates.
- Maintain: `zeroui.degraded` and `zeroui.hasReceipt` based on Agent responses/receipts.

---

## 10. Performance Budgets (measured, not aspirational)

- Activation cold start: **< 50 ms** (registration only).
- Status pill initial render: **≤ 50 ms**.
- Command handlers: return control immediately; long work runs async.
- Diagnostics recompute: background, coalesced, with cancellation.
- No blocking UI thread calls to IPC. All IPC async with timeouts & error normalization.

---

## 11. Tests (required)

- **Module unit tests:** each `src/modules/<slug>/__tests__/` must cover:
  - command handlers (success/error);
  - providers (status pill, diagnostics) via mocks.
- **Core integration test:** boot extension with mock `CoreDeps`; validate:
  - commands are registered for all Modules;
  - context keys are applied for positive/negative `when` cases;
  - decision-card host renders a module section;
  - evidence-drawer merges items from two Modules.
- **Generator tests:** lint for duplicates, bad IDs, unknown context keys, unstable sort order.

---

## 12. CI Gates (deterministic, fail-fast)

1. **Generator Drift:** re-run `build/generate-contrib.ts`; fail if `package.json` changes (force commit).
2. **Duplicates/Invalid IDs:** generator must exit non-zero on any duplicate ID or invalid command id pattern.
3. **Schema Validation:** validate each `module.manifest.json` against the JSON Schema in §5.
4. **Activation Budget:** run an activation timing test; fail if > 50 ms on CI runner.
5. **Menu `when` Checks:** scripted e2e verifies visibility toggles using context keys.
6. **Windows Build:** compile on Windows runner; fail on native deps.

---

## 13. Acceptance Criteria (the split is “done” when)

- `extension.ts` ≤ 80 lines; no Module logic inside.
- All 20 Modules exist under `src/modules/…` and export `registerModule()`.
- `build/generate-contrib.ts` produces a single static `package.json.contributes` including commands/menus/views/keybindings/configuration; duplicates rejected.
- Status Pill, Decision Card, Evidence Drawer, Problems are hosted under `core/*`; Modules only provide providers/sections.
- Context keys are initialized and toggled deterministically; menus reflect `when` logic in tests.
- Performance budgets in §10 are met in CI.
- CI gates in §12 all pass.

---

## 14. Change Management

- Adding a Module requires:
  1) create `src/modules/<slug>/` with `module.manifest.json` and `index.ts`;  
  2) add a static import in `module-loader.ts`;  
  3) re-run generator and commit `package.json` changes;  
  4) add tests;  
  5) pass CI gates.

- Removing a Module requires the inverse steps; generator removes contributions.

---

**This document is normative.** Any deviation (foldering, command IDs, missing manifests, runtime-generated contributions) must be corrected before merge.
