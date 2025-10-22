# Windows Quick Start — ZeroUI Scaffold

To create the 4‑plane structure with all governance rules applied, run this single command from the repo root:

```powershell
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

**Tip:** Remove `-DryRun` to actually create the folders.
