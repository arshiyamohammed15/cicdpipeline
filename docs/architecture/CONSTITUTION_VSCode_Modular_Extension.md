# ZeroUI VS Code Extension — **Constitution Rules** (Derived from ARCHITECTURE_VSCode_Modular_Extension.md)

> **Source of truth:** Every rule below is derived solely from `ARCHITECTURE_VSCode_Modular_Extension.md`. No additions beyond that document. This file governs the VS Code extension architecture in this repository.

---

## 1. Scope & Non‑Goals

1.1 **Scope:** IDE-only surfaces (Status Pill → Decision Card → Evidence Drawer → Quick Actions → Receipt). **No web UI.**  
1.2 **Non‑Goals:** This Constitution does **not** define server endpoints or policy content.

---

## 2. Hard Constraints (VS Code Host)

2.1 **Static contributions:** `package.json` contributions (commands, menus, views, keybindings, configuration) **MUST** exist at package time. Runtime mutation is **NOT** allowed.  
2.2 **Fast activation:** `activate()` **MUST** return quickly; heavy work **MUST** be deferred to command handlers.  
2.3 **Context keys:** Menus **MUST** be driven via `vscode.commands.executeCommand('setContext', key, value)` and `when` clauses.  
2.4 **Status Bar policy:** The extension **SHALL** standardize on a **single shared** Status Bar item with composition logic.  
2.5 **Single artifact:** The repository **MUST** ship **one** extension artifact; multi-extension packaging is **NOT** permitted.

---

## 3. Canonical Directory Layout

3.1 **Authoritative structure:**

```
src/
  core/
    command-registry/
    context-keys/
    decision-card/
    evidence-drawer/
    problems-publisher/
    quick-actions/
    receipts/
    status-pill/
    telemetry/
    ipc-client/
    types/
  modules/                  # m01..m20 (one folder per Module)
    m01-mmm-engine/
      module.manifest.json
      index.ts
      commands.ts
      providers/
      views/
      actions/
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
  extension.ts              # Thin bootstrap (≤ 80 lines)
  module-loader.ts          # Static imports & module assembly
  build/
    generate-contrib.ts     # Build-time merge → package.json.contributes
```

3.2 **Core isolation:** `src/core/` contains shared framework code only. Product logic **MUST NOT** be placed in `core/`.  
3.3 **Modules home:** All feature code **MUST** live under `src/modules/<slug>/…` with the files shown above.

---

## 4. Module Slugs (Canonical Mapping)

4.1 **Allowed slugs:** `m01`…`m20` mapped exactly as listed in §3.1.  
4.2 **Naming:** Filenames and command IDs **MUST** use these slugs **exactly**.

---

## 5. Command Naming & Menus

5.1 **Pattern:** Command IDs **MUST** match `^zeroui\.m\d{2}\.[A-Za-z0-9_.-]+$`.  
5.2 **Examples (non-exhaustive):**
```
zeroui.m03.showDecisionCard
zeroui.m03.runCanaryProbe
zeroui.m03.viewReceipt
zeroui.m03.quickFix.addTestStub
zeroui.m09.runSecurityScan
zeroui.m01.mmm.refresh
```
5.3 **Context keys (allowed):** `zeroui.module` (string), `zeroui.degraded` (boolean), `zeroui.hasReceipt` (boolean).  
5.4 **Menus:** `when` clauses **MUST** use only the allowed keys. Example: `"when": "zeroui.module == 'm03' && !zeroui.degraded"`.

---

## 6. Module Contract (TypeScript)

6.1 **Export contract:** Each Module **MUST** export `registerModule(context, deps): ZeroUIModule` from `index.ts`.  
6.2 **Interface shape (normative):**
- `ZeroUICommand` with `id`, `title`, `handler`, optional `category`.  
- Optional providers: `StatusPillProvider`, `DecisionCardSection[]`, `EvidenceDrawerProvider`, `ProblemsPublisher`, `QuickAction[]`.  
- Lifecycle: `activate(context, deps)`, optional `deactivate()`.

6.3 **Providers:**  
- `StatusPillProvider` **MUST** implement `getText()` and `getTooltip()`; `onClickCommandId` optional.  
- `DecisionCardSection` **MUST** implement `render(webview, panel)`.  
- `EvidenceDrawerProvider` **MUST** implement `listItems()`.  
- `ProblemsPublisher` **MUST** implement `computeDiagnostics()`.

---

## 7. Module Manifest (Per‑Folder)

7.1 **Location:** `src/modules/<slug>/module.manifest.json`.  
7.2 **Required fields:** `id`, `title`, `commands[]`, `menus`, `views[]`, `keybindings[]`, `configuration[]`.  
7.3 **ID enum:** `id` **MUST** be one of `m01…m20`.  
7.4 **Command IDs:** Each `commands[i].id` **MUST** follow the pattern in §5.1; each `commands[i].title` **MUST** be non-empty.  
7.5 **Schema validity:** Manifests **MUST** validate against the JSON Schema specified in the architecture file (§5).

---

## 8. Build‑Time Contribution Generation

8.1 **Generator:** `build/generate-contrib.ts` **MUST** merge all module manifests into a **single** `package.json.contributes`.  
8.2 **Coverage:** The generator **MUST** output: `commands`, `menus`, and—if present—`views`, `keybindings`, `configuration`.  
8.3 **Duplicates:** The generator **MUST FAIL** on duplicate command IDs or view IDs.  
8.4 **Naming rule:** The generator **MUST FAIL** if any command ID does not match `^zeroui\.m\d{2}\.`.  
8.5 **Context key allow‑list:** The generator **MUST FAIL** on unknown `when` keys other than: `zeroui.module`, `zeroui.degraded`, `zeroui.hasReceipt`.  
8.6 **Deterministic order:** Generated contributions **MUST** be stably sorted (by Module id, then command id).  
8.7 **Timing:** Generation **MUST** complete **before** packaging; the published `package.json` is static.

