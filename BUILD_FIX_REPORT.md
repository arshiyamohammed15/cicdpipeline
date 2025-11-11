# Build Fix Report

| Error | Location | Callee | Expected Signature | Actual Call | Candidate Fix |
| --- | --- | --- | --- | --- | --- |
| TS2554 | `src/vscode-extension/ui/client-admin-dashboard/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/compliance-security-challenges/ExtensionInterface.ts:87` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/cross-cutting-concerns/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/detection-engine-core/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/feature-development-blind-spots/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/gold-standards/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/integration-adapters/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/knowledge-integrity-discovery/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/knowledge-silo-prevention/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/legacy-systems-safety/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/merge-conflicts-delays/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/mmm-engine/ExtensionInterface.ts:74` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/monitoring-observability-gaps/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/product-success-monitoring/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/release-failures-rollbacks/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/reporting/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/roi-dashboard/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/signal-ingestion-normalization/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2554 | `src/vscode-extension/ui/technical-debt-accumulation/ExtensionInterface.ts:64` | `EventEmitter.fire` | `fire(data: T): void` | `this._onDidChangeTreeData.fire();` | supply argument from scope |
| TS2345 | `src/vscode-extension/ui/toast/ToastManager.ts:12` | `Array<Disposable>.push` | `push(...items: Disposable[]): number` | `this.activeToasts.push(toast);` | thread from caller |
| TS2345 | `src/vscode-extension/ui/toast/ToastManager.ts:20` | `Array<Disposable>.push` | `push(...items: Disposable[]): number` | `this.activeToasts.push(toast);` | thread from caller |
| TS2345 | `src/vscode-extension/ui/toast/ToastManager.ts:44` | `Array<Disposable>.push` | `push(...items: Disposable[]): number` | `this.activeToasts.push(toast);` | thread from caller |

## `npm run compile` (latest)

```
ui/toast/ToastManager.ts(12,32): error TS2345: Argument of type 'Thenable<string | undefined>' is not assignable to parameter of type 'Disposable'.
  Property 'dispose' is missing in type 'Thenable<string | undefined>' but required in type 'Disposable'.
ui/toast/ToastManager.ts(20,32): error TS2345: Argument of type 'Thenable<string | undefined>' is not assignable to parameter of type 'Disposable'.
ui/toast/ToastManager.ts(44,32): error TS2345: Argument of type 'Thenable<string | undefined>' is not assignable to parameter of type 'Disposable'.
```

### `npm run compile` (rerun)

```
ui/toast/ToastManager.ts(12,32): error TS2345: Argument of type 'Thenable<string | undefined>' is not assignable to parameter of type 'Disposable'.
  Property 'dispose' is missing in type 'Thenable<string | undefined>' but required in type 'Disposable'.
ui/toast/ToastManager.ts(20,32): error TS2345: Argument of type 'Thenable<string | undefined>' is not assignable to parameter of type 'Disposable'.
ui/toast/ToastManager.ts(44,32): error TS2345: Argument of type 'Thenable<string | undefined>' is not assignable to parameter of type 'Disposable'.
```

### `npm run compile` (post toast fix)

```
(no errors)
```

## Final Status

- **STATUS: PASS**
- Diff summary: updated 19 extension interface files to call `_onDidChangeTreeData.fire(undefined)`, adjusted `ToastManager` to stop storing `Thenable` instances, and maintained `BUILD_FIX_REPORT.md` changelog.

