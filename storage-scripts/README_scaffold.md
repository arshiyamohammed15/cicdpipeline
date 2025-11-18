# ZeroUI 4‑Plane Storage — Windows‑first Scaffold (v2.0)

This repo is Windows‑first. Use **PowerShell** to create the final folder structure under a configurable root (`ZU_ROOT`).

## v2.0 Simplified Structure

The scaffold implements **lazy creation**: only parent folders are created during scaffold (~25 folders instead of 50+). Subfolders (like `telemetry/metrics/dt=.../`, `llm/prompts/`) are created on-demand when actually used.

**Key improvements:**
- **Flattened paths**: Removed `agent/` prefix from IDE plane
- **Unified telemetry**: All planes use `telemetry/` instead of `observability/service-metrics/otel/`
- **Consolidated evidence**: Receipts/manifests/checksums merged to `evidence/data/`
- **Reduced depth**: Max nesting depth reduced from 5 to 3 levels

## Required files
- `tools/create-folder-structure-development.ps1` — creates development environment with IDE, tenant, product, and shared planes
- `tools/create-folder-structure-integration.ps1` — creates integration environment with tenant, product, and shared planes
- `tools/create-folder-structure-staging.ps1` — creates staging environment with tenant, product, and shared planes
- `tools/create-folder-structure-production.ps1` — creates production environment with tenant, product, and shared planes

## Quick start (PowerShell)

### Development Environment
```powershell
# from storage-scripts directory
pwsh -File tools\create-folder-structure-development.ps1 `
  -ZuRoot D:\ZeroUI\development
```

### Integration Environment
```powershell
# from storage-scripts directory
pwsh -File tools\create-folder-structure-integration.ps1 `
  -ZuRoot D:\ZeroUI\integration
```

### Staging Environment
```powershell
# from storage-scripts directory
pwsh -File tools\create-folder-structure-staging.ps1 `
  -ZuRoot D:\ZeroUI\staging
```

### Production Environment
```powershell
# from storage-scripts directory
pwsh -File tools\create-folder-structure-production.ps1 `
  -ZuRoot D:\ZeroUI\production
```

### Testing Created Structure
After creating the folder structure, verify it with:
```powershell
# from storage-scripts directory
pwsh -File tests\test-folder-structure.ps1 `
  -ZuRoot D:\ZeroUI
```

## Parameters

### Common Parameters (all scripts)
- **-ZuRoot** — Base path for ZU_ROOT. If not provided, constructed from Drive and ProductName, or uses `$env:ZU_ROOT` environment variable.
- **-Drive** — Drive letter for ZU_ROOT path. Default: "D". Ignored if -ZuRoot is specified.
- **-ProductName** — Product name for ZU_ROOT path. Default: "ZeroUI". Ignored if -ZuRoot is specified.
- **-CompatAliases** — If specified, creates deprecated alias folders (e.g., `tenant/meta/schema/`).
- **-Consumer** — Consumer ID for creating watermark folders (parent folders are created; leaf folders created on-demand).

### Notes
- All scripts are idempotent — safe to re-run.
- Only parent folders are created during scaffold (~25 folders instead of 50+).
- Subfolders (like `telemetry/metrics/dt=.../`, `llm/prompts/`) are created on-demand when actually used.
- Development environment includes IDE plane; other environments (integration, staging, production) do not.

## Behavior
- **Idempotent** — safe to re‑run.
- **Folders only** — no files are created.
- **Lazy creation** — only parent folders created; subfolders created on-demand.
- **Spec‑aligned** — creates *only* the folders in `folder-business-rules.md` v2.0 (no `extension/*`).
