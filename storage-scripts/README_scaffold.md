# ZeroUI 4‑Plane Storage — Windows‑first Scaffold

This repo is Windows‑first. Use **PowerShell** to create the final folder structure under a configurable root (`ZU_ROOT`).

## Required file
- `tools/scaffold/zero_ui_scaffold.ps1` — the **only script** you need.

## Quick start (PowerShell)
```powershell
# from repo root
pwsh -File tools\scaffold\zero_ui_scaffold.ps1 `
  -ZuRoot D:\ZeroUI `
  -Tenant acme `
  -Env dev `
  -Repo core `
  -CreateDt 2025-10-18 `
  -Consumer metrics `
  -CompatAliases:$false `
  -DryRun
```

## Flags (strict)
- **-ZuRoot** *(required)* — scaffold root.
- **-Tenant, -Org, -Region, -Env, -Repo** — identifiers (slugged to kebab‑case).
- **-CreateDt** *(YYYY-MM-DD)* — enables **dt=** partitions and **IDE (laptop) YYYY/MM** receipts.
- **-Shards** *(0|16|256)* — **validated only**; directories are **not** created implicitly.
- **-Consumer** — creates `.../evidence/watermarks/<consumer>/` in Tenant and Product.
- **-CompatAliases** — opt‑in to create deprecated `tenant/meta/schema` alias.
- **-DryRun** — print planned `mkdir` ops only.
- **-StampUnclassified <slug>** — create RFC fallback folders (`UNCLASSIFIED__<slug>`) in Tenant/Product/Laptop.

## Behavior
- **Idempotent** — safe to re‑run.
- **Folders only** — no files are created.
- **Spec‑aligned** — creates *only* the folders in `folder-business-rules.md` v1.1 (no `extension/*`).

