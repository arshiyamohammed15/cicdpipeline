# One-Command Bootstrap Guide

This guide explains how to use the ZeroUI bootstrap script to set up a fresh development environment on Windows with a single command.

## What the Script Does

The `zeroui_bootstrap_local.ps1` script automates the complete setup process:

1. **Prerequisite Checks**: Verifies Git, Python 3.11+, Node.js LTS, and optionally Docker/Ollama
2. **Auto-Installation**: Optionally installs missing prerequisites via winget (if `-AutoInstallPrereqs` is set)
3. **Folder Structure**: Creates the complete ZU_ROOT folder structure using the existing `create-folder-structure-development.ps1` tool
4. **Python Environment**: Creates a virtual environment and installs all Python dependencies from `requirements.txt`
5. **Node.js Dependencies**: Installs dependencies for root package, VS Code extension, and edge agent
6. **Docker Postgres**: Optionally starts 3 Postgres containers for tenant/zeroui/shared planes (ports 5433/5434/5435)
7. **Ollama Models**: Optionally pulls LLM models (small or large)
8. **Unit Tests**: Runs Python and TypeScript tests to verify everything works (default ON in setup mode)

The script is **idempotent** - safe to run multiple times. It will skip steps that are already complete.

## Quick Start Commands

### Basic Setup (Manual Prerequisites)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/zeroui_bootstrap_local.ps1 -Mode setup -RunTests
```

This will:
- Check prerequisites (but won't install them)
- Create folder structure
- Install Python and Node dependencies
- Run unit tests
- Fail if anything goes wrong

### Full Setup with Auto-Install

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/zeroui_bootstrap_local.ps1 -Mode setup -AutoInstallPrereqs -SetupDockerPlanePostgres -SetupOllama -PullSmallModels -RunTests
```

This will:
- Auto-install missing prerequisites via winget
- Start Docker Postgres containers
- Install Ollama and pull small models
- Run all tests

### Verify-Only Mode

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup/zeroui_bootstrap_local.ps1 -Mode verify
```

This will:
- Check prerequisites exist
- Verify folder structure exists
- **Not** install dependencies or run tests

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-Mode` | Operation mode: `setup` or `verify` | `setup` |
| `-AutoInstallPrereqs` | Auto-install missing prerequisites via winget | `false` |
| `-SetupDockerPlanePostgres` | Start 3 Postgres containers (ports 5433/5434/5435) | `false` |
| `-SetupOllama` | Ensure Ollama is installed | `false` |
| `-PullSmallModels` | Pull tinyllama, qwen2.5-coder:14b, llama3:instruct | `false` |
| `-PullBigModels` | Pull qwen2.5-coder:32b | `false` |
| `-RunTests` | Run unit tests (default ON in setup, OFF in verify) | Auto |
| `-ZuRoot` | Override ZU_ROOT path | Uses `.env` or `{repo}\.zu` |

## ZU_ROOT Location

The script determines ZU_ROOT in this order:

1. `-ZuRoot` parameter (if provided)
2. `ZU_ROOT` from `.env` file (if exists)
3. Default: `{repo-root}\.zu`

The script will create/update the `.env` file with the resolved ZU_ROOT value.

## Folder Structure

The script uses `storage-scripts/tools/create-folder-structure-development.ps1` to create the folder structure under `ZU_ROOT\development\`:

- `development\ide` - IDE plane
- `development\tenant` - Tenant plane
- `development\product` - Product plane
- `development\shared` - Shared plane

## Docker Postgres Connection Strings

When `-SetupDockerPlanePostgres` is used, the script starts 3 Postgres containers:

- **Tenant**: `postgresql://zeroui:zeroui_dev_only@localhost:5433/zeroui`
- **Zeroui**: `postgresql://zeroui:zeroui_dev_only@localhost:5434/zeroui`
- **Shared**: `postgresql://zeroui:zeroui_dev_only@localhost:5435/zeroui`

**Note**: These credentials are for **local development only**. Never use in production.

## Troubleshooting

### Python Launcher "py -3.11" Not Found

If you get an error about `py -3.11` not found:

1. Install Python 3.11+ from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Or use `-AutoInstallPrereqs` to auto-install via winget

### Docker Desktop Not Running

If Docker commands fail:

1. Start Docker Desktop
2. Wait for it to fully start (whale icon in system tray)
3. Run the script again

### winget Blocked or Not Available

If `-AutoInstallPrereqs` fails because winget is not available:

1. Install prerequisites manually:
   - Git: https://git-scm.com/download/win
   - Python 3.11+: https://www.python.org/downloads/
   - Node.js LTS: https://nodejs.org/
   - Docker Desktop: https://www.docker.com/products/docker-desktop/
   - Ollama: https://ollama.ai/
2. Run the script again without `-AutoInstallPrereqs`

### Execution Policy Error

If you get an execution policy error:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Tests Fail

If unit tests fail:

1. Check the error output for specific test failures
2. Ensure all prerequisites are correctly installed
3. Try running tests manually:
   ```powershell
   .\venv\Scripts\Activate.ps1
   pytest -q
   ```

### Folder Structure Creation Fails

If folder structure creation fails:

1. Check that `storage-scripts/tools/create-folder-structure-development.ps1` exists
2. Verify you have write permissions to the ZU_ROOT location
3. Check the error output for specific path issues

## Next Steps

After successful bootstrap:

1. **Activate Python venv**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. **Review documentation**:
   - `docs/architecture/dev/quickstart_windows.md` - Full quickstart guide
   - `docs/architecture/` - Architecture documentation

3. **Start developing**:
   - Run tests: `pytest -q`
   - Build TypeScript: `npm run build:typescript`
   - Check out module implementation guides

## Script Behavior

- **Idempotent**: Safe to run multiple times
- **Strict Error Handling**: Fails fast on any error (no silent failures)
- **Clear Output**: Color-coded success/warning/error messages
- **Test Enforcement**: In setup mode, tests must pass or script exits with error

## See Also

- `docs/architecture/dev/quickstart_windows.md` - Full Windows quickstart guide
- `storage-scripts/folder-business-rules.md` - Folder structure rules
- `AGENTS.md` - Agent guidance and rules

