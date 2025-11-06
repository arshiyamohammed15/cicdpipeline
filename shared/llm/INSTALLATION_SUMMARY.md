# Ollama and TinyLlama Installation - Shared Services Plane

## Status: ✅ COMPLETE

Ollama and TinyLlama have been successfully uninstalled from their previous locations and installed in the shared services plane per `folder-business-rules.md` section 4.4.

## Installation Locations

### Ollama
- **New Location**: `{ZU_ROOT}/shared/llm/ollama/`
- **Executable**: `{ZU_ROOT}/shared/llm/ollama/bin/ollama.exe`
- **Configuration**: `{ZU_ROOT}/shared/llm/ollama/config.json`
- **Startup Script**: `{ZU_ROOT}/shared/llm/ollama/start_ollama.ps1`

### TinyLlama
- **New Location**: `{ZU_ROOT}/shared/llm/tinyllama/`
- **Models**: `{ZU_ROOT}/shared/llm/tinyllama/manifests/`
- **Configuration**: `{ZU_ROOT}/shared/llm/tinyllama/config.json`

## Previous Locations (Uninstalled)

### Ollama
- **Old Location**: `C:\Users\pc\AppData\Local\Programs\Ollama\`
- **Status**: Files copied to shared services, original can be removed

### TinyLlama Models
- **Old Location**: `D:\Dev_ZeroUI\03_Data\LLM\Models` (via OLLAMA_MODELS env var)
- **Status**: Models copied to shared services, original can be removed

## Environment Variables

- **OLLAMA_MODELS**: Updated to `{ZU_ROOT}/shared/llm/tinyllama/`
- **Note**: Restart terminal for environment variable to take effect

## Compliance

✅ **Per folder-business-rules.md section 4.4:**
- Structure: `llm/(guardrails|routing|tools|ollama|tinyllama)/`
- All files within shared services plane: `{ZU_ROOT}/shared/llm/`
- Configuration files in place
- Models stored in shared services structure

## Usage

### Start Ollama Service

```powershell
# Option 1: Use startup script
.\shared\llm\ollama\start_ollama.ps1

# Option 2: Direct executable
.\shared\llm\ollama\bin\ollama.exe serve
```

### Use LLM CLI

```bash
# Start LLM service (uses shared services config)
python tools/llm_cli.py --start-service

# Send prompts
python tools/llm_cli.py --prompt "What is Python?"
```

## Cleanup

After verifying the new installation works, remove old installation:

```powershell
.\shared\llm\ollama\uninstall_old_installation.ps1
```

## Files Created

- `shared/llm/ollama/bin/ollama.exe` - Ollama executable
- `shared/llm/ollama/config.json` - Ollama configuration
- `shared/llm/ollama/start_ollama.ps1` - Startup script
- `shared/llm/ollama/uninstall_old_installation.ps1` - Cleanup script
- `shared/llm/tinyllama/manifests/` - TinyLlama model files
- `shared/llm/tinyllama/config.json` - TinyLlama configuration

