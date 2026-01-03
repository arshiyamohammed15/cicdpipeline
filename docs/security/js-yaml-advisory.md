# js-yaml advisory (prototype pollution)

- Advisory: GHSA-mh29-5h37-fv8m (js-yaml merge operator prototype pollution)
- Affected path: `src/vscode-extension` via `mocha` -> `js-yaml@4.1.0`
- Current status: `npm audit --audit-level=moderate` reports this issue; no patched js-yaml version is available in the mocha dependency chain at this time.
- Mitigation: No untrusted YAML is loaded by the extension; usage is limited to test tooling. Audit remains open until upstream mocha publishes a fix. Tracking is explicit here to document acceptance.