---

## 9. Bootstrap & Loader

9.1 **Thin `extension.ts`:** File length **MUST** be ≤ 80 lines and contain only bootstrap/registration logic.  
9.2 **Static imports:** `module-loader.ts` **MUST** use static imports for `m01…m20` and return an array from `loadAllModules(context, deps)`.  
9.3 **Registration:** For each Module, all commands **MUST** be registered; `activate()` **MUST** be invoked during bootstrap.

---

## 10. Shared UI Hosts (Strict Separation)

10.1 **Status Pill host:** Implemented in `core/status-pill/`; composes text/tooltip from module `StatusPillProvider`s.  
10.2 **Decision Card host:** Single Webview host in `core/decision-card/`; Modules contribute **sections** only.  
10.3 **Evidence Drawer host:** Implemented in `core/evidence-drawer/`; Modules contribute list items.  
10.4 **Problems Publisher host:** Implemented in `core/problems-publisher/`; Modules return diagnostics.

10.5 **Isolation rules:**  
- Each Decision Card section **MUST** render under `#zeroui-section-<moduleId>-<sectionId>`.  
- Host↔Section messages **MUST** include `{ moduleId, type, payload }` and be validated; mismatched `moduleId` **MUST** be rejected.  
- Modules **MUST NOT** import each other; Modules **MAY** import from `core/*` only.

---

## 11. Context Keys Manager

11.1 **Initialization:** `zeroui.module` **MUST** be set when a Module’s surfaces are in focus (default `'m01'` or `'none'` if no focus).  
11.2 **Updates:** Keys **MUST** be updated on editor change, panel visibility change, and receipt updates.  
11.3 **Additional keys:** `zeroui.degraded` and `zeroui.hasReceipt` **MUST** reflect Agent responses/receipts.

---

## 12. Performance Budgets (Measured)

12.1 **Activation cold start:** **< 50 ms** (registration only).  
12.2 **Status Pill initial render:** **≤ 50 ms**.  
12.3 **Command handlers:** **MUST** return control immediately; long work **MUST** run asynchronously.  
12.4 **Diagnostics:** **MUST** run in background, coalesced, with cancellation.  
12.5 **IPC:** **MUST** be async with timeouts and error normalization; **MUST NOT** block the UI thread.

---

## 13. Tests (Required)

13.1 **Per‑Module unit tests** (`src/modules/<slug>/__tests__/`):  
- command handlers (success/error cases);  
- providers (status pill, diagnostics) using mocks.

13.2 **Core integration tests:** boot the extension with mock `CoreDeps`; verify:  
- commands registered for all Modules;  
- context keys enforce positive/negative `when` cases;  
- Decision Card host renders a Module section;  
- Evidence Drawer merges items from at least two Modules.

13.3 **Generator tests:** fail on duplicates, invalid command IDs, unknown context keys, or unstable sort order.

---

## 14. CI Gates (Fail‑Fast)

14.1 **Generator drift:** Re‑run generator; **FAIL** if `package.json` changes (uncommitted).  
14.2 **Duplicates/invalid IDs:** **FAIL** on any duplicate ID or command ID violating §5.1.  
14.3 **Schema validation:** **FAIL** if any `module.manifest.json` does not validate against the schema in §7.5.  
14.4 **Activation budget:** **FAIL** if activation exceeds **50 ms** on the CI runner.  
14.5 **Menu checks:** **FAIL** if `when` visibility tests fail for context keys.  
14.6 **Windows build:** **FAIL** if Windows compilation fails or introduces native dependencies.

---

## 15. Acceptance Criteria (Release Gate)

15.1 `extension.ts` ≤ 80 lines; contains no Module logic.  
15.2 All 20 Modules exist and export `registerModule()`.  
15.3 Generated `package.json.contributes` includes commands, menus, and—where provided—views, keybindings, configuration; duplicates rejected.  
15.4 Status Pill, Decision Card, Evidence Drawer, Problems are hosted in `core/*`; Modules provide providers/sections only.  
15.5 Context keys initialized and toggled deterministically; menu `when` logic verified in tests.  
15.6 Performance budgets (§12) are met in CI.  
15.7 All CI gates (§14) pass.

---

## 16. Change Management

16.1 **Add Module:** create `src/modules/<slug>/` with `module.manifest.json` and `index.ts`; add static import in `module-loader.ts`; re‑run generator and commit `package.json` changes; add tests; pass CI.  
16.2 **Remove Module:** inverse of 16.1; generator removes contributions automatically.

---

## 17. Enforcement (What Causes a Block)

- Missing or mislocated files vs §3.1.  
- Any command ID not matching §5.1.  
- Use of context keys beyond §5.3 in `when` clauses.  
- Cross‑module imports (violates §10.5).  
- Webview sections not namespaced per §10.5.  
- `extension.ts` exceeding 80 lines or containing Module logic (violates §9.1).  
- Generator not run or drift detected (violates §8, §14.1).  
- CI failures defined in §14.

---

**End of Constitution** — Derived solely from ARCHITECTURE_VSCode_Modular_Extension.md.
